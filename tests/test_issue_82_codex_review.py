#!/usr/bin/env python3
"""Regression tests for Codex review findings on Issue #82 / PR #83."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from antenna_evidence_resolver import resolve_installation_antenna_evidence
from create_pr import CANONICAL_RENDERER_COLUMNS, _renderer_row


class TestApprovedEvidenceProvenance(unittest.TestCase):
    def test_renderer_propagates_mapping_status_for_every_new_antenna_evidence_source(self):
        record = {
            "site": {"site_code": "S1", "site_name": "", "du_key": "D1"},
            "identity": {"source_row_number": 5},
            "pr_context": {
                "tx_sow_raw": "MW SWAP",
                "tx_sow_normalized": "MW SWAP",
                "region": "Sabah",
                "state": "Sabah",
                "subcontractor_tss": "",
                "subcontractor_ti": "Seri Pancar",
            },
            "technical_context": {
                "antenna_size_ne": "2.4m",
                "antenna_size_fe": "",
                "tx_sow_details": "Install antenna 0.6m",
                "ne_sow_details": "NE antenna 2.4m",
                "fe_sow_details": "",
            },
            "source_evidence": {
                "fields": {
                    "antenna_size_ne": {"mapping_status": "APPROVED"},
                    "antenna_size_fe": {"mapping_status": "UNVERIFIED"},
                    "tx_sow_details": {"mapping_status": "APPROVED"},
                    "ne_sow_details": {"mapping_status": "UNVERIFIED"},
                    "fe_sow_details": {"mapping_status": "UNVERIFIED"},
                }
            },
            "validation": {"profile_id": "mw_eos_swap_pr_v1"},
            "approved_contract": {},
        }
        row = _renderer_row(record)
        self.assertEqual(row["Antenna Evidence Governance"], "CANONICAL_MAPPING_STATUS")
        self.assertEqual(row["Antenna Size NE Mapping Status"], "APPROVED")
        self.assertEqual(row["Antenna Size FE Mapping Status"], "UNVERIFIED")
        self.assertEqual(row["TX SOW Details Mapping Status"], "APPROVED")
        self.assertEqual(row["NE SOW Details Mapping Status"], "UNVERIFIED")
        self.assertEqual(row["FE SOW Details Mapping Status"], "UNVERIFIED")
        for column in (
            "Antenna Evidence Governance",
            "Antenna Size NE Mapping Status",
            "Antenna Size FE Mapping Status",
            "TX SOW Details Mapping Status",
            "NE SOW Details Mapping Status",
            "FE SOW Details Mapping Status",
        ):
            self.assertIn(column, CANONICAL_RENDERER_COLUMNS)

    def test_unverified_common_detail_is_ignored_in_canonical_mode(self):
        result = resolve_installation_antenna_evidence(
            {
                "Antenna Evidence Governance": "CANONICAL_MAPPING_STATUS",
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "TX SOW Details": "Install antenna 1.2m",
                "TX SOW Details Mapping Status": "UNVERIFIED",
                "NE SOW Details": "",
                "FE SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["selected_size"])

    def test_unverified_direct_size_is_ignored_in_canonical_mode(self):
        result = resolve_installation_antenna_evidence(
            {
                "Antenna Evidence Governance": "CANONICAL_MAPPING_STATUS",
                "MW Config Antenna Size NE": "1.2m",
                "Antenna Size NE Mapping Status": "UNVERIFIED",
                "MW Config Antenna Size FE": "1.2m",
                "Antenna Size FE Mapping Status": "UNVERIFIED",
                "TX SOW Details": "",
                "NE SOW Details": "",
                "FE SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "MISSING")

    def test_eos_profile_marks_only_governed_issue_82_sources_approved(self):
        profile = json.loads((REPO_ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml").read_text(encoding="utf-8"))
        self.assertEqual(profile["profile_version"], "0.1.1")
        fields = profile["field_mapping"]
        for name in ("antenna_size_ne", "antenna_size_fe", "tx_sow_details"):
            with self.subTest(name=name):
                self.assertEqual(fields[name]["source_candidates"][0]["mapping_status"], "APPROVED")
        self.assertEqual(fields["site_name"]["source_candidates"][0]["mapping_status"], "UNVERIFIED")


class TestFallbackPrecedence(unittest.TestCase):
    def test_common_fallback_cannot_replace_larger_approved_endpoint(self):
        result = resolve_installation_antenna_evidence(
            {
                "Antenna Evidence Governance": "CANONICAL_MAPPING_STATUS",
                "MW Config Antenna Size NE": "2.4m",
                "Antenna Size NE Mapping Status": "APPROVED",
                "MW Config Antenna Size FE": "",
                "Antenna Size FE Mapping Status": "APPROVED",
                "TX SOW Details": "Install antenna 0.6m",
                "TX SOW Details Mapping Status": "APPROVED",
                "NE SOW Details": "",
                "NE SOW Details Mapping Status": "UNVERIFIED",
                "FE SOW Details": "",
                "FE SOW Details Mapping Status": "UNVERIFIED",
            }
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["ne_size"], 2.4)
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 2.4)


class TestStrictDetailParsing(unittest.TestCase):
    def _resolve_common(self, text: str):
        return resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "TX SOW Details": text,
                "NE SOW Details": "",
                "FE SOW Details": "",
            }
        )

    def test_ghz_decimal_is_not_antenna_size(self):
        result = self._resolve_common("Upgrade radio to 2.4 GHz")
        self.assertEqual(result["status"], "MISSING")

    def test_ip_address_is_not_antenna_size(self):
        result = self._resolve_common("New IP 1.2.3.4")
        self.assertEqual(result["status"], "MISSING")

    def test_bare_decimal_requires_antenna_specific_phrase(self):
        result = self._resolve_common("MW swap; install antenna size 1.2")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["selected_size"], 1.2)

    def test_endpoint_detail_cable_length_is_not_antenna_evidence(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "Install IF cable 3.0m",
                "FE SOW Details": "Install IF cable 3.0m",
                "TX SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["selected_size"])

    def test_endpoint_detail_explicit_antenna_value_still_resolves(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "Install antenna 0.6m",
                "FE SOW Details": "Target antenna 1.2m",
                "TX SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["selected_size"], 1.2)

    def test_common_detail_uses_install_size_not_larger_dismantle_size(self):
        result = self._resolve_common(
            "Dismantle existing antenna 2.4m and install new antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["selected_size"], 0.6)
        self.assertEqual(result["common_size"], 0.6)

    def test_endpoint_detail_uses_install_size_not_larger_dismantle_size(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "Dismantle existing antenna 2.4m; install new antenna 0.6m",
                "FE SOW Details": "Install target antenna 1.2m",
                "TX SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["ne_size"], 0.6)
        self.assertEqual(result["fe_size"], 1.2)
        self.assertEqual(result["selected_size"], 1.2)

    def test_dismantle_only_detail_is_not_installation_evidence(self):
        result = self._resolve_common("Dismantle existing antenna 2.4m")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["selected_size"])


class TestDirectSizeCompatibility(unittest.TestCase):
    def test_direct_meter_and_metre_spellings_remain_supported(self):
        for spelling in ("0.6 meter", "0.6 metre", "0.6 meters", "0.6 metres"):
            with self.subTest(spelling=spelling):
                result = resolve_installation_antenna_evidence(
                    {
                        "MW Config Antenna Size NE": spelling,
                        "MW Config Antenna Size FE": spelling,
                        "NE SOW Details": "",
                        "FE SOW Details": "",
                        "TX SOW Details": "",
                    }
                )
                self.assertEqual(result["status"], "RESOLVED")
                self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
