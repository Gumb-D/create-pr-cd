#!/usr/bin/env python3
"""Canonical Planning field/scope regression coverage for Issue #34."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from canonical_input_pipeline import _required_fields_for_scope  # noqa: E402
from canonical_site_validator import PR_INPUT_READY, empty_canonical_site_record  # noqa: E402
from du_export_adapter import PR_STATUS_NONE, build_canonical_site_record  # noqa: E402
from profile_du_export import fingerprint_key  # noqa: E402


def _fp(code: str, display: str) -> dict[str, str]:
    return {
        "field_code": code,
        "wbs_stage": "Installation",
        "task_name": "Wireless RAN",
        "display_header": display,
    }


class PlanningCanonicalContractTest(unittest.TestCase):
    def test_empty_record_contains_planning_duplicate_status(self):
        record = empty_canonical_site_record()
        self.assertIn("existing_planning_pr_status", record["pr_context"])
        self.assertEqual(record["pr_context"]["existing_planning_pr_status"], "")

    def test_planning_pipeline_does_not_inherit_tss_ti_required_fields(self):
        profile = {
            "field_mapping": {
                "site_code": {"required": True},
                "region": {"required": True},
                "tx_sow_raw": {"required": True},
                "subcontractor_ti": {"required": True},
                "existing_ti_pr_status": {"required": True},
                "subcontractor_planning": {"required": False},
                "existing_planning_pr_status": {"required": False},
            }
        }
        required = _required_fields_for_scope(profile, "Planning")
        self.assertEqual(
            required,
            {"site_code", "region", "subcontractor_planning", "existing_planning_pr_status"},
        )
        self.assertNotIn("tx_sow_raw", required)
        self.assertNotIn("subcontractor_ti", required)
        self.assertNotIn("existing_ti_pr_status", required)

    def test_existing_tss_ti_scopes_keep_profile_required_fields(self):
        profile = {
            "field_mapping": {
                "site_code": {"required": True},
                "region": {"required": True},
                "tx_sow_raw": {"required": True},
                "subcontractor_ti": {"required": True},
                "existing_ti_pr_status": {"required": True},
            }
        }
        required = _required_fields_for_scope(profile, "TI")
        self.assertIn("tx_sow_raw", required)
        self.assertIn("subcontractor_ti", required)
        self.assertIn("existing_ti_pr_status", required)

    def test_planning_scope_maps_and_validates_without_tx_sow(self):
        site_fp = _fp("SITE", "customer site code")
        region_fp = _fp("REGION", "region")
        subcon_fp = _fp("PLANNING_SUBCON", "Subcon Planning")
        status_fp = _fp("PLANNING_PR", "Subcon PR - Planning")
        profile = {
            "profile_id": "planning-test-profile",
            "profile_version": "1.0.0",
            "mapping_version": "planning-test-v1",
            "identity": {"project_key": "Malaysia_CelcomDigi_Project"},
            "field_mapping": {
                "site_code": {"transforms": ["trim", "uppercase"]},
                "region": {"transforms": ["trim"]},
                "subcontractor_planning": {"transforms": ["trim"]},
                "existing_planning_pr_status": {"transforms": ["normalize_pr_reference_status"]},
            },
        }
        resolved = {
            "site_code": {"status": "RESOLVED", "matches": [{"fingerprint": site_fp, "mapping_status": "APPROVED"}]},
            "region": {"status": "RESOLVED", "matches": [{"fingerprint": region_fp, "mapping_status": "APPROVED"}]},
            "subcontractor_planning": {"status": "RESOLVED", "matches": [{"fingerprint": subcon_fp, "mapping_status": "APPROVED"}]},
            "existing_planning_pr_status": {"status": "RESOLVED", "matches": [{"fingerprint": status_fp, "mapping_status": "APPROVED"}]},
        }
        values = {
            fingerprint_key(site_fp): " a0001 ",
            fingerprint_key(region_fp): " Central ",
            fingerprint_key(subcon_fp): " GCI_AA ",
            fingerprint_key(status_fp): "",
        }
        record = build_canonical_site_record(
            values,
            profile,
            {
                "du_model_name": "2024 Celcomdigi BAU",
                "du_model_id": "7278317398457076992",
                "view_id": "1090541706000906451",
                "source_file_name": "planning.xlsx",
                "source_file_hash": "source-hash",
                "header_hash": "header-hash",
                "source_row_number": 5,
            },
            scope="Planning",
            resolved_mappings=resolved,
        )
        self.assertEqual(record["site"]["site_code"], "A0001")
        self.assertEqual(record["pr_context"]["subcontractor_planning"], "GCI_AA")
        self.assertEqual(record["pr_context"]["existing_planning_pr_status"], PR_STATUS_NONE)
        self.assertEqual(record["validation"]["pr_input_classification"], PR_INPUT_READY)
        self.assertNotIn("tx_sow_raw", record["validation"]["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
