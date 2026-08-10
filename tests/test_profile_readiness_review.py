import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_readiness_review import build_readiness_entry, readiness_markdown
from du_profile_loader import load_du_profile


PRODUCTION_PROFILE_IDS = (
    "tx_mini_pr_v1",
    "tx_rollout_2023_pr_v1",
    "mw_eos_swap_pr_v1",
    "celcomdigi_bau_2023_pr_v1",
    "celcomdigi_bau_2024_pr_v1",
    "celcomdigi_usp_pr_v1",
    "jendela_tx_migration_pr_v1",
    "zte_tx_mini_pr_v1",
)


class TestProfileReadinessReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        cls.bridge = json.loads(
            (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        cls.unresolved_by_profile = {
            entry["profile_id"]: entry for entry in cls.unresolved["entries"]
        }
        cls.bridge_by_profile = {
            entry["profile_id"]: entry for entry in cls.bridge["entries"]
        }

    def _build_entry(self, profile_id):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / f"{profile_id}.yaml")
        return profile, build_readiness_entry(
            profile,
            self.unresolved_by_profile[profile_id],
            self.bridge_by_profile.get(profile_id),
        )

    def test_all_promoted_profiles_are_production_ready_without_required_field_blockers(self):
        for profile_id in PRODUCTION_PROFILE_IDS:
            with self.subTest(profile_id=profile_id):
                profile, entry = self._build_entry(profile_id)
                blockers = entry["blocker_summary"]
                self.assertEqual(profile["status"], "PRODUCTION")
                self.assertEqual(entry["profile_status"], "PRODUCTION")
                self.assertEqual(entry["readiness_status"], "PRODUCTION_READY")
                self.assertEqual(blockers["overall_blockers"], [])
                self.assertEqual(blockers["lifecycle_blockers"], [])
                self.assertEqual(blockers["missing_required_fields"], [])
                self.assertEqual(blockers["unapproved_required_fields"], [])
                self.assertEqual(blockers["required_competing_candidate_fields"], [])
                self.assertEqual(blockers["required_single_candidate_unverified_fields"], [])
                self.assertEqual(blockers["required_no_profile_selection_fields"], [])
                self.assertEqual(blockers["required_shortlist_mismatch_fields"], [])
                self.assertEqual(blockers["cross_model_bridge_fields"], [])

    def test_optional_review_work_remains_visible_but_non_blocking(self):
        expected_optional = {
            "mw_eos_swap_pr_v1": {
                "competing": ["site_name", "subcontractor_planning"],
                "single": ["du_key"],
            },
            "tx_rollout_2023_pr_v1": {
                "competing": ["subcontractor_planning"],
                "single": ["du_key", "site_name"],
            },
            "zte_tx_mini_pr_v1": {
                "competing": ["site_name", "subcontractor_planning"],
                "single": ["antenna_size_fe", "antenna_size_ne", "du_key"],
            },
            "celcomdigi_bau_2023_pr_v1": {
                "competing": ["subcontractor_planning"],
                "single": ["antenna_size_fe", "antenna_size_ne", "du_key", "site_name"],
            },
        }
        for profile_id, expected in expected_optional.items():
            with self.subTest(profile_id=profile_id):
                _, entry = self._build_entry(profile_id)
                blockers = entry["blocker_summary"]
                self.assertEqual(blockers["competing_candidate_fields"], expected["competing"])
                self.assertEqual(blockers["single_candidate_unverified_fields"], expected["single"])
                self.assertEqual(blockers["required_competing_candidate_fields"], [])
                self.assertEqual(blockers["required_single_candidate_unverified_fields"], [])
                self.assertNotIn("COMPETING_SHORTLIST_CANDIDATES", blockers["overall_blockers"])
                self.assertNotIn("UNVERIFIED_SINGLE_CANDIDATE_FIELDS", blockers["overall_blockers"])
                self.assertEqual(entry["readiness_status"], "PRODUCTION_READY")

    def test_cd_consolidation_profile_family_stays_discovery_only_blocked(self):
        profile_id = "celcomdigi_cd_consolidation_2023_pr_v1"
        profile, entry = self._build_entry(profile_id)
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
        self.assertEqual(entry["profile_status"], "DRAFT")
        self.assertEqual(entry["approved_header_hashes"], [])
        self.assertIn("PROFILE_NOT_PRODUCTION", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("NO_APPROVED_HEADER_HASH", entry["blocker_summary"]["overall_blockers"])
        self.assertIn("MISSING_REQUIRED_FIELDS", entry["blocker_summary"]["overall_blockers"])
        self.assertEqual(
            entry["blocker_summary"]["cross_model_bridge_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )
        self.assertEqual(set(row["variant_id"] for row in profile["layout_variants"]), {"decom", "rollout"})

    def test_markdown_mentions_production_and_remaining_draft_blocker(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_readiness_review.yaml").read_text(
                encoding="utf-8"
            )
        )
        markdown = readiness_markdown(registry)
        self.assertIn("PRODUCTION", markdown)
        self.assertIn("DISCOVERY_ONLY_BLOCKED", markdown)
        self.assertIn("CROSS_MODEL_BRIDGE_ONLY_FIELDS", markdown)


if __name__ == "__main__":
    unittest.main()
