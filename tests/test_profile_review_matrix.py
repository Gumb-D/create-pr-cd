import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_review_matrix import build_review_matrix_registry, review_matrix_markdown


class TestProfileReviewMatrix(unittest.TestCase):
    def test_registry_groups_shared_missing_required_fields(self):
        action_queue = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )

        registry = build_review_matrix_registry(action_queue)

        existing_ti = next(
            item
            for item in registry["batch_review_queue"]
            if item["action_type"] == "RESOLVE_MISSING_REQUIRED_FIELD" and item["field_name"] == "existing_ti_pr_status"
        )
        # tx_mini_pr_v1 left this batch on 2026-07-07, and mw_eos_swap_pr_v1,
        # celcomdigi_bau_2024_pr_v1, and celcomdigi_usp_pr_v1 left it on
        # 2026-07-09 when their approved PR-critical mappings landed.
        self.assertEqual(existing_ti["profile_count"], 5)
        self.assertEqual(
            existing_ti["profiles"],
            [
                "cd_consolidation_2023_decom_pr_v1",
                "cd_consolidation_2023_rollout_pr_v1",
                "celcomdigi_bau_2023_pr_v1",
                "jendela_tx_migration_pr_v1",
                "zte_tx_mini_pr_v1",
            ],
        )
        self.assertEqual(existing_ti["batch_priority"], 1)

    def test_registry_captures_profile_specific_work(self):
        action_queue = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )

        registry = build_review_matrix_registry(action_queue)

        tx_region = next(
            item
            for item in registry["batch_review_queue"]
            if item["action_type"] == "VERIFY_SINGLE_CANDIDATE" and item["field_name"] == "region"
        )
        # tx_mini_pr_v1 left this batch on 2026-07-07, and tx_rollout_2023_pr_v1,
        # mw_eos_swap_pr_v1, celcomdigi_bau_2024_pr_v1, and celcomdigi_usp_pr_v1
        # left it on 2026-07-09 when region was approved for PR input review.
        self.assertEqual(tx_region["profile_count"], 3)
        self.assertNotIn("tx_mini_pr_v1", tx_region["profiles"])
        self.assertNotIn("tx_rollout_2023_pr_v1", tx_region["profiles"])
        self.assertNotIn("mw_eos_swap_pr_v1", tx_region["profiles"])
        self.assertNotIn("celcomdigi_bau_2024_pr_v1", tx_region["profiles"])
        self.assertNotIn("celcomdigi_usp_pr_v1", tx_region["profiles"])
        tx_summary = next(item for item in registry["profile_summaries"] if item["profile_id"] == "tx_mini_pr_v1")
        self.assertEqual(tx_summary["profile_version"], "0.2.0")
        self.assertEqual(tx_summary["observed_header_hash"], "167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221")

        tx_site_name = next(
            item
            for item in registry["batch_review_queue"]
            if item["action_type"] == "VERIFY_SINGLE_CANDIDATE" and item["field_name"] == "site_name"
        )
        self.assertEqual(tx_site_name["profile_count"], 4)
        self.assertEqual(
            tx_site_name["profiles"],
            [
                "cd_consolidation_2023_rollout_pr_v1",
                "celcomdigi_bau_2023_pr_v1",
                "celcomdigi_bau_2024_pr_v1",
                "tx_rollout_2023_pr_v1",
            ],
        )

    def test_markdown_mentions_batch_priority_and_profile_summary(self):
        action_queue = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
        )

        registry = build_review_matrix_registry(action_queue)
        markdown = review_matrix_markdown(registry)

        self.assertIn("# MW DU Profile Review Matrix", markdown)
        self.assertIn("Batch priority", markdown)
        self.assertIn("existing_ti_pr_status", markdown)
        self.assertIn("tx_mini_pr_v1", markdown)
        self.assertIn("Observed header hash", markdown)


if __name__ == "__main__":
    unittest.main()
