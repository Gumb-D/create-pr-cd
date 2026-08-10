import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import PR_INPUT_READY, validate_canonical_site_record


PROFILE_ID = "jendela_tx_migration_pr_v1"
PROFILE_PATH = ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"


class TestIssue77JendelaProfileValidation(unittest.TestCase):
    def test_profile_keeps_final_backhaul_optional(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertFalse(profile["field_mapping"]["final_backhaul"]["required"])
        self.assertEqual(profile["identity"]["accepted_du_models"], ["Jendela TX Migration"])

    def _record(self, *, final_backhaul=""):
        evidence = {
            "site_code": {"source_header_fingerprint": {"field_code": "site"}},
            "tx_sow_raw": {"source_header_fingerprint": {"field_code": "tx-sow"}},
            "region": {"source_header_fingerprint": {"field_code": "region"}},
            "subcontractor_ti": {"source_header_fingerprint": {"field_code": "subcon"}},
            "existing_ti_pr_status": {"source_header_fingerprint": {"field_code": "existing-pr"}},
            "tx_before_migration": {"source_header_fingerprint": {"field_code": "before"}},
        }
        return {
            "identity": {"header_hash": "header", "source_file_hash": "source"},
            "site": {"site_code": "SITE-1", "site_name": "", "du_key": ""},
            "pr_context": {
                "tx_sow_raw": "",
                "tx_sow_normalized": "",
                "tx_upgrade_scope_raw": "",
                "tx_before_migration": "Fiber Own Build",
                "final_backhaul": final_backhaul,
                "region": "Southern",
                "state": "Johor",
                "subcontractor_ti": "GTSB",
                "subcontractor_tss": "",
                "subcontractor_planning": "",
                "existing_tss_pr_status": "",
                "existing_ti_pr_status": "NO_PR",
                "migration_decision": {
                    "classification": "APPROVED",
                    "reason_code": "JENDELA_TI_WORK_PLAN_APPROVED",
                    "decision_code": "JENDELA_TI_WORK_PLAN",
                    "source_values": {},
                    "work_items": [],
                },
            },
            "technical_context": {
                "latitude": None,
                "longitude": None,
                "antenna_size_ne": "",
                "antenna_size_fe": "",
                "boq_configuration": "",
                "tx_sow_details": "",
                "ne_sow_details": "",
                "fe_sow_details": "",
            },
            "source_evidence": {"fields": evidence, "ambiguous_fields": []},
            "validation": {
                "profile_id": PROFILE_ID,
                "profile_version": "0.5.0",
                "mapping_version": "issue-77",
                "warnings": [],
            },
        }

    def test_blank_final_backhaul_does_not_block_ready_state(self):
        result = validate_canonical_site_record(self._record(final_backhaul=""), "TI")
        self.assertEqual(result["classification"], PR_INPUT_READY, result)
        self.assertFalse(any("final_backhaul" in reason for reason in result["blocking_reasons"]))

    def test_changing_final_backhaul_does_not_change_validation(self):
        blank = validate_canonical_site_record(self._record(final_backhaul=""), "TI")
        unexpected = validate_canonical_site_record(self._record(final_backhaul="anything"), "TI")
        self.assertEqual(blank, unexpected)


if __name__ == "__main__":
    unittest.main()
