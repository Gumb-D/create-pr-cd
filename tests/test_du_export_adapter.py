import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import QUARANTINE_NO_ECC
from du_export_adapter import build_canonical_site_record, resolve_profile_field_mappings
from profile_du_export import fingerprint_key


def fp(code):
    return {
        "field_code": code,
        "wbs_stage": "WBS",
        "task_name": "Task",
        "display_header": "Display",
    }


class TestDuExportAdapter(unittest.TestCase):
    def test_resolver_requires_exact_four_layer_fingerprint(self):
        site_fp = fp("SITE_CODE")
        other_fp = fp("SITE_CODE")
        other_fp["display_header"] = "Different Display"
        inventory = {
            "sheets": [
                {
                    "sheet_name": "DU Export",
                    "columns": [
                        {"fingerprint": site_fp, "fingerprint_key": fingerprint_key(site_fp)},
                        {"fingerprint": other_fp, "fingerprint_key": fingerprint_key(other_fp)},
                    ],
                }
            ]
        }
        profile = {
            "field_mapping": {
                "site_code": {
                    "source_candidates": [{"fingerprint": site_fp, "mapping_status": "APPROVED"}],
                    "transforms": ["trim", "uppercase"],
                }
            }
        }
        resolved = resolve_profile_field_mappings(inventory, profile)
        self.assertEqual(resolved["site_code"]["status"], "RESOLVED")
        self.assertEqual(resolved["site_code"]["matches"][0]["fingerprint"], site_fp)

    def test_adapter_preserves_source_provenance_and_does_not_generate_ecc(self):
        site_fp = fp("SITE_CODE")
        tx_sow_fp = fp("TX_SOW")
        profile = {
            "profile_id": "test_profile",
            "profile_version": "1.0.0",
            "mapping_version": "test-mapping-v1",
            "identity": {"project_key": "CelcomDigi_MW"},
            "field_mapping": {
                "site_code": {"transforms": ["trim", "uppercase"]},
                "tx_sow_raw": {"transforms": ["trim"]},
            },
        }
        resolved = {
            "site_code": {"status": "RESOLVED", "matches": [{"fingerprint": site_fp}]},
            "tx_sow_raw": {"status": "RESOLVED", "matches": [{"fingerprint": tx_sow_fp}]},
        }
        values = {fingerprint_key(site_fp): " a0001 ", fingerprint_key(tx_sow_fp): " MW Swap "}
        record = build_canonical_site_record(
            values,
            profile,
            {
                "du_model_name": "MW EOS Swap",
                "du_model_id": "5440935430300168497",
                "view_id": "7476572371505372260",
                "source_file_name": "source.xlsx",
                "source_file_hash": "hash",
                "header_hash": "header",
                "source_row_number": 5,
            },
            scope="TI",
            resolved_mappings=resolved,
        )
        self.assertEqual(record["site"]["site_code"], "A0001")
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "MW Swap")
        self.assertEqual(record["source_evidence"]["fields"]["site_code"]["source_value"], " a0001 ")
        self.assertEqual(record["source_evidence"]["fields"]["site_code"]["transformation"], "trim+uppercase")
        self.assertEqual(record["validation"]["mapping_version"], "test-mapping-v1")
        self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_INCOMPLETE")
        self.assertEqual(record["validation"]["output_decision"], QUARANTINE_NO_ECC)


if __name__ == "__main__":
    unittest.main()
