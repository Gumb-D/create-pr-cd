import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import PR_INPUT_INCOMPLETE, PR_INPUT_QUARANTINED, PR_INPUT_READY, empty_canonical_site_record, validate_canonical_site_record
from pr_input_gate import gate_canonical_site_record, gate_raw_iepms_export


def fingerprint(name: str):
    return {"field_code": name, "wbs_stage": "WBS", "task_name": "Task", "display_header": name}


class TestCanonicalSiteValidator(unittest.TestCase):
    def _ready_record(self):
        record = empty_canonical_site_record()
        record["identity"].update(
            {
                "project_key": "CelcomDigi_MW",
                "du_model_name": "MW EOS Swap",
                "du_model_id": "5440935430300168497",
                "view_id": "7476572371505372260",
                "source_file_name": "source.xlsx",
                "source_file_hash": "source-hash",
                "header_hash": "header-hash",
                "source_row_number": 5,
            }
        )
        record["site"].update({"site_code": "A0001", "site_name": "Site A", "du_key": "A0001"})
        record["pr_context"].update(
            {
                "tx_sow_raw": "MW Swap",
                "tx_sow_normalized": "MW Swap",
                "region": "Northern",
                "subcontractor_ti": "GTSB",
                "existing_tss_pr_status": "",
                "existing_ti_pr_status": "",
            }
        )
        required = ["site_code", "tx_sow_raw", "tx_sow_normalized", "region", "subcontractor_ti", "existing_tss_pr_status", "existing_ti_pr_status"]
        record["source_evidence"]["fields"] = {
            field: {"source_header_fingerprint": fingerprint(field), "source_value": record["site"].get(field) or record["pr_context"].get(field), "transformation": "trim"}
            for field in required
        }
        record["validation"].update({"profile_id": "mw_eos_swap_pr_v1", "profile_version": "1.0.0"})
        return record

    def test_complete_record_is_ready(self):
        result = validate_canonical_site_record(self._ready_record(), "TI")
        self.assertEqual(result["classification"], PR_INPUT_READY)

    def test_missing_critical_field_is_incomplete(self):
        record = self._ready_record()
        record["pr_context"]["tx_sow_raw"] = ""
        result = validate_canonical_site_record(record, "TI")
        self.assertEqual(result["classification"], PR_INPUT_INCOMPLETE)
        self.assertIn("MISSING_PR_CRITICAL_FIELD:tx_sow_raw", result["blocking_reasons"])

    def test_ambiguous_mapping_is_quarantined(self):
        record = self._ready_record()
        record["source_evidence"]["ambiguous_fields"] = ["region"]
        result = validate_canonical_site_record(record, "TI")
        self.assertEqual(result["classification"], PR_INPUT_QUARANTINED)
        self.assertIn("AMBIGUOUS_HEADER_MAPPING:region", result["blocking_reasons"])

    def test_draft_profile_and_direct_raw_export_cannot_enable_ecc(self):
        record = self._ready_record()
        draft_profile = {
            "status": "DRAFT",
            "identity": {"accepted_du_models": ["MW EOS Swap"], "accepted_du_model_ids": ["5440935430300168497"], "accepted_view_ids": ["7476572371505372260"]},
            "export_structure": {"approved_header_hashes": []},
        }
        gate = gate_canonical_site_record(record, draft_profile, scope="TI", dry_run=True)
        self.assertFalse(gate["allow_ecc_generation"])
        self.assertEqual(gate["classification"], PR_INPUT_QUARANTINED)
        self.assertEqual(gate_raw_iepms_export()["blocking_reasons"], ["RAW_IEPMS_EXPORT_DIRECT_ECC_PROHIBITED"])

    def test_changed_header_hash_is_quarantined_even_for_production_profile(self):
        record = self._ready_record()
        production_profile = {
            "status": "PRODUCTION",
            "identity": {"accepted_du_models": ["MW EOS Swap"], "accepted_du_model_ids": ["5440935430300168497"], "accepted_view_ids": ["7476572371505372260"]},
            "export_structure": {"approved_header_hashes": ["another-header-hash"]},
        }
        gate = gate_canonical_site_record(record, production_profile, scope="TI")
        self.assertFalse(gate["allow_ecc_generation"])
        self.assertEqual(gate["classification"], PR_INPUT_QUARANTINED)
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
