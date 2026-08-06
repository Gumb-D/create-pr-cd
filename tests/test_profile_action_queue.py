import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_action_queue import action_queue_markdown, build_action_queue_entry
from du_profile_loader import load_du_profile


PRODUCTION_PROFILE_IDS = {
    "tx_mini_pr_v1",
    "tx_rollout_2023_pr_v1",
    "mw_eos_swap_pr_v1",
    "celcomdigi_bau_2023_pr_v1",
    "celcomdigi_bau_2024_pr_v1",
    "celcomdigi_usp_pr_v1",
    "jendela_tx_migration_pr_v1",
    "zte_tx_mini_pr_v1",
}


class TestProfileActionQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(
                encoding="utf-8"
            )
        )

    def _entry(self, profile_id):
        return next(
            entry for entry in self.registry["entries"] if entry["profile_id"] == profile_id
        )

    def test_tx_mini_queue_has_no_required_or_optional_field_work(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        readiness = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_readiness_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        readiness_entry = next(
            entry for entry in readiness["entries"] if entry["profile_id"] == "tx_mini_pr_v1"
        )
        unresolved_entry = next(
            entry for entry in unresolved["entries"] if entry["profile_id"] == "tx_mini_pr_v1"
        )
        bridge_entry = next(
            entry for entry in bridge["entries"] if entry["profile_id"] == "tx_mini_pr_v1"
        )

        entry = build_action_queue_entry(
            profile,
            readiness_entry,
            unresolved_entry,
            bridge_entry,
        )

        self.assertEqual(entry["readiness_status"], "PRODUCTION_READY")
        self.assertEqual(entry["action_queue"], [])

    def test_production_profiles_never_receive_lifecycle_hold(self):
        for profile_id in PRODUCTION_PROFILE_IDS:
            with self.subTest(profile_id=profile_id):
                entry = self._entry(profile_id)
                action_types = [item["action_type"] for item in entry["action_queue"]]
                self.assertEqual(entry["profile_status"], "PRODUCTION")
                self.assertEqual(entry["readiness_status"], "PRODUCTION_READY")
                self.assertNotIn("HOLD_LIFECYCLE_PROMOTION", action_types)
                self.assertFalse(
                    any("uat" in item["summary"].lower() for item in entry["action_queue"])
                )

    def test_optional_review_actions_remain_visible_for_production_profiles(self):
        for profile_id in (
            "mw_eos_swap_pr_v1",
            "jendela_tx_migration_pr_v1",
            "zte_tx_mini_pr_v1",
            "celcomdigi_bau_2023_pr_v1",
        ):
            with self.subTest(profile_id=profile_id):
                entry = self._entry(profile_id)
                action_types = [item["action_type"] for item in entry["action_queue"]]
                self.assertTrue(
                    {"CONFIRM_COMPETING_CANDIDATE", "VERIFY_SINGLE_CANDIDATE"}
                    & set(action_types)
                )
                self.assertNotIn("APPROVE_HEADER_HASH", action_types)
                self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)

    def test_cd_consolidation_retains_required_hold_without_uat_requirement(self):
        entry = self._entry("celcomdigi_cd_consolidation_2023_pr_v1")
        action_types = [item["action_type"] for item in entry["action_queue"]]
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
        self.assertIn("APPROVE_HEADER_HASH", action_types)
        self.assertEqual(action_types[-1], "HOLD_LIFECYCLE_PROMOTION")
        self.assertFalse(any("uat" in item["summary"].lower() for item in entry["action_queue"]))

    def test_markdown_distinguishes_optional_actions_and_draft_hold(self):
        markdown = action_queue_markdown(self.registry)
        self.assertIn("Prioritized governance action queue", markdown)
        self.assertIn("CONFIRM_COMPETING_CANDIDATE", markdown)
        self.assertIn("HOLD_LIFECYCLE_PROMOTION", markdown)
        self.assertIn("celcomdigi_cd_consolidation_2023_pr_v1", markdown)
        self.assertNotIn("current DRAFT profiles", markdown)
        self.assertNotIn("UAT evidence", markdown)


if __name__ == "__main__":
    unittest.main()
