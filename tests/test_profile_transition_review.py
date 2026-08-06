import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_transition_review import evaluate_transition, transition_markdown


PRODUCTION_PROFILE_IDS = (
    "tx_mini_pr_v1",
    "tx_rollout_2023_pr_v1",
    "mw_eos_swap_pr_v1",
    "celcomdigi_bau_2023_pr_v1",
    "celcomdigi_bau_2024_pr_v1",
    "celcomdigi_usp_pr_v1",
    "jendela_tx_migration_pr_v1",
    "zte_tx_mini_pr_v1",
)


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

    def test_all_approved_profile_production_transitions_are_eligible(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        by_profile = {entry["profile_id"]: entry for entry in registry["entries"]}

        for profile_id in PRODUCTION_PROFILE_IDS:
            with self.subTest(profile_id=profile_id):
                entry = by_profile[profile_id]
                production = next(
                    item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
                )
                business_validated = next(
                    item for item in entry["transition_targets"]
                    if item["target_status"] == "BUSINESS_VALIDATED"
                )
                self.assertEqual(entry["current_status"], "PRODUCTION")
                self.assertTrue(business_validated["eligible"])
                self.assertTrue(production["eligible"])
                self.assertEqual(production["denied_reasons"], [])

    def test_pr_input_ready_ignores_optional_competing_and_unverified_fields(self):
        readiness_entry = {
            "blocker_summary": {
                "lifecycle_blockers": ["PROFILE_NOT_PRODUCTION"],
                "missing_required_fields": [],
                "unapproved_required_fields": [],
                "competing_candidate_fields": ["subcontractor_planning"],
                "required_competing_candidate_fields": [],
                "single_candidate_unverified_fields": ["site_name"],
                "required_single_candidate_unverified_fields": [],
                "no_profile_selection_fields": [],
                "required_no_profile_selection_fields": [],
                "shortlist_mismatch_fields": [],
                "required_shortlist_mismatch_fields": [],
                "cross_model_bridge_fields": [],
            }
        }
        result = evaluate_transition(readiness_entry, "PR_INPUT_READY")
        self.assertTrue(result["eligible"])

    def test_production_ignores_optional_competing_and_unverified_fields(self):
        readiness_entry = {
            "blocker_summary": {
                "lifecycle_blockers": [],
                "missing_required_fields": [],
                "unapproved_required_fields": [],
                "competing_candidate_fields": ["subcontractor_planning"],
                "required_competing_candidate_fields": [],
                "single_candidate_unverified_fields": ["site_name"],
                "required_single_candidate_unverified_fields": [],
                "no_profile_selection_fields": [],
                "required_no_profile_selection_fields": [],
                "shortlist_mismatch_fields": [],
                "required_shortlist_mismatch_fields": [],
                "cross_model_bridge_fields": [],
            }
        }
        result = evaluate_transition(readiness_entry, "PRODUCTION")
        self.assertTrue(result["eligible"])
        self.assertEqual(result["denied_reasons"], [])

    def test_cd_consolidation_production_transition_remains_denied(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        entry = next(
            item for item in registry["entries"]
            if item["profile_id"] == "celcomdigi_cd_consolidation_2023_pr_v1"
        )
        production = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
        )
        self.assertEqual(entry["current_status"], "DRAFT")
        self.assertFalse(production["eligible"])
        self.assertTrue(production["denied_reasons"])

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
