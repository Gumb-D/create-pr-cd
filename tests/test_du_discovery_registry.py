import sys
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_du_discovery_registry import (
    _skill_field_presence,
    build_discovery_entry,
    discovery_inventory_markdown,
    extract_du_identity,
    find_profiler_root,
    infer_project_key,
    parse_source_filename,
)


class TestDuDiscoveryRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiler_root = ROOT / find_profiler_root()

    def test_parse_source_filename(self):
        parsed = parse_source_filename("A-P202211283695_D002-MW EOS Swap-MW EOS Swap Rollout-20260703160307.xlsx")
        self.assertEqual(parsed.project_ref, "A-P202211283695_D002")
        self.assertEqual(parsed.du_model_name, "MW EOS Swap")
        self.assertEqual(parsed.view_label, "MW EOS Swap Rollout")
        self.assertEqual(parsed.timestamp, "20260703160307")

    def test_infer_project_key(self):
        self.assertEqual(infer_project_key("MW EOS Swap"), "CelcomDigi_MW")
        self.assertEqual(infer_project_key("TX Mini Project"), "Malaysia_CelcomDigi_Project")

    def test_extract_du_identity_from_header_inventory(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "site|fix00012|4188808420049567786|2477626672974883536"
                            }
                        }
                    ]
                }
            ]
        }
        identity = extract_du_identity(inventory)
        self.assertEqual(identity["du_model_id"], "4188808420049567786")
        self.assertEqual(identity["view_id"], "2477626672974883536")

    def test_build_discovery_entry_for_tx_mini(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-TX_Mini_Project-TX_Mini_PR_PO_View-20260703160246"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "TX Mini Project")
        self.assertEqual(entry["du_model_id"], "4188808420049567786")
        self.assertEqual(entry["view_id"], "2477626672974883536")
        self.assertEqual(entry["profile_id"], "tx_mini_pr_v1")
        self.assertEqual(entry["profile_version"], "0.2.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-07-tx-mini-v1")
        self.assertEqual(entry["pr_input_status"], "PR_INPUT_QUARANTINED")
        self.assertTrue(entry["skill_field_presence"]["site_id"])

    def test_build_discovery_entry_for_mw_eos_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202211283695_D002-MW_EOS_Swap-MW_EOS_Swap_Rollout-20260703160307"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "MW EOS Swap")
        self.assertEqual(entry["profile_id"], "mw_eos_swap_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-10-mw-eos-swap-v2")

    def test_build_discovery_entry_for_2023_tx_rollout_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-2023_TX_Rollout-TX_Rollout_PR_PO_View-20260703160446"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "2023 TX Rollout")
        self.assertEqual(entry["profile_id"], "tx_rollout_2023_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-10-2023-tx-rollout-v2")

    def test_build_discovery_entry_for_jendela_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-Jendela_TX_Migration-Migration_Rollout_TX_-20260703160246"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "Jendela TX Migration")
        self.assertEqual(entry["profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.2.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-13-jendela-tx-migration-v1")

    def test_build_discovery_entry_for_2023_celcomdigi_bau_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-2023_Celcomdigi_BAU-2023_Celcomdigi_BAU__TX_-20260703160239"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "2023 Celcomdigi BAU")
        self.assertEqual(entry["view_label"], "2023 Celcomdigi BAU_(TX_PRPO)")
        self.assertEqual(entry["view_id"], "3882899459299681347")
        self.assertEqual(
            entry["source_file_name"],
            "A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx",
        )
        self.assertEqual(entry["profile_id"], "celcomdigi_bau_2023_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.2.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1")
        self.assertTrue(entry["skill_field_presence"]["existing_tss_pr"])
        self.assertTrue(entry["skill_field_presence"]["existing_ti_pr"])

    def test_skill_field_presence_recognizes_direct_subcon_pr_headers(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ641766",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TSS",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ641765",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - TI",
                            }
                        },
                    ]
                }
            ]
        }
        presence = _skill_field_presence(inventory)
        self.assertTrue(presence["existing_tss_pr"])
        self.assertTrue(presence["existing_ti_pr"])

    def test_skill_field_presence_keeps_existing_non_pr_discovery_variants(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "tx-sow",
                                "wbs_stage": "TX Solution",
                                "task_name": "Post MOCN",
                                "display_header": "Post MOCN TX SOW (LLD)",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "ant-ne",
                                "wbs_stage": "Config",
                                "task_name": "Microwave",
                                "display_header": "MW Config Antenna Size NE",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "ant-fe",
                                "wbs_stage": "Config",
                                "task_name": "Microwave",
                                "display_header": "MW Config Antenna Size FE",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "tss-team",
                                "wbs_stage": "Subcon Info",
                                "task_name": "SubCon - TSS",
                                "display_header": "SubCon - TSS Team",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "ti-team",
                                "wbs_stage": "Subcon Info",
                                "task_name": "SubCon - TI",
                                "display_header": "SubCon - TI Team",
                            }
                        },
                    ]
                }
            ]
        }
        presence = _skill_field_presence(inventory)
        self.assertTrue(presence["tx_sow"])
        self.assertTrue(presence["antenna_size_ne"])
        self.assertTrue(presence["antenna_size_fe"])
        self.assertTrue(presence["subcon_tss_team"])
        self.assertTrue(presence["subcon_ti_team"])

    def test_skill_field_presence_does_not_broad_match_rectification_or_planning(self):
        inventory = {
            "sheets": [
                {
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "rect-tss",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TSS rectification status",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "rect-ti",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TI rectification status",
                            }
                        },
                        {
                            "fingerprint": {
                                "field_code": "planning",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            }
                        },
                    ]
                }
            ]
        }
        presence = _skill_field_presence(inventory)
        self.assertFalse(presence["existing_tss_pr"])
        self.assertFalse(presence["existing_ti_pr"])

    def test_non_pr_presence_matches_origin_main_baseline_for_live_exports(self):
        baseline_text = subprocess.run(
            [
                "git",
                "show",
                "origin/main:config/registries/mw_du_model_discovery_registry.yaml",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        baseline_registry = json.loads(baseline_text)
        baseline_by_source = {
            entry["source_file_name"]: entry["skill_field_presence"]
            for entry in baseline_registry["entries"]
        }
        excluded_fields = {"existing_tss_pr", "existing_ti_pr"}
        live_sources = [
            "A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx",
            "A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx",
            "A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx",
        ]

        for source_file_name in live_sources:
            profile_dir = next(
                path
                for path in self.profiler_root.iterdir()
                if path.is_dir()
                and (path / "header_inventory.json").exists()
                and json.loads((path / "header_inventory.json").read_text(encoding="utf-8"))["source"]["file_name"]
                == source_file_name
            )
            entry = build_discovery_entry(profile_dir)
            baseline_presence = baseline_by_source[source_file_name]
            for field_name, baseline_value in baseline_presence.items():
                if field_name in excluded_fields:
                    continue
                self.assertEqual(
                    entry["skill_field_presence"][field_name],
                    baseline_value,
                    f"{source_file_name} changed {field_name} from {baseline_value} to {entry['skill_field_presence'][field_name]}",
                )

        tx_rollout_entry = next(
            build_discovery_entry(path)
            for path in self.profiler_root.iterdir()
            if path.is_dir()
            and (path / "header_inventory.json").exists()
            and json.loads((path / "header_inventory.json").read_text(encoding="utf-8"))["source"]["file_name"]
            == "A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx"
        )
        tx_mini_entry = next(
            build_discovery_entry(path)
            for path in self.profiler_root.iterdir()
            if path.is_dir()
            and (path / "header_inventory.json").exists()
            and json.loads((path / "header_inventory.json").read_text(encoding="utf-8"))["source"]["file_name"]
            == "A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx"
        )
        bau_2024_entry = next(
            build_discovery_entry(path)
            for path in self.profiler_root.iterdir()
            if path.is_dir()
            and (path / "header_inventory.json").exists()
            and json.loads((path / "header_inventory.json").read_text(encoding="utf-8"))["source"]["file_name"]
            == "A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx"
        )
        self.assertTrue(tx_rollout_entry["skill_field_presence"]["tx_sow"])
        self.assertTrue(tx_mini_entry["skill_field_presence"]["subcon_tss_team"])
        self.assertTrue(tx_mini_entry["skill_field_presence"]["subcon_ti_team"])
        self.assertTrue(bau_2024_entry["skill_field_presence"]["antenna_size_ne"])
        self.assertTrue(bau_2024_entry["skill_field_presence"]["antenna_size_fe"])

    def test_build_discovery_entry_for_2024_celcomdigi_bau_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-2024_Celcomdigi_BAU-2024_BAU_Rollout_TX_-20260703160253"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "2024 Celcomdigi BAU")
        self.assertEqual(entry["profile_id"], "celcomdigi_bau_2024_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-10-2024-celcomdigi-bau-v2")

    def test_build_discovery_entry_for_celcomdigi_usp_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-Celcomdigi_USP-Celcomdigi_USP_TX_-20260703160234"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "Celcomdigi USP")
        self.assertEqual(entry["profile_id"], "celcomdigi_usp_pr_v1")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "approved-2026-07-10-celcomdigi-usp-v2")

    def test_build_discovery_entry_for_cd_consolidation_2023_decom_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-CD_consolidation_2023-CD_2023_Decom_Site-20260703160415"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "CD consolidation 2023")
        self.assertEqual(entry["profile_id"], "cd_consolidation_2023_decom_pr_v1")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "discovery-2026-07-07-cd-consolidation-2023-decom-v1")

    def test_build_discovery_entry_for_cd_consolidation_2023_rollout_uses_existing_profile_file(self):
        profile_dir = self.profiler_root / "A-P202202168750_D002-CD_consolidation_2023-CD_consolidation_2023_Rollout-20260703160351"
        entry = build_discovery_entry(profile_dir)
        self.assertEqual(entry["du_model_name"], "CD consolidation 2023")
        self.assertEqual(entry["profile_id"], "cd_consolidation_2023_rollout_pr_v1")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertEqual(entry["profile_version"], "0.1.0")
        self.assertEqual(entry["mapping_version"], "discovery-2026-07-07-cd-consolidation-2023-rollout-v1")

    def test_inventory_markdown_mentions_du(self):
        registry = {
            "entries": [
                {
                    "project_key": "CelcomDigi_MW",
                    "du_model_name": "MW EOS Swap",
                    "du_model_id": "5440935430300168497",
                    "view_label": "MW EOS Swap Rollout",
                    "view_id": "7476572371505372260",
                    "observed_header_hash": "hash",
                    "profile_id": None,
                    "pr_input_status": "PR_INPUT_QUARANTINED",
                }
            ]
        }
        markdown = discovery_inventory_markdown(registry)
        self.assertIn("MW EOS Swap", markdown)
        self.assertIn("PR_INPUT_QUARANTINED", markdown)


if __name__ == "__main__":
    unittest.main()
