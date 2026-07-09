import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_all_du_mapping_recommendation_matrix import build_matrix_registry


def _profile(profile_id, model_name, source_file_name, header_hash, field_mapping):
    return {
        "profile_id": profile_id,
        "profile_version": "0.1.0",
        "mapping_version": f"discovery-{profile_id}",
        "status": "DRAFT",
        "identity": {"accepted_du_models": [model_name]},
        "export_structure": {"observed_header_hash": header_hash},
        "field_mapping": field_mapping,
    }


def _candidate(sheet_name, field_code, wbs_stage, task_name, display_header):
    return {
        "sheet_name": sheet_name,
        "fingerprint": {
            "field_code": field_code,
            "wbs_stage": wbs_stage,
            "task_name": task_name,
            "display_header": display_header,
        },
        "mapping_status": "UNVERIFIED",
    }


class TestAllDuMappingRecommendationMatrix(unittest.TestCase):
    def test_build_matrix_registry_creates_rows_groups_and_donor_similarity(self):
        discovery_registry = {
            "entries": [
                {
                    "profile_id": "tx_mini_pr_v1",
                    "du_model_name": "TX Mini Project",
                    "source_file_name": "tx.xlsx",
                    "view_label": "TX View",
                },
                {
                    "profile_id": "mw_eos_swap_pr_v1",
                    "du_model_name": "MW EOS Swap",
                    "source_file_name": "mw.xlsx",
                    "view_label": "MW View",
                },
            ]
        }
        grouping_registry = {
            "entries": [
                {
                    "profile_id": "tx_mini_pr_v1",
                    "closest_neighbors": [],
                },
                {
                    "profile_id": "mw_eos_swap_pr_v1",
                    "closest_neighbors": [
                        {"profile_id": "tx_mini_pr_v1", "fingerprint_similarity": 0.20},
                        {"profile_id": "mw_eos_swap_pr_v1", "fingerprint_similarity": 1.0},
                    ],
                },
            ]
        }
        unresolved_registry = {
            "entries": [
                {
                    "profile_id": "tx_mini_pr_v1",
                    "summary": {
                        "missing_required_fields": [],
                        "competing_candidate_fields": [],
                    },
                },
                {
                    "profile_id": "mw_eos_swap_pr_v1",
                    "summary": {
                        "missing_required_fields": ["existing_tss_pr_status"],
                        "competing_candidate_fields": ["tx_sow_raw"],
                    },
                },
            ]
        }
        bridge_registry = {
            "entries": [
                {"profile_id": "tx_mini_pr_v1", "field_bridges": {}},
                {
                    "profile_id": "mw_eos_swap_pr_v1",
                    "field_bridges": {
                        "existing_tss_pr_status": {
                            "review_reason": "Use donor review before deciding missing-field treatment."
                        }
                    },
                },
            ]
        }
        profiles = {
            "tx_mini_pr_v1": _profile(
                "tx_mini_pr_v1",
                "TX Mini Project",
                "tx.xlsx",
                "hash-tx",
                {
                    "site_code": {
                        "required": True,
                        "source_candidates": [
                            {
                                "fingerprint": {
                                    "field_code": "site|code",
                                    "wbs_stage": "Site Basic Info",
                                    "task_name": "Site Basic Info",
                                    "display_header": "customer site code",
                                },
                                "mapping_status": "APPROVED",
                            }
                        ],
                        "transforms": ["trim"],
                    },
                    "existing_tss_pr_status": {"required": True, "source_candidates": [], "transforms": ["trim"]},
                },
            ),
            "mw_eos_swap_pr_v1": _profile(
                "mw_eos_swap_pr_v1",
                "MW EOS Swap",
                "mw.xlsx",
                "hash-mw",
                {
                    "site_code": {
                        "required": True,
                        "source_candidates": [
                            {
                                "fingerprint": {
                                    "field_code": "site|code",
                                    "wbs_stage": "Site Basic Info",
                                    "task_name": "Site Basic Info",
                                    "display_header": "customer site code",
                                },
                                "mapping_status": "UNVERIFIED",
                            }
                        ],
                        "transforms": ["trim"],
                    },
                    "existing_tss_pr_status": {"required": True, "source_candidates": [], "transforms": ["trim"]},
                },
            ),
        }
        inventory_registry = {
            "inventory": [
                {"original_file_name": "tx.xlsx", "relative_path": "du_exports\\tx.xlsx"},
                {"original_file_name": "mw.xlsx", "relative_path": "du_exports\\mw.xlsx"},
            ]
        }
        profiler_artifacts = {
            "tx.xlsx": {
                "header_inventory": {
                    "source": {"file_name": "tx.xlsx"},
                    "sheets": [
                        {
                            "sheet_name": "data",
                            "columns": [
                                {
                                    "raw_header_values": ["site|code", "Site Basic Info", "Site Basic Info", "customer site code"],
                                    "fingerprint": {
                                        "field_code": "site|code",
                                        "wbs_stage": "Site Basic Info",
                                        "task_name": "Site Basic Info",
                                        "display_header": "customer site code",
                                    },
                                }
                            ],
                        }
                    ],
                },
                "candidates_report": {
                    "fields": {
                        "site_code": {
                            "status": "UNVERIFIED",
                            "candidates": [_candidate("data", "site|code", "Site Basic Info", "Site Basic Info", "customer site code")],
                        },
                        "existing_tss_pr_status": {"status": "MISSING", "candidates": []},
                    }
                },
                "observed_header_hash": "hash-tx",
            },
            "mw.xlsx": {
                "header_inventory": {
                    "source": {"file_name": "mw.xlsx"},
                    "sheets": [
                        {
                            "sheet_name": "data",
                            "columns": [
                                {
                                    "raw_header_values": ["site|code", "Site Basic Info", "Site Basic Info", "customer site code"],
                                    "fingerprint": {
                                        "field_code": "site|code",
                                        "wbs_stage": "Site Basic Info",
                                        "task_name": "Site Basic Info",
                                        "display_header": "customer site code",
                                    },
                                }
                            ],
                        }
                    ],
                },
                "candidates_report": {
                    "fields": {
                        "site_code": {
                            "status": "UNVERIFIED",
                            "candidates": [_candidate("data", "site|code", "Site Basic Info", "Site Basic Info", "customer site code")],
                        },
                        "existing_tss_pr_status": {"status": "MISSING", "candidates": []},
                    }
                },
                "observed_header_hash": "hash-mw",
            },
        }

        registry = build_matrix_registry(
            discovery_registry=discovery_registry,
            grouping_registry=grouping_registry,
            unresolved_registry=unresolved_registry,
            bridge_registry=bridge_registry,
            profiles=profiles,
            inventory_registry=inventory_registry,
            profiler_artifacts=profiler_artifacts,
        )

        self.assertEqual(registry["export_count"], 2)
        rows = [row for row in registry["rows"] if row["canonical_pr_field"] in {"site_code", "existing_tss_pr_status"}]
        tx_site = next(row for row in rows if row["profile_id_candidate"] == "tx_mini_pr_v1" and row["canonical_pr_field"] == "site_code")
        mw_missing = next(row for row in rows if row["profile_id_candidate"] == "mw_eos_swap_pr_v1" and row["canonical_pr_field"] == "existing_tss_pr_status")
        self.assertEqual(tx_site["ai_recommendation_class"], "HIGH_CONFIDENCE_MATCH")
        self.assertEqual(tx_site["similarity_to_tx_mini_approved_mapping"], "SELF_REFERENCE")
        self.assertEqual(tx_site["local_relative_path_under_info_reference"], "du_exports\\tx.xlsx")
        self.assertEqual(mw_missing["ai_recommendation_class"], "MISSING")
        self.assertIn("Use donor review", mw_missing["missing_field_reason"])
        self.assertIn(
            "missing_pr_critical_fields_quarantine_candidate",
            {group["group_id"] for group in registry["groups"]},
        )


if __name__ == "__main__":
    unittest.main()
