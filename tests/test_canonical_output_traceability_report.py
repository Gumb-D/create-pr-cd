import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import ALLOW_ECC_OUTPUT, PR_INPUT_QUARANTINED, PR_INPUT_READY, QUARANTINE_NO_ECC, empty_canonical_site_record
from canonical_output_traceability_report import (
    TRACEABILITY_REVIEW_REQUIRED,
    TRACEABLE,
    build_output_traceability_entry,
    build_output_traceability_report,
    output_traceability_markdown,
    validate_output_traceability_report,
)


class TestCanonicalOutputTraceabilityReport(unittest.TestCase):
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
        record["validation"].update(
            {
                "profile_id": "mw_eos_swap_pr_v1",
                "profile_version": "1.0.0",
                "mapping_version": "approved-mapping-v1",
                "pr_input_classification": PR_INPUT_READY,
                "blocking_reasons": [],
                "warnings": [],
                "output_decision": ALLOW_ECC_OUTPUT,
            }
        )
        return record

    def test_entry_marks_traceable_when_profile_and_header_fields_exist(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        self.assertEqual(entry["traceability_status"], TRACEABLE)
        self.assertEqual(entry["du_profile"]["profile_version"], "1.0.0")
        self.assertEqual(entry["source_export_identity"]["header_hash"], "header-hash")
        self.assertEqual(entry["validation_audit"]["output_decision"], ALLOW_ECC_OUTPUT)
        self.assertEqual(entry["traceability_gaps"], [])

    def test_entry_flags_missing_header_hash_for_review(self):
        record = self._record()
        record["identity"]["header_hash"] = ""
        record["validation"]["pr_input_classification"] = PR_INPUT_QUARANTINED
        record["validation"]["output_decision"] = QUARANTINE_NO_ECC
        entry = build_output_traceability_entry(record, scope="TI", profile_status="DRAFT")
        self.assertEqual(entry["traceability_status"], TRACEABILITY_REVIEW_REQUIRED)
        self.assertIn("MISSING_HEADER_HASH", entry["traceability_gaps"])
        self.assertEqual(entry["validation_audit"]["output_decision"], QUARANTINE_NO_ECC)

    def test_report_markdown_mentions_traceability_status_and_decision(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        report = build_output_traceability_report([entry])
        markdown = output_traceability_markdown(report)
        self.assertEqual(report["report_type"], "canonical_pr_output_traceability_review")
        self.assertIn("TRACEABLE", markdown)
        self.assertIn("ALLOW_ECC_OUTPUT", markdown)
        self.assertIn("approved-mapping-v1", markdown)

    def test_validation_fails_when_summary_counts_drift(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        report = build_output_traceability_report([entry])
        report["traceability_counts"]["TRACEABLE"] = 99

        with self.assertRaises(ValueError) as error:
            validate_output_traceability_report(report)

        self.assertIn("traceability_counts", str(error.exception))

    def test_validation_fails_when_entry_status_disagrees_with_gaps(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        entry["traceability_gaps"] = ["MISSING_HEADER_HASH"]
        report = {
            "report_type": "canonical_pr_output_traceability_review",
            "entry_count": 1,
            "traceability_counts": {"TRACEABLE": 1},
            "entries": [entry],
        }

        with self.assertRaises(ValueError) as error:
            validate_output_traceability_report(report)

        self.assertIn("traceability_gaps", str(error.exception))

    def test_validation_fails_when_traceability_gaps_do_not_match_entry_fields(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        entry["source_export_identity"]["header_hash"] = ""
        entry["traceability_status"] = TRACEABILITY_REVIEW_REQUIRED
        entry["traceability_gaps"] = []
        report = {
            "report_type": "canonical_pr_output_traceability_review",
            "entry_count": 1,
            "traceability_counts": {"TRACEABILITY_REVIEW_REQUIRED": 1},
            "entries": [entry],
        }

        with self.assertRaises(ValueError) as error:
            validate_output_traceability_report(report)

        self.assertIn("traceability_gaps", str(error.exception))

    def test_build_report_fails_closed_when_entry_status_disagrees_with_gaps(self):
        entry = build_output_traceability_entry(self._record(), scope="TI", profile_status="PRODUCTION")
        entry["traceability_gaps"] = ["MISSING_HEADER_HASH"]

        with self.assertRaises(ValueError) as error:
            build_output_traceability_report([entry])

        self.assertIn("traceability_gaps", str(error.exception))


if __name__ == "__main__":
    unittest.main()
