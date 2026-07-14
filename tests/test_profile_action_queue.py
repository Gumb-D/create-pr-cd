import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_action_queue import build_action_queue_entry, action_queue_markdown
from du_profile_loader import load_du_profile


class TestProfileActionQueue(unittest.TestCase):
    def test_tx_mini_queue_has_no_missing_required_fields_after_approvals(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        readiness = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_readiness_review.yaml").read_text(encoding="utf-8")
        )
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        readiness_entry = next(entry for entry in readiness["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "tx_mini_pr_v1")

        entry = build_action_queue_entry(profile, readiness_entry, unresolved_entry, bridge_entry)

        # Every TX Mini mapping ruling landed by 2026-07-08, so no field work
        # remains in the queue; only the explicit lifecycle-promotion hold.
        action_types = [item["action_type"] for item in entry["action_queue"]]
        self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
        self.assertNotIn("CONFIRM_COMPETING_CANDIDATE", action_types)
        self.assertEqual(entry["action_queue"][-1]["action_type"], "HOLD_LIFECYCLE_PROMOTION")

    def test_mw_eos_queue_contains_competing_but_no_header_or_missing_required_actions(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "mw_eos_swap_pr_v1")
        action_types = [item["action_type"] for item in entry["action_queue"]]
        self.assertIn("CONFIRM_COMPETING_CANDIDATE", action_types)
        self.assertNotIn("APPROVE_HEADER_HASH", action_types)
        self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
        self.assertEqual(entry["action_queue"][-1]["action_type"], "HOLD_LIFECYCLE_PROMOTION")

    def test_jendela_queue_has_no_header_or_missing_required_actions_after_approval(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "jendela_tx_migration_pr_v1")
        action_types = [item["action_type"] for item in entry["action_queue"]]
        self.assertNotIn("APPROVE_HEADER_HASH", action_types)
        self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
        self.assertEqual(entry["action_queue"][-1]["action_type"], "HOLD_LIFECYCLE_PROMOTION")

    def test_2023_celcomdigi_bau_queue_has_no_missing_required_header_or_lifecycle_hold_actions(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "celcomdigi_bau_2023_pr_v1")
        action_types = [item["action_type"] for item in entry["action_queue"]]
        self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
        self.assertNotIn("APPROVE_HEADER_HASH", action_types)
        self.assertNotIn("HOLD_LIFECYCLE_PROMOTION", action_types)

    def test_markdown_mentions_priority_ids_and_hints(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )
        markdown = action_queue_markdown(registry)
        self.assertIn("tx_mini_pr_v1:01", markdown)
        self.assertIn("HOLD_LIFECYCLE_PROMOTION", markdown)
        self.assertIn("Current observed header hash", markdown)


if __name__ == "__main__":
    unittest.main()
