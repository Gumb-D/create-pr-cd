import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_transition_review import evaluate_transition, transition_markdown


class TestProfileTransitionReview(unittest.TestCase):
    def test_business_validated_ignores_current_not_production_status(self):
        readiness_entry = {
            "blocker_summary": {
                "lifecycle_blockers": ["PROFILE_NOT_PRODUCTION", "NO_APPROVED_HEADER_HASH"],
                "missing_required_fields": ["existing_ti_pr_status"],
                "unapproved_required_fields": ["site_code"],
                "competing_candidate_fields": ["tx_sow_raw"],
                "single_candidate_unverified_fields": [],
                "no_profile_selection_fields": [],
                "shortlist_mismatch_fields": [],
                "cross_model_bridge_fields": [],
            }
        }
        result = evaluate_transition(readiness_entry, "BUSINESS_VALIDATED")
        self.assertFalse(result["eligible"])
        self.assertNotIn("PROFILE_NOT_PRODUCTION", result["denied_reasons"])
        self.assertIn("NO_APPROVED_HEADER_HASH", result["denied_reasons"])

    def test_tx_mini_production_transition_stays_denied(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        tx_entry = next(entry for entry in registry["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        production = next(item for item in tx_entry["transition_targets"] if item["target_status"] == "PRODUCTION")
        # Mappings and the header hash are approved, but production stays
        # denied by the non-production lifecycle state and the remaining
        # keyword-level competing shortlist candidates.
        self.assertFalse(production["eligible"])
        self.assertIn("PROFILE_NOT_PRODUCTION", production["denied_reasons"])
        self.assertIn("COMPETING_SHORTLIST_CANDIDATES", production["denied_reasons"])

    def test_markdown_mentions_denied_transition(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        markdown = transition_markdown(registry)
        self.assertIn("BUSINESS_VALIDATED", markdown)
        self.assertIn("DENIED", markdown)
        self.assertIn("NO_APPROVED_HEADER_HASH", markdown)


if __name__ == "__main__":
    unittest.main()
