import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_rollback_readiness import build_rollback_registry
from du_profile_loader import load_du_profile
from jendela_migration_decision import parse_jendela_before_mw_antenna_size


class TestIssue84CodexFinalFollowup(unittest.TestCase):
    def test_parser_includes_larger_supported_standalone_candidate_outside_link(self):
        for raw in (
            "2.4 / 18G 1.2 1+0",
            "18G 1.2 1+0 / 2.4",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(parse_jendela_before_mw_antenna_size(raw), 2.4)

    def test_duplicate_unknown_rollback_profile_id_blocks_registry_globally(self):
        profile = load_du_profile(
            ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"
        )
        source = json.loads(
            (
                ROOT
                / "config"
                / "registries"
                / "mw_du_profile_rollback_baselines_source.yaml"
            ).read_text(encoding="utf-8")
        )
        stale_entry = {
            "profile_id": "stale_profile_typo",
            "current_profile_version": "9.9.9",
            "rollback_profile_id": "stale_profile_typo",
            "rollback_profile_version": "9.9.8",
            "rollback_header_hashes": ["stale-hash"],
        }
        source["entries"].extend([dict(stale_entry), dict(stale_entry)])

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("DUPLICATE_ROLLBACK_BASELINE_ENTRIES", entry["blockers"])
        self.assertIn("stale_profile_typo", registry["duplicate_rollback_profile_ids"])

    def test_null_rollback_header_hashes_fail_closed_without_crashing(self):
        profile = load_du_profile(
            ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"
        )
        source = json.loads(
            (
                ROOT
                / "config"
                / "registries"
                / "mw_du_profile_rollback_baselines_source.yaml"
            ).read_text(encoding="utf-8")
        )
        for entry in source["entries"]:
            if entry.get("profile_id") == "jendela_tx_migration_pr_v1":
                entry["rollback_header_hashes"] = None
                break

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_HEADER_HASHES_INVALID", entry["blockers"])
        self.assertEqual(entry["rollback_target_header_hashes"], [])


if __name__ == "__main__":
    unittest.main()
