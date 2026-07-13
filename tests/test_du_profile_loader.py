import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from du_profile_loader import ProfileValidationError, load_du_profile


class TestDuProfileLoader(unittest.TestCase):
    def test_all_pr_input_ready_profiles_have_approved_subcontractor_tss_and_remain_non_production(self):
        expected = {
            "tx_mini_pr_v1.yaml": ("docata|ZDCSZ0657770", "SubCon - TSS Team"),
            "tx_rollout_2023_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "mw_eos_swap_pr_v1.yaml": ("docata|ZDCSZ00970153", "Subcon - TSS"),
            "celcomdigi_bau_2024_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "celcomdigi_usp_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
        }
        for profile_name, (field_code, display_header) in expected.items():
            with self.subTest(profile_name=profile_name):
                profile = load_du_profile(ROOT / "config" / "du_profiles" / profile_name)
                self.assertEqual(profile["status"], "PR_INPUT_READY")
                self.assertNotEqual(profile["status"], "PRODUCTION")
                candidate = profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]
                self.assertEqual(candidate["mapping_status"], "APPROVED")
                self.assertEqual(candidate["fingerprint"]["field_code"], field_code)
                self.assertEqual(candidate["fingerprint"]["display_header"], display_header)

    def test_tx_mini_profile_loads_without_claiming_production_readiness(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        # Declared PR_INPUT_READY by JJ on 2026-07-08 after the completed field
        # review, golden-parity PASS, and negative-test sweep; still not
        # PRODUCTION, so ECC output stays blocked by the guard.
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-07-tx-mini-v1")
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["2477626672974883536"])
        self.assertEqual(profile["export_structure"]["header_rows"], [0, 1, 2, 3])
        self.assertEqual(
            profile["export_structure"]["approved_header_hashes"],
            ["167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221"],
        )
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221")
        self.assertEqual(profile["field_mapping"]["site_code"]["source_candidates"][0]["mapping_status"], "APPROVED")
        self.assertEqual(
            profile["field_mapping"]["site_code"]["source_candidates"][0]["fingerprint"]["display_header"],
            "customer site code",
        )
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Tx SOW",
        )

    def test_pr_input_ready_mw_eos_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml")
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-10-mw-eos-swap-v2")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["MW EOS Swap"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["5440935430300168497"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["7476572371505372260"])
        self.assertEqual(
            profile["export_structure"]["approved_header_hashes"],
            ["46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a"],
        )
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a")
        self.assertEqual(profile["field_mapping"]["site_code"]["source_candidates"][0]["mapping_status"], "APPROVED")
        self.assertEqual(
            profile["field_mapping"]["site_code"]["source_candidates"][0]["fingerprint"]["display_header"],
            "customer site code",
        )
        self.assertEqual(
            profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["subcontractor_ti"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon - TI",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_tss_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_ti_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )

    def test_draft_zte_tx_mini_profile_loads_with_discovery_only_candidates(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["mapping_version"], "discovery-2026-07-06-zte-tx-mini-v1")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["ZTE TX MINI"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8638668101234290847"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["2279585426760368522"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810")
        self.assertEqual(
            profile["field_mapping"]["site_code"]["source_candidates"][0]["fingerprint"]["display_header"],
            "customer site code",
        )
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Microwave Tx SOW",
        )

    def test_pr_input_ready_2023_tx_rollout_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-10-2023-tx-rollout-v2")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["2023 TX Rollout"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["1027190858144623081"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["8530399820526021092"])
        self.assertEqual(
            profile["export_structure"]["approved_header_hashes"],
            ["8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320"],
        )
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320")
        self.assertEqual(
            profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_tss_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_ti_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Post MOCN TX SOW (LLD)",
        )
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][1]["fingerprint"]["display_header"],
            "TX SOW (LLD)",
        )

    def test_draft_jendela_profile_loads_with_antenna_and_sow_candidates(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["mapping_version"], "discovery-2026-07-07-jendela-tx-migration-v1")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["Jendela TX Migration"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["4972593269368006257"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["4026888666764910245"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3")
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Tx SOW",
        )
        self.assertEqual(
            profile["field_mapping"]["antenna_size_ne"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Antenna Size NE",
        )

    def test_draft_2023_celcomdigi_bau_profile_loads_with_direct_tx_and_antenna_candidates(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2023_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["mapping_version"], "discovery-2026-07-07-2023-celcomdigi-bau-v1")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["2023 Celcomdigi BAU"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8296022438223590261"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["6611960521271999255"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "77fa728c7a4105d9062378a999228cf24575e56e82ee97bce3ab9be630d7b313")
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Tx SOW",
        )
        self.assertEqual(
            profile["field_mapping"]["antenna_size_ne"]["source_candidates"][0]["fingerprint"]["display_header"],
            "MW Config Antenna Size NE",
        )

    def test_pr_input_ready_2024_celcomdigi_bau_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2024_pr_v1.yaml")
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-10-2024-celcomdigi-bau-v2")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["2024 Celcomdigi BAU"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["7278317398457076992"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["1090541706000906451"])
        self.assertEqual(
            profile["export_structure"]["approved_header_hashes"],
            ["b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86"],
        )
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86")
        self.assertEqual(profile["field_mapping"]["site_code"]["source_candidates"][0]["mapping_status"], "APPROVED")
        self.assertEqual(
            profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Tx SOW",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_tss_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_ti_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )

    def test_pr_input_ready_celcomdigi_usp_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_usp_pr_v1.yaml")
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-10-celcomdigi-usp-v2")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["Celcomdigi USP"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["3765504705612341090"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["703232142435130905"])
        self.assertEqual(
            profile["export_structure"]["approved_header_hashes"],
            ["79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf"],
        )
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf")
        self.assertEqual(profile["field_mapping"]["site_code"]["source_candidates"][0]["mapping_status"], "APPROVED")
        self.assertEqual(
            profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["site_code"]["source_candidates"][0]["fingerprint"]["display_header"],
            "customer site code",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_tss_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            profile["field_mapping"]["existing_ti_pr_status"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )

    def test_draft_cd_consolidation_2023_decom_profile_loads_with_discovery_only_cd_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "cd_consolidation_2023_decom_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["mapping_version"], "discovery-2026-07-07-cd-consolidation-2023-decom-v1")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["CD consolidation 2023"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8359047522524182050"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["702960351133798763"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16")
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "TX SOW",
        )
        self.assertEqual(
            profile["field_mapping"]["subcontractor_ti"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TI",
        )

    def test_draft_cd_consolidation_2023_rollout_profile_loads_with_discovery_only_cd_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "cd_consolidation_2023_rollout_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["mapping_version"], "discovery-2026-07-07-cd-consolidation-2023-rollout-v1")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["CD consolidation 2023"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8359047522524182050"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["8359047522524230651"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1")
        self.assertEqual(
            profile["field_mapping"]["site_name"]["source_candidates"][0]["fingerprint"]["display_header"],
            "customer site name",
        )
        self.assertEqual(
            profile["field_mapping"]["subcontractor_ti"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TI",
        )

    def test_production_profile_requires_approved_header_hash_and_approved_mapping(self):
        base = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing approved header hash blocks PRODUCTION.
            no_hash = json.loads(json.dumps(base))
            no_hash["status"] = "PRODUCTION"
            no_hash["export_structure"]["approved_header_hashes"] = []
            path = Path(tmpdir) / "no-hash.yaml"
            path.write_text(json.dumps(no_hash), encoding="utf-8")
            with self.assertRaises(ProfileValidationError):
                load_du_profile(path)

            # A required field with a non-APPROVED mapping blocks PRODUCTION.
            unapproved = json.loads(json.dumps(base))
            unapproved["status"] = "PRODUCTION"
            unapproved["field_mapping"]["site_code"]["source_candidates"][0]["mapping_status"] = "UNVERIFIED"
            path = Path(tmpdir) / "unapproved.yaml"
            path.write_text(json.dumps(unapproved), encoding="utf-8")
            with self.assertRaises(ProfileValidationError):
                load_du_profile(path)

    def test_deprecated_profile_requires_deprecation_metadata(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        profile["status"] = "DEPRECATED"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "deprecated-without-metadata.yaml"
            path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaises(ProfileValidationError):
                load_du_profile(path)


if __name__ == "__main__":
    unittest.main()
