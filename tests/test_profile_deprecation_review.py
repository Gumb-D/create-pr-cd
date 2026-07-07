import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_deprecation_review import evaluate_deprecation, deprecation_markdown


class TestProfileDeprecationReview(unittest.TestCase):
    def test_deprecated_profile_requires_successor_and_rollback_evidence(self):
        profile = {
            "profile_id": "legacy_tx_mini_pr_v0",
            "profile_version": "0.0.9",
            "mapping_version": "legacy-v0",
            "status": "DEPRECATED",
            "export_structure": {
                "observed_header_hash": "abc123",
                "approved_header_hashes": ["abc123"],
            },
            "deprecation": {
                "reason": "Superseded by approved successor profile.",
                "successor_profile_id": "tx_mini_pr_v1",
                "successor_profile_version": "0.1.0",
                "rollback_profile_id": "legacy_tx_mini_pr_v0",
                "rollback_profile_version": "0.0.9",
                "superseded_header_hashes": ["abc123"],
            },
        }
        production_transition = {"target_status": "PRODUCTION", "eligible": True, "denied_reasons": []}

        result = evaluate_deprecation(profile, production_transition)

        self.assertEqual(result["deprecation_status"], "DEPRECATION_RECORDED")
        self.assertEqual(result["successor_profile_id"], "tx_mini_pr_v1")
        self.assertEqual(result["superseded_header_hashes"], ["abc123"])

    def test_draft_profile_without_deprecation_plan_stays_not_requested(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_deprecation_review.yaml").read_text(encoding="utf-8")
        )
        tx_entry = next(entry for entry in registry["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        self.assertEqual(tx_entry["deprecation_status"], "NO_DEPRECATION_PLAN")
        self.assertIn("DEPRECATED lifecycle state", " ".join(tx_entry["notes"]))

    def test_markdown_mentions_no_deprecation_plan(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_deprecation_review.yaml").read_text(encoding="utf-8")
        )
        markdown = deprecation_markdown(registry)
        self.assertIn("# MW DU Profile Deprecation Review", markdown)
        self.assertIn("NO_DEPRECATION_PLAN", markdown)
        self.assertIn("tx_mini_pr_v1", markdown)


if __name__ == "__main__":
    unittest.main()
