"""DU Profile loader tests with current compatible-layout expectations."""
from __future__ import annotations

from tests.du_profile_loader_legacy_tests import TestDuProfileLoader as _LegacyTestDuProfileLoader


class TestDuProfileLoader(_LegacyTestDuProfileLoader):
    def test_pr_input_ready_2023_tx_rollout_profile_loads_with_human_approved_pr_critical_mappings(self):
        profile = self._load_tx_rollout_profile()
        old_hash = "8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320"
        new_hash = "e61b834994eeef30e7d8249f87616cb04d60598eea323feea50178fc4292c162"
        self.assertEqual(profile["status"], "PR_INPUT_READY")
        self.assertEqual(profile["profile_version"], "0.1.1")
        self.assertEqual(profile["mapping_version"], "approved-2026-07-10-2023-tx-rollout-v2")
        self.assertEqual(profile["identity"]["accepted_du_models"], ["2023 TX Rollout"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["1027190858144623081"])
        self.assertEqual(profile["identity"]["accepted_view_ids"], ["8530399820526021092"])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [old_hash, new_hash])
        self.assertEqual(profile["export_structure"]["observed_header_hash"], new_hash)
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

    def test_draft_cd_consolidation_2023_decom_profile_loads_with_discovery_only_cd_fields(self):
        profile = self._load_cd_consolidation_profile()
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(
            profile["mapping_version"],
            "discovery-2026-08-05-cd-consolidation-2023-family-v1",
        )
        self.assertEqual(profile["identity"]["accepted_du_models"], ["CD consolidation 2023"])
        self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["8359047522524182050"])
        self.assertEqual(
            profile["identity"]["accepted_view_ids"],
            ["702960351133798763", "8359047522524230651"],
        )
        variants = {row["variant_id"]: row for row in profile["layout_variants"]}
        decom = variants["decom"]
        self.assertEqual(decom["view_id"], "702960351133798763")
        self.assertEqual(
            decom["observed_header_hash"],
            "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16",
        )
        self.assertEqual(
            decom["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["task_name"],
            "TX Final SOW (LLD)",
        )
        self.assertEqual(
            decom["field_mapping"]["subcontractor_ti"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TI",
        )

    def test_draft_cd_consolidation_2023_rollout_profile_loads_with_discovery_only_cd_fields(self):
        profile = self._load_cd_consolidation_profile()
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        variants = {row["variant_id"]: row for row in profile["layout_variants"]}
        rollout = variants["rollout"]
        self.assertEqual(rollout["view_id"], "8359047522524230651")
        self.assertEqual(
            rollout["observed_header_hash"],
            "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1",
        )
        self.assertEqual(
            rollout["field_mapping"]["tx_sow_raw"]["source_candidates"][0]["fingerprint"]["task_name"],
            "Wireless RAN",
        )
        self.assertEqual(
            rollout["field_mapping"]["subcontractor_ti"]["source_candidates"][0]["fingerprint"]["display_header"],
            "SubCon - TI",
        )

    def _load_tx_rollout_profile(self):
        from pathlib import Path
        from du_profile_loader import load_du_profile

        root = Path(__file__).resolve().parent.parent
        return load_du_profile(root / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")

    def _load_cd_consolidation_profile(self):
        from pathlib import Path
        from du_profile_loader import load_du_profile

        root = Path(__file__).resolve().parent.parent
        return load_du_profile(
            root / "config" / "du_profiles" / "celcomdigi_cd_consolidation_2023_pr_v1.yaml"
        )


del _LegacyTestDuProfileLoader
