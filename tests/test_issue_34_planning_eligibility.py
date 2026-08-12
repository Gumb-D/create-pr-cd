#!/usr/bin/env python3
"""Planning eligibility and duplicate-prevention regression tests for Issue #34."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from create_pr import _partition_records, _scope_subcontractor  # noqa: E402
from du_export_adapter import PR_STATUS_EXISTS, PR_STATUS_NONE, PR_STATUS_NOT_REQUIRED  # noqa: E402

EMPTY_POLICY = {"schema_version": "1.0", "excluded_from_pr": {}}


def _record(
    subcontractor: str,
    status: str = PR_STATUS_NONE,
    *,
    du_model: str = "2024 Celcomdigi BAU",
) -> dict:
    return {
        "identity": {"du_model_name": du_model, "source_row_number": 5},
        "site": {"site_code": "A0001"},
        "pr_context": {
            "region": "Central",
            "subcontractor_planning": subcontractor,
            "existing_planning_pr_status": status,
            "tx_sow_raw": "SHOULD NOT MATTER",
            "tx_sow_normalized": "",
        },
        "source_evidence": {"fields": {}},
        "validation": {
            "profile_id": "celcomdigi_bau_2024_pr_v1",
            "pr_input_classification": "PR_INPUT_READY",
            "blocking_reasons": [],
        },
    }


class PlanningEligibilityTest(unittest.TestCase):
    def test_scope_subcontractor_uses_planning_field(self):
        record = _record("GCI_AA")
        self.assertEqual(_scope_subcontractor(record, "Planning"), "GCI_AA")

    def test_blank_planning_subcontractor_is_ignored(self):
        partitions = _partition_records([_record("")], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["ignored"]), 1)
        self.assertEqual(len(partitions["candidates"]), 0)

    def test_standard_planning_candidate_gets_resolved_selection(self):
        record = _record("GCI")
        partitions = _partition_records([record], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["candidates"]), 1)
        selection = partitions["candidates"][0]["planning_selection"]
        self.assertEqual(selection["pbom_code"], "350001143904")
        self.assertEqual(selection["contract_subcontractor"], "GCI")

    def test_aa_candidate_gets_only_aa_selection_and_base_contract_identity(self):
        record = _record("GTSB_AA", du_model="MW EOS Swap")
        partitions = _partition_records([record], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["candidates"]), 1)
        selection = partitions["candidates"][0]["planning_selection"]
        self.assertEqual(selection["pbom_code"], "350001042321")
        self.assertEqual(selection["contract_subcontractor"], "GTSB")

    def test_existing_planning_pr_is_duplicate_blocked(self):
        partitions = _partition_records([_record("GCI", PR_STATUS_EXISTS)], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["duplicates"]), 1)
        self.assertEqual(len(partitions["candidates"]), 0)

    def test_no_pr_required_marker_is_ignored(self):
        partitions = _partition_records([_record("GCI", PR_STATUS_NOT_REQUIRED)], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["ignored"]), 1)
        self.assertEqual(len(partitions["candidates"]), 0)

    def test_unknown_planning_subcontractor_fails_closed(self):
        partitions = _partition_records([_record("UNKNOWN_VENDOR")], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["review_required"]), 1)
        self.assertEqual(len(partitions["candidates"]), 0)
        decision = partitions["review_required"][0]["pr_generation_decision"]
        self.assertEqual(decision["reason_code"], "PLANNING_SUBCONTRACTOR_NOT_APPROVED")

    def test_planning_does_not_require_tx_sow_normalization(self):
        record = _record("GCI")
        record["pr_context"]["tx_sow_raw"] = ""
        record["pr_context"]["tx_sow_normalized"] = ""
        partitions = _partition_records([record], "Planning", EMPTY_POLICY)
        self.assertEqual(len(partitions["candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
