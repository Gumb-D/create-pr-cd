import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_skill_field_shortlists import shortlist_skill_fields


class TestSkillFieldShortlists(unittest.TestCase):
    def test_site_id_prefers_customer_site_code(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ALT",
                                "wbs_stage": "Planner",
                                "task_name": "Microwave",
                                "display_header": "FE Site ID",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                        {
                            "fingerprint": {
                                "field_code": "site|fix00012|1|2",
                                "wbs_stage": "Site Basic Info",
                                "task_name": "Site Basic Info",
                                "display_header": "customer site code",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["site_id"][0]["fingerprint"]["display_header"], "customer site code")

    def test_tx_sow_prefers_direct_field_over_details(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "a",
                                "wbs_stage": "TX Solution",
                                "task_name": "TX SOW Details",
                                "display_header": "TX SOW Details",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                        {
                            "fingerprint": {
                                "field_code": "b",
                                "wbs_stage": "Installation",
                                "task_name": "Microwave",
                                "display_header": "Tx SOW",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["tx_sow"][0]["fingerprint"]["display_header"], "Tx SOW")

    def test_ti_subcon_prefers_team_field_over_pr_field(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "pr",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TI",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                        {
                            "fingerprint": {
                                "field_code": "team",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "SubCon - TI Team",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["subcon_ti_team"][0]["fingerprint"]["display_header"], "SubCon - TI Team")

    def test_existing_ti_pr_prefers_exact_status(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "rect",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TI rectification status",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                        {
                            "fingerprint": {
                                "field_code": "status",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TI Status",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["existing_ti_pr"][0]["fingerprint"]["display_header"], "PR TI Status")

    def test_existing_pr_shortlists_prefer_direct_subcon_pr_headers(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "tss-rect",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TSS rectification status",
                            },
                            "source_position": {"one_based_index": 3},
                        },
                        {
                            "fingerprint": {
                                "field_code": "ti-rect",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TI rectification status",
                            },
                            "source_position": {"one_based_index": 4},
                        },
                        {
                            "fingerprint": {
                                "field_code": "tss-pr",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TSS",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                        {
                            "fingerprint": {
                                "field_code": "ti-pr",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TI",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["existing_tss_pr"][0]["fingerprint"]["display_header"], "Subcon PR - TSS")
        self.assertEqual(shortlists["existing_ti_pr"][0]["fingerprint"]["display_header"], "Subcon PR - TI")
        self.assertLess(shortlists["existing_tss_pr"][1]["score"], shortlists["existing_tss_pr"][0]["score"])
        self.assertLess(shortlists["existing_ti_pr"][1]["score"], shortlists["existing_ti_pr"][0]["score"])

    def test_team_shortlists_exclude_pr_headers_but_keep_direct_subcon_fields(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "tss-team",
                                "wbs_stage": "Subcon Info",
                                "task_name": "SubCon - TSS",
                                "display_header": "SubCon - TSS",
                            },
                            "source_position": {"one_based_index": 1},
                        },
                        {
                            "fingerprint": {
                                "field_code": "ti-team",
                                "wbs_stage": "Subcon Info",
                                "task_name": "SubCon - TI",
                                "display_header": "SubCon - TI",
                            },
                            "source_position": {"one_based_index": 2},
                        },
                        {
                            "fingerprint": {
                                "field_code": "tss-pr",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TSS",
                            },
                            "source_position": {"one_based_index": 3},
                        },
                        {
                            "fingerprint": {
                                "field_code": "ti-pr",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TI",
                            },
                            "source_position": {"one_based_index": 4},
                        },
                    ]
                }
            ]
        }
        shortlists = shortlist_skill_fields(inventory)
        self.assertEqual(shortlists["subcon_tss_team"][0]["fingerprint"]["display_header"], "SubCon - TSS")
        self.assertEqual(shortlists["subcon_ti_team"][0]["fingerprint"]["display_header"], "SubCon - TI")
        self.assertNotIn("Subcon PR - TSS", [item["fingerprint"]["display_header"] for item in shortlists["subcon_tss_team"]])
        self.assertNotIn("Subcon PR - TI", [item["fingerprint"]["display_header"] for item in shortlists["subcon_ti_team"]])

    def test_generated_registry_includes_zte_bau_and_usp_priority_entries(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        source_names = [entry["source_file_name"] for entry in registry["entries"]]
        self.assertIn("A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-Jendela TX Migration-Migration Rollout (TX)-20260703160246.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-Celcomdigi USP-Celcomdigi USP (TX)-20260703160234.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx", source_names)
        decom_entry = next(
            entry for entry in registry["entries"]
            if entry["source_file_name"] == "A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx"
        )
        rollout_entry = next(
            entry for entry in registry["entries"]
            if entry["source_file_name"] == "A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx"
        )
        self.assertEqual(decom_entry["observed_header_hash"], "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16")
        self.assertEqual(rollout_entry["observed_header_hash"], "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1")



if __name__ == "__main__":
    unittest.main()
