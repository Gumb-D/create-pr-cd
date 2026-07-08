import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_skill_field_shortlists import build_shortlist_registry, shortlist_skill_fields


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

    def test_generated_registry_includes_zte_bau_and_usp_priority_entries(self):
        registry = build_shortlist_registry(
            [
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-TX_Mini_Project-TX_Mini_PR_PO_View-20260703160246",
                ROOT / "output" / "du-20260706-profile" / "A-P202211283695_D002-MW_EOS_Swap-MW_EOS_Swap_Rollout-20260703160307",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-2023_TX_Rollout-TX_Rollout_PR_PO_View-20260703160446",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-Jendela_TX_Migration-Migration_Rollout_TX_-20260703160246",
                ROOT / "output" / "du-20260706-profile" / "A-P202211283695_D002-ZTE_TX_MINI-ZTE_TX_MINI_v1-20260703160312",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-2023_Celcomdigi_BAU-2023_Celcomdigi_BAU__TX_-20260703160239",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-2024_Celcomdigi_BAU-2024_BAU_Rollout_TX_-20260703160253",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-Celcomdigi_USP-Celcomdigi_USP_TX_-20260703160234",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-CD_consolidation_2023-CD_2023_Decom_Site-20260703160415",
                ROOT / "output" / "du-20260706-profile" / "A-P202202168750_D002-CD_consolidation_2023-CD_consolidation_2023_Rollout-20260703160351",
            ]
        )
        source_names = [entry["source_file_name"] for entry in registry["entries"]]
        self.assertIn("A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-Jendela TX Migration-Migration Rollout (TX)-20260703160246.xlsx", source_names)
        self.assertIn("A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX)-20260703160239.xlsx", source_names)
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
