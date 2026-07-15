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
        # All mappings are approved (2026-07-08), so intermediate targets are
        # eligible, but production stays denied by the explicit non-production
        # lifecycle state until a controlled promotion happens.
        business_validated = next(
            item for item in tx_entry["transition_targets"] if item["target_status"] == "BUSINESS_VALIDATED"
        )
        self.assertTrue(business_validated["eligible"])
        self.assertFalse(production["eligible"])
        self.assertEqual(production["denied_reasons"], ["PROFILE_NOT_PRODUCTION"])

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

    def test_jendela_pr_input_ready_transition_is_eligible_but_production_is_denied(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "jendela_tx_migration_pr_v1")
        pr_input_ready = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PR_INPUT_READY"
        )
        production = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
        )
        self.assertTrue(pr_input_ready["eligible"])
        self.assertFalse(production["eligible"])
        self.assertEqual(production["denied_reasons"], ["PROFILE_NOT_PRODUCTION"])

    def test_zte_pr_input_ready_transition_is_eligible_but_production_is_denied(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "zte_tx_mini_pr_v1")
        pr_input_ready = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PR_INPUT_READY"
        )
        production = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
        )
        self.assertTrue(pr_input_ready["eligible"])
        self.assertFalse(production["eligible"])
        self.assertEqual(production["denied_reasons"], ["PROFILE_NOT_PRODUCTION"])

    def test_2023_celcomdigi_bau_pr_input_ready_transition_is_eligible_but_production_is_denied(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        entry = next(item for item in registry["entries"] if item["profile_id"] == "celcomdigi_bau_2023_pr_v1")
        pr_input_ready = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PR_INPUT_READY"
        )
        production = next(
            item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
        )
        self.assertTrue(pr_input_ready["eligible"])
        self.assertFalse(production["eligible"])
        self.assertEqual(production["denied_reasons"], ["PROFILE_NOT_PRODUCTION"])

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
