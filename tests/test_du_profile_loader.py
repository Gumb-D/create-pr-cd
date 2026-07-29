"""DU Profile loader tests with current TX Rollout compatible-header expectations."""
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

    def _load_tx_rollout_profile(self):
        from pathlib import Path
        from du_profile_loader import load_du_profile

        root = Path(__file__).resolve().parent.parent
        return load_du_profile(root / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")


del _LegacyTestDuProfileLoader
