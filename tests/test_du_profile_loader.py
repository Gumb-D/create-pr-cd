"""DU Profile loader tests with current production lifecycle expectations."""
from __future__ import annotations

from tests.du_profile_loader_legacy_tests import TestDuProfileLoader as _LegacyTestDuProfileLoader


PRODUCTION_PROFILES = {
    "tx_mini_pr_v1.yaml": "approved-2026-07-07-tx-mini-v1",
    "tx_rollout_2023_pr_v1.yaml": "approved-2026-07-10-2023-tx-rollout-v2",
    "mw_eos_swap_pr_v1.yaml": "approved-2026-07-10-mw-eos-swap-v2",
    "celcomdigi_bau_2023_pr_v1.yaml": "approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1",
    "celcomdigi_bau_2024_pr_v1.yaml": "approved-2026-07-10-2024-celcomdigi-bau-v2",
    "celcomdigi_usp_pr_v1.yaml": "approved-2026-07-10-celcomdigi-usp-v2",
    "jendela_tx_migration_pr_v1.yaml": "approved-2026-08-04-jendela-tx-migration-v3",
    "zte_tx_mini_pr_v1.yaml": "approved-2026-07-15-zte-tx-mini-v1",
}


class TestDuProfileLoader(_LegacyTestDuProfileLoader):
    def _assert_production_profile(self, profile_name):
        profile = self._load_profile(profile_name)
        self.assertEqual(profile["status"], "PRODUCTION")
        self.assertEqual(profile["mapping_version"], PRODUCTION_PROFILES[profile_name])
        self.assertTrue(profile["export_structure"]["approved_header_hashes"])
        for canonical_field, config in profile["field_mapping"].items():
            if not config.get("required"):
                continue
            candidates = config.get("source_candidates", [])
            self.assertTrue(candidates, canonical_field)
            self.assertTrue(
                all(candidate.get("mapping_status") == "APPROVED" for candidate in candidates),
                canonical_field,
            )
        return profile

    def test_all_pr_input_ready_profiles_have_approved_subcontractor_tss_and_remain_non_production(self):
        expected = {
            "tx_mini_pr_v1.yaml": ("docata|ZDCSZ0657770", "SubCon - TSS Team"),
            "tx_rollout_2023_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "mw_eos_swap_pr_v1.yaml": ("docata|ZDCSZ00970153", "Subcon - TSS"),
            "celcomdigi_bau_2023_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "celcomdigi_bau_2024_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "celcomdigi_usp_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "jendela_tx_migration_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
            "zte_tx_mini_pr_v1.yaml": ("docata|ZDCSZ00970153", "Subcon - TSS"),
        }
        for profile_name, (field_code, display_header) in expected.items():
            with self.subTest(profile_name=profile_name):
                profile = self._assert_production_profile(profile_name)
                candidate = profile["field_mapping"]["subcontractor_tss"]["source_candidates"][0]
                self.assertEqual(candidate["mapping_status"], "APPROVED")
                self.assertEqual(candidate["fingerprint"]["field_code"], field_code)
                self.assertEqual(candidate["fingerprint"]["display_header"], display_header)

    def test_tx_mini_profile_loads_without_claiming_production_readiness(self):
        profile = self._assert_production_profile("tx_mini_pr_v1.yaml")
        old_hash = "167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221"
        revalidated_hash = "1a466e31d3c25ca73f059123d4cc33280761746ea3dca61d25a384acad5c9fde"
        supplied_hash = "830864906f3e69041995bec10b0a5840d5f8c6fa5defa2cfaef30b868b91a921"
        authoritative_fixture_hash = "99645657ed5177bed3f0af673f141dc700fb7b486743cb830d5350a473c007ff"
        approved_hashes = profile["export_structure"]["approved_header_hashes"]
        self.assertTrue({old_hash, revalidated_hash, supplied_hash}.issubset(set(approved_hashes)))
        self.assertIn(authoritative_fixture_hash, approved_hashes)
        self.assertEqual(profile["export_structure"]["observed_header_hash"], supplied_hash)
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["2477626672974883536"])

    def test_pr_input_ready_mw_eos_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._assert_production_profile("mw_eos_swap_pr_v1.yaml")
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["5440935430300168497"])
        self.assertEqual(
            profile["field_mapping"]["existing_ti_pr_status"]["transforms"],
            ["normalize_pr_reference_status"],
        )

    def test_pr_input_ready_zte_tx_mini_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._assert_production_profile("zte_tx_mini_pr_v1.yaml")
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8638668101234290847"])
        self.assertEqual(
            profile["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["display_header"],
            "Microwave Tx SOW",
        )
        self.assertFalse(profile["field_mapping"]["subcontractor_tss"]["required"])

    def test_pr_input_ready_2023_tx_rollout_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._assert_production_profile("tx_rollout_2023_pr_v1.yaml")
        old_hash = "8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320"
        new_hash = "e61b834994eeef30e7d8249f87616cb04d60598eea323feea50178fc4292c162"
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [old_hash, new_hash])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], new_hash)
        self.assertEqual(
            [
                candidate["fingerprint"]["display_header"]
                for candidate in profile["field_mapping"]["tx_sow_raw"]["source_candidates"]
            ],
            ["Post MOCN TX SOW (LLD)", "TX SOW (LLD)"],
        )

    def test_pr_input_ready_jendela_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._assert_production_profile("jendela_tx_migration_pr_v1.yaml")
        self.assertEqual(profile["profile_version"], "0.4.0")
        self.assertTrue(profile["field_mapping"]["tx_before_migration"]["required"])
        self.assertTrue(profile["field_mapping"]["final_backhaul"]["required"])
        self.assertFalse(profile["field_mapping"]["subcontractor_tss"]["required"])

    def test_pr_input_ready_2023_celcomdigi_bau_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._assert_production_profile("celcomdigi_bau_2023_pr_v1.yaml")
        self.assertEqual(profile["profile_version"], "0.2.0")
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["3882899459299681347"])
        self.assertNotIn("6611960521271999255", profile["identity"]["accepted_view_ids"])
