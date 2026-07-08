import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import (
    ALLOW_ECC_OUTPUT,
    PR_INPUT_INCOMPLETE,
    PR_INPUT_QUARANTINED,
    PR_INPUT_READY,
    QUARANTINE_NO_ECC,
    empty_canonical_site_record,
    validate_canonical_site_record,
)
from pr_input_guard import block_raw_source, evaluate_record


def fingerprint(name):
    return {"field_code": name, "wbs_stage": "WBS", "task_name": "Task", "display_header": name}


class TestCanonicalSiteValidator(unittest.TestCase):
    def _record(self):
        record = empty_canonical_site_record()
        record["identity"].update({"project_key": "CelcomDigi_MW", "du_model_name": "MW EOS Swap", "du_model_id": "5440935430300168497", "view_id": "7476572371505372260", "source_file_name": "source.xlsx", "source_file_hash": "source-hash", "header_hash": "header-hash", "source_row_number": 5})
        record["site"].update({"site_code": "A0001", "site_name": "Site A", "du_key": "A0001"})
        record["pr_context"].update({"tx_sow_raw": "MW Swap", "tx_sow_normalized": "MW Swap", "region": "Northern", "subcontractor_ti": "GTSB", "existing_tss_pr_status": "", "existing_ti_pr_status": ""})
        required = ["site_code", "tx_sow_raw", "tx_sow_normalized", "region", "subcontractor_ti", "existing_tss_pr_status", "existing_ti_pr_status"]
        record["source_evidence"]["fields"] = {field: {"source_header_fingerprint": fingerprint(field), "source_value": record["site"].get(field) or record["pr_context"].get(field), "transformation": "trim"} for field in required}
        record["validation"].update({"profile_id": "mw_eos_swap_pr_v1", "profile_version": "1.0.0", "mapping_version": "test-mapping-v1"})
        return record

    def _profile(self, hashes=None, status="PRODUCTION"):
        return {"status": status, "identity": {"accepted_du_models": ["MW EOS Swap"], "accepted_du_model_ids": ["5440935430300168497"], "accepted_view_ids": ["7476572371505372260"]}, "export_structure": {"approved_header_hashes": hashes or ["header-hash"]}}

    def test_complete_record_is_ready(self):
        self.assertEqual(validate_canonical_site_record(self._record(), "TI")["classification"], PR_INPUT_READY)

    def test_missing_critical_field_is_incomplete(self):
        record = self._record()
        record["pr_context"]["tx_sow_raw"] = ""
        result = validate_canonical_site_record(record, "TI")
        self.assertEqual(result["classification"], PR_INPUT_INCOMPLETE)
        self.assertIn("MISSING_PR_CRITICAL_FIELD:tx_sow_raw", result["blocking_reasons"])

    def test_ambiguous_mapping_is_quarantined(self):
        record = self._record()
        record["source_evidence"]["ambiguous_fields"] = ["region"]
        result = validate_canonical_site_record(record, "TI")
        self.assertEqual(result["classification"], PR_INPUT_QUARANTINED)
        self.assertIn("AMBIGUOUS_HEADER_MAPPING:region", result["blocking_reasons"])

    def test_draft_and_raw_source_are_blocked(self):
        gate = evaluate_record(self._record(), self._profile(status="DRAFT"), scope="TI", dry_run=True)
        self.assertFalse(gate["allow_output"])
        self.assertEqual(gate["classification"], PR_INPUT_QUARANTINED)
        self.assertEqual(gate["output_decision"], QUARANTINE_NO_ECC)
        self.assertEqual(gate["record"]["validation"]["output_decision"], QUARANTINE_NO_ECC)
        self.assertFalse(block_raw_source()["allow_output"])
        self.assertEqual(block_raw_source()["output_decision"], QUARANTINE_NO_ECC)

    def test_changed_header_hash_is_quarantined(self):
        gate = evaluate_record(self._record(), self._profile(hashes=["another-header-hash"]), scope="TI")
        self.assertFalse(gate["allow_output"])
        self.assertEqual(gate["classification"], PR_INPUT_QUARANTINED)
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])
        self.assertEqual(gate["record"]["validation"]["output_decision"], QUARANTINE_NO_ECC)

    def test_unverified_normalization_is_quarantined(self):
        record = self._record()
        record["source_evidence"]["fields"]["tx_sow_normalized"]["normalization_status"] = "UNVERIFIED"
        gate = evaluate_record(record, self._profile(), scope="TI")
        self.assertFalse(gate["allow_output"])
        self.assertIn("UNVERIFIED_NORMALIZATION:tx_sow_normalized", gate["blocking_reasons"])
        self.assertEqual(gate["output_decision"], QUARANTINE_NO_ECC)

    def test_missing_mapping_version_is_incomplete(self):
        record = self._record()
        record["validation"]["mapping_version"] = ""
        result = validate_canonical_site_record(record, "TI")
        self.assertEqual(result["classification"], PR_INPUT_INCOMPLETE)
        self.assertIn("MISSING_MAPPING_VERSION", result["blocking_reasons"])

    def test_ready_production_gate_records_allow_output_decision(self):
        gate = evaluate_record(self._record(), self._profile(), scope="TI")
        self.assertTrue(gate["allow_output"])
        self.assertEqual(gate["classification"], PR_INPUT_READY)
        self.assertEqual(gate["output_decision"], ALLOW_ECC_OUTPUT)
        self.assertEqual(gate["record"]["validation"]["output_decision"], ALLOW_ECC_OUTPUT)


if __name__ == "__main__":
    unittest.main()
