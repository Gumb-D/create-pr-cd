import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_readiness_review import build_readiness_entry, readiness_markdown
from du_profile_loader import load_du_profile


class TestProfileReadinessReview(unittest.TestCase):
    def test_tx_mini_entry_stays_discovery_only_blocked(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "tx_mini_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        # All TX Mini mapping rulings landed by 2026-07-08 and JJ declared the
        # profile PR_INPUT_READY. The only remaining fail-closed blocker is the
        # non-production lifecycle state, so output stays blocked.
        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(entry["blocker_summary"]["overall_blockers"], ["PROFILE_NOT_PRODUCTION"])
        self.assertEqual(entry["blocker_summary"]["cross_model_bridge_fields"], [])

    def test_mw_eos_entry_records_required_unapproved_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "mw_eos_swap_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, None)

        self.assertIn("REQUIRED_FIELDS_NOT_APPROVED", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["unapproved_required_fields"],
            ["region", "site_code", "subcontractor_ti", "tx_sow_raw"],
        )
        self.assertIn("site_code", entry["blocker_summary"]["competing_candidate_fields"])

    def test_2023_tx_rollout_entry_stays_discovery_only_blocked_only_for_non_production_status(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "tx_rollout_2023_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, None)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
        self.assertIn("PROFILE_NOT_PRODUCTION", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(entry["blocker_summary"]["missing_required_fields"], [])
        self.assertEqual(entry["blocker_summary"]["unapproved_required_fields"], [])
        self.assertEqual(entry["blocker_summary"]["required_competing_candidate_fields"], [])
        self.assertEqual(entry["blocker_summary"]["required_single_candidate_unverified_fields"], [])
        self.assertEqual(entry["blocker_summary"]["cross_model_bridge_fields"], [])

    def test_jendela_entry_stays_discovery_only_blocked_with_missing_pr_status_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertIn("NO_APPROVED_HEADER_HASH", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_2023_celcomdigi_bau_entry_stays_discovery_only_blocked_with_missing_pr_status_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2023_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "celcomdigi_bau_2023_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "celcomdigi_bau_2023_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertIn("NO_APPROVED_HEADER_HASH", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_2024_celcomdigi_bau_entry_stays_discovery_only_blocked_with_missing_pr_status_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2024_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "celcomdigi_bau_2024_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "celcomdigi_bau_2024_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertIn("NO_APPROVED_HEADER_HASH", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_celcomdigi_usp_entry_stays_discovery_only_blocked_with_missing_pr_status_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_usp_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "celcomdigi_usp_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "celcomdigi_usp_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertIn("NO_APPROVED_HEADER_HASH", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("COMPETING_SHORTLIST_CANDIDATES", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_cd_consolidation_2023_decom_entry_stays_discovery_only_blocked_with_competing_core_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "cd_consolidation_2023_decom_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "cd_consolidation_2023_decom_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "cd_consolidation_2023_decom_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("COMPETING_SHORTLIST_CANDIDATES", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_cd_consolidation_2023_rollout_entry_stays_discovery_only_blocked_with_competing_core_fields(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "cd_consolidation_2023_rollout_pr_v1.yaml")
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
        )
        unresolved_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "cd_consolidation_2023_rollout_pr_v1")
        bridge_entry = next(entry for entry in bridge["entries"] if entry["profile_id"] == "cd_consolidation_2023_rollout_pr_v1")

        entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)

        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("COMPETING_SHORTLIST_CANDIDATES", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )

    def test_markdown_mentions_mapping_version_and_blockers(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_readiness_review.yaml").read_text(encoding="utf-8")
        )
        markdown = readiness_markdown(registry)
        self.assertIn("discovery-2026-07-06-mw-eos-swap-v1", markdown)
        self.assertIn("DISCOVERY_ONLY_BLOCKED", markdown)
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", markdown)


if __name__ == "__main__":
    unittest.main()
