import sys
import unittest
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_generator_bridge import classify_uat_record
from canonical_site_validator import empty_canonical_site_record


class TestScopeActualEndEligibility(unittest.TestCase):
    def make_record(self, *, scope="TI", status="NO_PR", actual_end=None, details="Drop by CD"):
        record = empty_canonical_site_record()
        record["pr_context"].update(
            {
                "tx_sow_raw": "MW New Link / Reroute",
                "tx_sow_normalized": "MW NEW LINK / REROUTE",
                "region": "Central",
                "subcontractor_tss": "GTSB",
                "subcontractor_ti": "GTSB",
                "existing_tss_pr_status": status if scope == "TSS" else "NO_PR",
                "existing_ti_pr_status": status if scope == "TI" else "NO_PR",
            }
        )
        record["technical_context"]["tx_sow_details"] = details
        record["validation"].update(
            {
                "profile_id": "zte_tx_mini_pr_v1",
                "profile_version": "0.2.0",
                "mapping_version": "approved-v1",
                "pr_input_classification": "PR_INPUT_READY",
                "blocking_reasons": [],
            }
        )
        record["source_evidence"]["fields"]["tx_sow_normalized"] = {
            "source_header_fingerprint": {
                "field_code": "TX_SOW",
                "wbs_stage": "Network Planning",
                "task_name": "Microwave",
                "display_header": "Microwave Tx SOW",
            },
            "normalization_status": "APPROVED",
            "sow_classification": "PR_TRIGGER",
        }
        date_field = "tss_actual_end_date" if scope == "TSS" else "ti_actual_end_date"
        record["source_evidence"]["fields"][date_field] = {
            "source_header_fingerprint": {
                "field_code": "ACTUAL_END",
                "wbs_stage": "Stage",
                "task_name": "Task",
                "display_header": "actual end time",
            },
            "source_value": actual_end,
            "mapping_status": "APPROVED",
        }
        return record

    def test_missing_scope_actual_end_is_ignored(self):
        classification, reasons = classify_uat_record(self.make_record(actual_end=None), "TI")
        self.assertEqual(classification, "NO_PR_OR_IGNORED")
        self.assertIn("ti_actual_end_date:ACTUAL_END_MISSING", reasons)

    def test_completed_scope_remains_candidate_even_when_details_say_drop_by_cd(self):
        classification, reasons = classify_uat_record(self.make_record(actual_end=datetime.date(2026, 7, 17)), "TI")
        self.assertEqual(classification, "UAT_CANDIDATE")
        self.assertEqual(reasons, [])

    def test_existing_pr_precedes_missing_actual_end(self):
        classification, reasons = classify_uat_record(
            self.make_record(status="PR_EXISTS", actual_end=None),
            "TI",
        )
        self.assertEqual(classification, "DUPLICATE_BLOCKED")
        self.assertIn("existing_ti_pr_status:PR_EXISTS", reasons)

    def test_tss_uses_its_own_actual_end_field(self):
        self.assertEqual(
            classify_uat_record(self.make_record(scope="TSS", actual_end="2026-07-17"), "TSS")[0],
            "UAT_CANDIDATE",
        )
        self.assertEqual(
            classify_uat_record(self.make_record(scope="TSS", actual_end=None), "TSS")[0],
            "NO_PR_OR_IGNORED",
        )

    def test_date_validation_excel_datetime(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end=datetime.datetime(2026, 7, 17, 12, 0)), "TI")[0], "UAT_CANDIDATE")

    def test_date_validation_iso_string(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end="2026-07-17T12:00:00Z"), "TI")[0], "UAT_CANDIDATE")

    def test_date_validation_supported_workbook_date_string(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end="2026/07/17 12:00"), "TI")[0], "UAT_CANDIDATE")
        self.assertEqual(classify_uat_record(self.make_record(actual_end="17-07-2026"), "TI")[0], "UAT_CANDIDATE")

    def test_date_validation_whitespace(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end="   "), "TI")[0], "NO_PR_OR_IGNORED")

    def test_date_validation_invalid_text(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end="N/A"), "TI")[0], "REVIEW_REQUIRED")

    def test_date_validation_invalid_calendar_date(self):
        self.assertEqual(classify_uat_record(self.make_record(actual_end="2026-13-45"), "TI")[0], "REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
