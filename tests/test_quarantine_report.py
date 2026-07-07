import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import empty_canonical_site_record
from quarantine_report import (
    SKILL_RELATED_FIELDS,
    build_quarantine_entry,
    build_quarantine_report,
    quarantine_report_markdown,
    validate_quarantine_report,
)


def fingerprint(name):
    return {"field_code": name, "wbs_stage": "WBS", "task_name": "Task", "display_header": name}


class TestQuarantineReport(unittest.TestCase):
    def _record(self):
        record = empty_canonical_site_record()
        record["identity"].update(
            {
                "project_key": "CelcomDigi_MW",
                "project_id": "P-1",
                "du_model_name": "MW EOS Swap",
                "du_model_id": "5440935430300168497",
                "view_id": "7476572371505372260",
                "source_file_name": "source.xlsx",
                "source_file_hash": "source-hash",
                "header_hash": "header-hash",
                "source_row_number": 7,
            }
        )
        record["site"].update({"site_code": "A0001", "site_name": "Site A", "du_key": "DU-A0001"})
        record["pr_context"].update(
            {
                "region": "Northern",
                "tx_sow_raw": "MW Swap",
                "subcontractor_ti": "GTSB",
                "existing_ti_pr_status": "",
            }
        )
        record["technical_context"].update({"antenna_size_ne": "1.2m", "antenna_size_fe": "1.8m"})
        record["source_evidence"]["fields"] = {
            "site_code": {
                "source_header_fingerprint": fingerprint("site_code"),
                "source_value": "A0001",
                "transformation": "trim",
                "mapping_status": "UNVERIFIED",
            },
            "tx_sow_raw": {
                "source_header_fingerprint": fingerprint("tx_sow_raw"),
                "source_value": "MW Swap",
                "transformation": "none",
                "mapping_status": "UNVERIFIED",
            },
            "tx_sow_normalized": {
                "source_header_fingerprint": fingerprint("tx_sow_raw"),
                "source_value": "MW Swap",
                "transformation": "trim",
                "mapping_status": "UNVERIFIED",
                "normalization_status": "UNVERIFIED",
            },
        }
        record["validation"].update(
            {
                "profile_id": "mw_eos_swap_pr_v1",
                "profile_version": "1.0.0",
                "mapping_version": "discovery-2026-07-06-mw-eos-swap-v1",
                "pr_input_classification": "PR_INPUT_QUARANTINED",
                "blocking_reasons": ["DU_PROFILE_NOT_PRODUCTION", "UNVERIFIED_NORMALIZATION:tx_sow_normalized"],
                "warnings": ["Dry-run only"],
            }
        )
        return record

    def test_entry_limits_field_review_to_skill_related_fields(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        reviewed_fields = [item["canonical_field"] for item in entry["skill_field_review"]]
        self.assertEqual(reviewed_fields, list(SKILL_RELATED_FIELDS))
        self.assertNotIn("latitude", reviewed_fields)
        self.assertEqual(entry["validation_audit"]["output_decision"], "QUARANTINE_NO_ECC")

    def test_entry_carries_identity_profile_and_reasons(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        self.assertEqual(entry["source_export_identity"]["du_model_name"], "MW EOS Swap")
        self.assertEqual(entry["du_profile"]["profile_id"], "mw_eos_swap_pr_v1")
        self.assertEqual(entry["du_profile"]["mapping_version"], "discovery-2026-07-06-mw-eos-swap-v1")
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", entry["validation_audit"]["blocking_reasons"])

    def test_report_markdown_mentions_decision_and_reasons(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        report = build_quarantine_report([entry])
        markdown = quarantine_report_markdown(report)
        self.assertIn("canonical_pr_input_quarantine_review", str(report["report_type"]))
        self.assertIn("QUARANTINE_NO_ECC", markdown)
        self.assertIn("UNVERIFIED_NORMALIZATION:tx_sow_normalized", markdown)
        self.assertIn("discovery-2026-07-06-mw-eos-swap-v1", markdown)
        self.assertIn("site_code", markdown)

    def test_validation_fails_when_decision_counts_drift(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        report = build_quarantine_report([entry])
        report["decision_counts"]["QUARANTINE_NO_ECC"] = 99

        with self.assertRaises(ValueError) as error:
            validate_quarantine_report(report)

        self.assertIn("decision_counts", str(error.exception))

    def test_validation_fails_when_allow_output_disagrees_with_decision(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        entry["validation_audit"]["allow_output"] = True
        report = {
            "report_type": "canonical_pr_input_quarantine_review",
            "entry_count": 1,
            "decision_counts": {"QUARANTINE_NO_ECC": 1},
            "entries": [entry],
        }

        with self.assertRaises(ValueError) as error:
            validate_quarantine_report(report)

        self.assertIn("allow_output", str(error.exception))

    def test_validation_fails_when_skill_field_review_drops_expected_field(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        entry["skill_field_review"] = entry["skill_field_review"][:-1]
        report = {
            "report_type": "canonical_pr_input_quarantine_review",
            "entry_count": 1,
            "decision_counts": {"QUARANTINE_NO_ECC": 1},
            "entries": [entry],
        }

        with self.assertRaises(ValueError) as error:
            validate_quarantine_report(report)

        self.assertIn("skill_field_review", str(error.exception))

    def test_build_report_fails_closed_when_entry_is_internally_inconsistent(self):
        entry = build_quarantine_entry(self._record(), scope="TI", profile_status="DRAFT")
        entry["validation_audit"]["allow_output"] = True

        with self.assertRaises(ValueError) as error:
            build_quarantine_report([entry])

        self.assertIn("allow_output", str(error.exception))


if __name__ == "__main__":
    unittest.main()
