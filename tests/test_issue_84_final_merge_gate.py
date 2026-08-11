import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_rollback_readiness import build_rollback_registry
from du_profile_loader import load_du_profile
from jendela_migration_decision import parse_jendela_before_mw_antenna_size


class TestIssue84FinalMergeGate(unittest.TestCase):
    def setUp(self):
        self.profile = load_du_profile(
            ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"
        )
        self.source = json.loads(
            (
                ROOT
                / "config"
                / "registries"
                / "mw_du_profile_rollback_baselines_source.yaml"
            ).read_text(encoding="utf-8")
        )

    def test_radio_configuration_requires_token_boundaries(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2 foo1+0bar")
        )
        self.assertEqual(
            parse_jendela_before_mw_antenna_size("18G 1.2 1+0"), 1.2
        )

    def test_non_mapping_rollback_source_root_fails_closed(self):
        for malformed in ([], [{}], "bad", 123):
            with self.subTest(malformed=malformed):
                registry = build_rollback_registry(
                    [self.profile], {"entries": []}, malformed
                )
                entry = registry["entries"][0]
                self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
                self.assertIn("ROLLBACK_BASELINE_SOURCE_ROOT_INVALID", entry["blockers"])
                self.assertTrue(registry["rollback_source_root_invalid"])

    def test_malformed_required_profile_id_fails_closed(self):
        for invalid_value in (None, 123, {}, [], ""):
            malformed = json.loads(json.dumps(self.source))
            malformed["required_profile_ids"] = [invalid_value]
            with self.subTest(invalid_value=invalid_value):
                registry = build_rollback_registry(
                    [self.profile], {"entries": []}, malformed
                )
                entry = registry["entries"][0]
                self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
                self.assertIn(
                    "ROLLBACK_BASELINE_REQUIRED_PROFILE_ID_INVALID",
                    entry["blockers"],
                )
                self.assertEqual(
                    registry["invalid_required_profile_id_indexes"], [0]
                )


if __name__ == "__main__":
    unittest.main()
