import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_rollback_readiness import evaluate_rollback_readiness, rollback_markdown
from du_profile_loader import load_du_profile


class TestProfileRollbackReadiness(unittest.TestCase):
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

    def test_jendela_records_rollback_baseline_after_pr_input_ready(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")

        entry = evaluate_rollback_readiness(profile, None)

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
        self.assertEqual(entry["rollback_target_profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(entry["rollback_target_profile_version"], "0.3.0")
        self.assertEqual(
            entry["rollback_target_header_hashes"],
            ["904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3"],
        )

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
