import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_mw_pair_divergence_review import build_pair_review, pair_review_markdown


class TestMwPairDivergenceReview(unittest.TestCase):
    def test_pair_review_marks_matching_and_diverging_fields(self):
        left = json.loads((ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml").read_text(encoding="utf-8"))
        right = json.loads((ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml").read_text(encoding="utf-8"))

        review = build_pair_review(left, right)

        self.assertEqual(review["left_profile_id"], "mw_eos_swap_pr_v1")
        self.assertEqual(review["right_profile_id"], "zte_tx_mini_pr_v1")
        self.assertEqual(review["left_profile_version"], "0.1.1")
        self.assertEqual(review["right_profile_version"], "0.2.0")
        self.assertEqual(review["left_observed_header_hash"], "46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a")
        self.assertEqual(review["right_observed_header_hash"], "a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810")
        self.assertEqual(review["field_differences"]["region"]["comparison_status"], "MATCHING_SELECTED_SOURCE")
        self.assertEqual(review["field_differences"]["tx_sow_raw"]["comparison_status"], "DIFFERENT_SELECTED_SOURCE")
        self.assertEqual(review["field_differences"]["subcontractor_ti"]["comparison_status"], "DIFFERENT_SELECTED_SOURCE")
        self.assertEqual(review["field_differences"]["boq_configuration"]["comparison_status"], "BOTH_MISSING_OPTIONAL")

    def test_pair_review_counts_shared_missing_required_fields(self):
        left = json.loads((ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml").read_text(encoding="utf-8"))
        right = json.loads((ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml").read_text(encoding="utf-8"))

        review = build_pair_review(left, right)

        self.assertEqual(sorted(review["summary"]["shared_missing_required_fields"]), [])

    def test_markdown_mentions_difference_status(self):
        registry = {
            "pair_reviews": [
                {
                    "left_profile_id": "mw_eos_swap_pr_v1",
                    "right_profile_id": "zte_tx_mini_pr_v1",
                    "left_profile_version": "0.1.0",
                    "right_profile_version": "0.1.0",
                    "left_observed_header_hash": "hash-left",
                    "right_observed_header_hash": "hash-right",
                    "summary": {"shared_missing_required_fields": ["existing_ti_pr_status"]},
                    "field_differences": {
                        "tx_sow_raw": {
                            "comparison_status": "DIFFERENT_SELECTED_SOURCE",
                            "left_display_header": "Microwave Tx SOW-1",
                            "right_display_header": "Microwave Tx SOW",
                            "review_reason": "The two MW profiles currently select different source columns for the same canonical field.",
                        }
                    },
                }
            ]
        }

        markdown = pair_review_markdown(registry)

        self.assertIn("DIFFERENT_SELECTED_SOURCE", markdown)
        self.assertIn("Microwave Tx SOW-1", markdown)
        self.assertIn("existing_ti_pr_status", markdown)
        self.assertIn("hash-left", markdown)


if __name__ == "__main__":
    unittest.main()
