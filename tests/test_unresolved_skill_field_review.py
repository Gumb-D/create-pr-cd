import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_unresolved_skill_field_review import build_review_entry, build_review_registry, review_markdown


class TestUnresolvedSkillFieldReview(unittest.TestCase):
    def test_approval_resolves_competition_but_unverified_selection_does_not(self):
        def profile_with_status(mapping_status):
            return {
                "profile_id": "synthetic_pr_v1",
                "profile_version": "0.1.0",
                "mapping_version": "synthetic-v1",
                "status": "DRAFT",
                "identity": {"accepted_du_models": ["Synthetic DU"]},
                "export_structure": {"observed_header_hash": "synthetic-hash"},
                "field_mapping": {
                    "tx_sow_raw": {
                        "required": True,
                        "source_candidates": [
                            {
                                "fingerprint": {
                                    "field_code": "docata|SOW1",
                                    "wbs_stage": "Installation",
                                    "task_name": "Microwave",
                                    "display_header": "Tx SOW",
                                },
                                "mapping_status": mapping_status,
                            }
                        ],
                    }
                },
            }

        shortlist_entry = {
            "source_file_name": "synthetic.xlsx",
            "skill_field_shortlists": {
                "tx_sow": [
                    {
                        "score": 100,
                        "reason": "Direct Tx SOW field.",
                        "fingerprint": {
                            "field_code": "docata|SOW1",
                            "wbs_stage": "Installation",
                            "task_name": "Microwave",
                            "display_header": "Tx SOW",
                        },
                    },
                    {
                        "score": 45,
                        "reason": "SOW details field.",
                        "fingerprint": {
                            "field_code": "docata|SOW2",
                            "wbs_stage": "TX Solution",
                            "task_name": "TX SOW Details",
                            "display_header": "TX SOW Details",
                        },
                    },
                ]
            },
        }

        unverified = build_review_entry(profile_with_status("UNVERIFIED"), shortlist_entry)
        self.assertEqual(
            unverified["field_reviews"]["tx_sow_raw"]["review_status"], "REVIEW_REQUIRED_COMPETING_CANDIDATES"
        )
        self.assertEqual(unverified["summary"]["competing_candidate_fields"], ["tx_sow_raw"])

        approved = build_review_entry(profile_with_status("APPROVED"), shortlist_entry)
        self.assertEqual(
            approved["field_reviews"]["tx_sow_raw"]["review_status"], "RESOLVED_BY_APPROVED_MAPPING"
        )
        self.assertEqual(approved["summary"]["competing_candidate_fields"], [])
        self.assertEqual(approved["summary"]["resolved_by_approval_fields"], ["tx_sow_raw"])

    def test_tx_mini_entry_flags_missing_and_competing_fields(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = shortlist_registry["entries"][0]

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "tx_mini_pr_v1")
        self.assertEqual(review_entry["source_file_name"], shortlist_entry["source_file_name"])
        # Every TX Mini ruling landed by 2026-07-08: nothing is missing or
        # competing, and the human-approved selections record their rejected
        # shortlist alternates as resolved-by-approval.
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertEqual(review_entry["summary"]["competing_candidate_fields"], [])
        self.assertEqual(
            review_entry["summary"]["resolved_by_approval_fields"],
            ["subcontractor_planning", "tx_sow_raw"],
        )
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["review_status"], "RESOLVED_BY_APPROVED_MAPPING"
        )
        # Rejected alternates stay listed for traceability.
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["alternate_candidates"][0]["fingerprint"]["display_header"],
            "TX SOW Details",
        )
        self.assertEqual(
            review_entry["field_reviews"]["site_code"]["recommended_source"]["fingerprint"]["display_header"],
            "customer site code",
        )

    def test_mw_eos_entry_records_human_approved_pr_critical_sources(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = shortlist_registry["entries"][1]

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "mw_eos_swap_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertEqual(review_entry["summary"]["no_profile_selection_fields"], [])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["alternate_candidates"][0]["fingerprint"]["display_header"],
            "TX SOW Details",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_tss_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["review_status"],
            "RESOLVED_BY_APPROVED_MAPPING",
        )

    def test_zte_entry_flags_same_missing_required_fields(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "ZTE TX MINI" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "zte_tx_mini_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertEqual(
            review_entry["summary"]["no_profile_selection_fields"],
            ["existing_ti_pr_status", "existing_tss_pr_status"],
        )
        self.assertIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])

    def test_2023_tx_rollout_entry_records_human_approved_pr_critical_sources(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "2023 TX Rollout" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "tx_rollout_2023_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertEqual(review_entry["summary"]["no_profile_selection_fields"], [])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["existing_tss_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["recommended_source"]["fingerprint"]["display_header"],
            "Post MOCN TX SOW (LLD)",
        )
        self.assertEqual(
            review_entry["field_reviews"]["tx_sow_raw"]["review_status"],
            "RESOLVED_BY_APPROVED_MAPPING",
        )

    def test_jendela_entry_records_human_approved_pr_critical_sources(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "Jendela TX Migration" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["existing_tss_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertIn("subcontractor_planning", review_entry["summary"]["competing_candidate_fields"])

    def test_2023_celcomdigi_bau_entry_uses_corrected_tx_prpo_candidates(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "celcomdigi_bau_2023_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "2023 Celcomdigi BAU" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "celcomdigi_bau_2023_pr_v1")
        self.assertEqual(review_entry["source_file_name"], "A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx")
        self.assertEqual(review_entry["profile_status"], "PR_INPUT_READY")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertIn("subcontractor_planning", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["summary"]["single_candidate_unverified_fields"],
            ["antenna_size_fe", "antenna_size_ne", "du_key", "site_name"],
        )
        self.assertEqual(
            review_entry["summary"]["resolved_by_approval_fields"],
            [
                "existing_ti_pr_status",
                "existing_tss_pr_status",
                "region",
                "site_code",
                "subcontractor_ti",
                "subcontractor_tss",
                "tx_sow_raw",
            ],
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_tss_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TSS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            review_entry["field_reviews"]["antenna_size_ne"]["recommended_source"]["fingerprint"]["display_header"],
            "MW Config Antenna Size NE",
        )

    def test_2024_celcomdigi_bau_entry_records_human_approved_pr_critical_sources(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "celcomdigi_bau_2024_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "2024 Celcomdigi BAU" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "celcomdigi_bau_2024_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("subcontractor_planning", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["review_status"],
            "READY_IF_APPROVAL_EVIDENCE_EXISTS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["antenna_size_ne"]["recommended_source"]["fingerprint"]["display_header"],
            "MW Config Antenna Size NE",
        )

    def test_celcomdigi_usp_entry_records_human_approved_pr_critical_sources(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "celcomdigi_usp_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "Celcomdigi USP" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "celcomdigi_usp_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
        self.assertNotIn("site_code", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("site_name", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("subcontractor_planning", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
            "Subcon PR - TI",
        )
        self.assertEqual(
            review_entry["field_reviews"]["existing_ti_pr_status"]["review_status"],
            "READY_IF_APPROVAL_EVIDENCE_EXISTS",
        )
        self.assertEqual(
            review_entry["field_reviews"]["antenna_size_ne"]["recommended_source"]["fingerprint"]["display_header"],
            "Antenna Size NE",
        )

    def test_cd_consolidation_2023_decom_entry_captures_missing_pr_status_fields_and_competing_core_fields(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "cd_consolidation_2023_decom_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "CD 2023 Decom Site" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "cd_consolidation_2023_decom_pr_v1")
        self.assertEqual(
            review_entry["source_file_name"],
            "A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx",
        )
        self.assertEqual(review_entry["summary"]["missing_required_fields"], ["existing_ti_pr_status", "existing_tss_pr_status"])
        self.assertIn("site_code", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("region", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["subcontractor_ti"]["recommended_source"]["fingerprint"]["display_header"],
            "SubCon - TI",
        )

    def test_cd_consolidation_2023_rollout_entry_captures_missing_pr_status_fields_and_competing_core_fields(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profile = json.loads((ROOT / "config" / "du_profiles" / "cd_consolidation_2023_rollout_pr_v1.yaml").read_text(encoding="utf-8"))
        shortlist_entry = next(
            entry for entry in shortlist_registry["entries"] if "CD consolidation 2023 Rollout" in entry["source_file_name"]
        )

        review_entry = build_review_entry(profile, shortlist_entry)

        self.assertEqual(review_entry["profile_id"], "cd_consolidation_2023_rollout_pr_v1")
        self.assertEqual(review_entry["summary"]["missing_required_fields"], ["existing_ti_pr_status", "existing_tss_pr_status"])
        self.assertIn("site_code", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
        self.assertIn("subcontractor_ti", review_entry["summary"]["single_candidate_unverified_fields"])
        self.assertEqual(
            review_entry["field_reviews"]["site_name"]["recommended_source"]["fingerprint"]["display_header"],
            "customer site name",
        )

    def test_markdown_mentions_review_reasons(self):
        registry = {
            "entries": [
                {
                    "profile_id": "tx_mini_pr_v1",
                    "du_model_name": "TX Mini Project",
                    "source_file_name": "tx-mini.xlsx",
                    "summary": {
                        "missing_required_fields": ["existing_ti_pr_status"],
                        "competing_candidate_fields": ["tx_sow_raw"],
                        "single_candidate_unverified_fields": ["site_code"],
                    },
                    "field_reviews": {
                        "tx_sow_raw": {
                            "skill_field": "tx_sow",
                            "required": True,
                            "selected_status": "UNVERIFIED",
                            "recommended_source": {
                                "fingerprint": {
                                    "field_code": "docata|1",
                                    "wbs_stage": "Installation",
                                    "task_name": "Microwave",
                                    "display_header": "Tx SOW",
                                },
                                "mapping_status": "UNVERIFIED",
                            },
                            "alternate_candidates": [
                                {
                                    "score": 45,
                                    "fingerprint": {
                                        "field_code": "docata|2",
                                        "wbs_stage": "TX Solution",
                                        "task_name": "TX SOW Details",
                                        "display_header": "TX SOW Details",
                                    },
                                    "reason": "SOW details field; likely evidence, not primary trigger.",
                                }
                            ],
                            "review_status": "REVIEW_REQUIRED_COMPETING_CANDIDATES",
                            "review_reason": "Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.",
                        }
                    },
                }
            ]
        }

        markdown = review_markdown(registry)

        self.assertIn("REVIEW_REQUIRED_COMPETING_CANDIDATES", markdown)
        self.assertIn("existing_ti_pr_status", markdown)
        self.assertIn("TX SOW Details", markdown)

    def test_registry_distinguishes_same_du_model_profiles_by_header_hash(self):
        shortlist_registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
        )
        profiles = [
            json.loads((ROOT / "config" / "du_profiles" / "cd_consolidation_2023_decom_pr_v1.yaml").read_text(encoding="utf-8")),
            json.loads((ROOT / "config" / "du_profiles" / "cd_consolidation_2023_rollout_pr_v1.yaml").read_text(encoding="utf-8")),
        ]

        registry = build_review_registry(profiles, shortlist_registry)
        by_profile = {entry["profile_id"]: entry for entry in registry["entries"]}

        self.assertEqual(
            by_profile["cd_consolidation_2023_decom_pr_v1"]["source_file_name"],
            "A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx",
        )
        self.assertEqual(
            by_profile["cd_consolidation_2023_rollout_pr_v1"]["source_file_name"],
            "A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx",
        )


if __name__ == "__main__":
    unittest.main()
