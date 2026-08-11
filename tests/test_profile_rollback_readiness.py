import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_rollback_readiness import (
    build_rollback_registry,
    evaluate_rollback_readiness,
    rollback_markdown,
    write_rollback_outputs,
)
from du_profile_loader import discover_du_profile_paths, load_du_profile


class TestProfileRollbackReadiness(unittest.TestCase):
    def _rollback_baseline_registry(self):
        return json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_rollback_baselines_source.yaml").read_text(
                encoding="utf-8"
            )
        )

    def _rollback_baseline_for(self, profile_id):
        registry = self._rollback_baseline_registry()
        return next(entry for entry in registry["entries"] if entry["profile_id"] == profile_id)

    def test_2023_celcomdigi_bau_records_rollback_baseline_after_pr_input_ready(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2023_pr_v1.yaml")

        entry = evaluate_rollback_readiness(profile, None)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "celcomdigi_bau_2023_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.2.0")
        self.assertEqual(
            entry["rollback_target_header_hashes"],
            ["b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454"],
        )
        self.assertEqual(entry["blockers"], [])

    def test_jendela_records_prior_version_rollback_baseline(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        baseline = self._rollback_baseline_for("jendela_tx_migration_pr_v1")

        entry = evaluate_rollback_readiness(profile, None, baseline)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.4.0")
        self.assertNotEqual(entry["rollback_target_profile_version"], profile["profile_version"])
        self.assertEqual(
            entry["rollback_target_header_hashes"],
            ["f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056"],
        )
        self.assertEqual(entry["blockers"], [])
        self.assertIn("explicit prior approved profile identity", entry["notes"][0])

    def test_jendela_required_baseline_blocks_when_entry_is_missing(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        source = self._rollback_baseline_registry()
        source["required_profile_ids"] = ["jendela_tx_migration_pr_v1"]
        source["entries"] = []

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIsNone(entry["rollback_target_profile_version"])
        self.assertIn("EXPLICIT_PRIOR_ROLLBACK_BASELINE_REQUIRED", entry["blockers"])

    def test_jendela_required_baseline_blocks_when_entry_profile_id_is_mistyped(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        source = self._rollback_baseline_registry()
        source["required_profile_ids"] = ["jendela_tx_migration_pr_v1"]
        source["entries"][0] = dict(source["entries"][0])
        source["entries"][0]["profile_id"] = "jendela_tx_migration_pr_v1_typo"

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIsNone(entry["rollback_target_profile_version"])
        self.assertIn("EXPLICIT_PRIOR_ROLLBACK_BASELINE_REQUIRED", entry["blockers"])

    def test_regeneration_preserves_jendela_prior_version_rollback_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "rollback.json"
            markdown_path = Path(tmpdir) / "rollback.md"
            write_rollback_outputs(
                [ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"],
                ROOT / "config" / "registries" / "mw_du_profile_deprecation_review.yaml",
                registry_path,
                markdown_path,
                ROOT / "config" / "registries" / "mw_du_profile_rollback_baselines_source.yaml",
            )

            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            entry = registry["entries"][0]
            markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(entry["profile_version"], "0.5.0")
        self.assertEqual(entry["rollback_target_profile_version"], "0.4.0")
        self.assertIn("Rollback target: `jendela_tx_migration_pr_v1` `0.4.0`", markdown)
        self.assertNotIn("Rollback target: `jendela_tx_migration_pr_v1` `0.5.0`", markdown)

    def test_tracked_rollback_outputs_match_clean_regeneration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "rollback.json"
            markdown_path = Path(tmpdir) / "rollback.md"
            write_rollback_outputs(
                discover_du_profile_paths(),
                ROOT / "config" / "registries" / "mw_du_profile_deprecation_review.yaml",
                registry_path,
                markdown_path,
                ROOT / "config" / "registries" / "mw_du_profile_rollback_baselines_source.yaml",
            )

            regenerated_registry = registry_path.read_text(encoding="utf-8")
            regenerated_markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(
            regenerated_registry,
            (ROOT / "config" / "registries" / "mw_du_profile_rollback_readiness.yaml").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            regenerated_markdown,
            (ROOT / "docs" / "MW_DU_Profile_Rollback_Readiness.md").read_text(encoding="utf-8"),
        )

    def test_regeneration_fails_closed_if_rollback_baseline_source_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "rollback.json"
            markdown_path = Path(tmpdir) / "rollback.md"
            missing_source = Path(tmpdir) / "missing-rollback-source.json"

            with self.assertRaises(FileNotFoundError):
                write_rollback_outputs(
                    [ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"],
                    ROOT / "config" / "registries" / "mw_du_profile_deprecation_review.yaml",
                    registry_path,
                    markdown_path,
                    missing_source,
                )

    def test_explicit_rollback_baseline_fails_closed_if_it_targets_current_version(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        invalid_baseline = dict(self._rollback_baseline_for("jendela_tx_migration_pr_v1"))
        invalid_baseline["rollback_profile_version"] = profile["profile_version"]

        entry = evaluate_rollback_readiness(profile, None, invalid_baseline)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_TARGET_IS_CURRENT_PROFILE_VERSION", entry["blockers"])

    def test_explicit_rollback_baseline_fails_closed_if_current_version_does_not_match(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        stale_baseline = dict(self._rollback_baseline_for("jendela_tx_migration_pr_v1"))
        stale_baseline["current_profile_version"] = "0.4.0"

        entry = evaluate_rollback_readiness(profile, None, stale_baseline)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_BASELINE_CURRENT_VERSION_MISMATCH", entry["blockers"])

    def test_zte_records_rollback_baseline_after_pr_input_ready(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml")

        entry = evaluate_rollback_readiness(profile, None)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "zte_tx_mini_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.2.0")
        self.assertEqual(
            entry["rollback_target_header_hashes"],
            ["a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810"],
        )

    def test_tx_mini_records_rollback_baseline_after_pr_input_ready(self):
        # PR_INPUT_READY (2026-07-08) plus the approved header hash gives
        # TX Mini a recorded rollback baseline.
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")

        entry = evaluate_rollback_readiness(profile, None)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "tx_mini_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.2.0")

    def test_profile_with_approved_header_hash_records_rollback_baseline(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        profile["status"] = "PRODUCTION"
        profile["export_structure"]["approved_header_hashes"] = [
            profile["export_structure"]["observed_header_hash"]
        ]
        for field in profile["field_mapping"].values():
            for candidate in field.get("source_candidates", []):
                candidate["mapping_status"] = "APPROVED"

        entry = evaluate_rollback_readiness(profile, None)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "tx_mini_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.2.0")
        self.assertEqual(
            entry["rollback_target_header_hashes"],
            [profile["export_structure"]["observed_header_hash"]],
        )

    def test_markdown_mentions_blocked_status(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_rollback_readiness.yaml").read_text(encoding="utf-8")
        )
        markdown = rollback_markdown(registry)

        self.assertIn("# MW DU Profile Rollback Readiness", markdown)
        self.assertIn("ROLLBACK_BLOCKED", markdown)
        self.assertIn("tx_mini_pr_v1", markdown)


if __name__ == "__main__":
    unittest.main()
