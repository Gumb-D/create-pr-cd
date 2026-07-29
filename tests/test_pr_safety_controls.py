import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import create_pr
from pr_safety_controls import (
    CONTRACT_MISSING_ACTION,
    CONTRACT_MISSING_REASON_CODE,
    EXCLUDED_REASON_CODE,
    SafetyControlError,
    get_exclusion_rule,
    load_contract_reference,
    load_subcontractor_policy,
    normalize_subcontractor,
    validate_candidate_contracts,
)


POLICY_PATH = ROOT / "config" / "subcontractor_pr_policy.json"
CONTRACT_PATH = ROOT / "Info" / "input" / "contract_info_reference.md"


def canonical_record(site: str, subcontractor: str, scope: str = "TSS") -> dict:
    context = {
        "region": "Central",
        "tx_sow_normalized": "MW NEW LINK",
        "subcontractor_tss": subcontractor if scope == "TSS" else "GTSB",
        "subcontractor_ti": subcontractor if scope == "TI" else "GTSB",
        "existing_tss_pr_status": "NO_PR",
        "existing_ti_pr_status": "NO_PR",
    }
    return {
        "identity": {"source_row_number": 10},
        "site": {"site_code": site, "site_name": f"Site {site}", "du_key": f"DU-{site}"},
        "pr_context": context,
        "technical_context": {},
        "source_evidence": {
            "fields": {"tx_sow_normalized": {"normalization_status": "APPROVED"}}
        },
        "validation": {
            "profile_id": "test_profile",
            "pr_input_classification": "PR_INPUT_READY",
            "blocking_reasons": [],
        },
    }


class TestPrSafetyControls(unittest.TestCase):
    def test_normalize_subcontractor_is_trimmed_case_insensitive_and_deterministic(self):
        self.assertEqual(normalize_subcontractor(" SM "), "SM")
        self.assertEqual(normalize_subcontractor("sm"), "SM")
        self.assertEqual(normalize_subcontractor("NR   Services"), "NR SERVICES")

    def test_policy_excludes_sm_for_tss_and_ti_only(self):
        policy = load_subcontractor_policy(POLICY_PATH)
        self.assertEqual(get_exclusion_rule(policy, "SM", "TSS")["reason_code"], EXCLUDED_REASON_CODE)
        self.assertEqual(get_exclusion_rule(policy, " sm ", "TI")["classification"], "IGNORED")
        self.assertIsNone(get_exclusion_rule(policy, "GTSB", "TSS"))

    def test_partition_ignores_sm_before_other_checks_for_both_scopes(self):
        policy = load_subcontractor_policy(POLICY_PATH)
        for scope, raw_name in (("TSS", " SM "), ("TI", "sm")):
            with self.subTest(scope=scope):
                record = canonical_record(f"{scope}-SM", raw_name, scope)
                partitions = create_pr._partition_records([record], scope, policy)
                self.assertEqual(partitions["candidates"], [])
                self.assertEqual(partitions["review_required"], [])
                self.assertEqual(partitions["ignored"], [record])
                self.assertEqual(
                    record["pr_generation_decision"]["reason_code"],
                    EXCLUDED_REASON_CODE,
                )

    def test_unconfigured_subcontractor_is_not_auto_ignored(self):
        policy = load_subcontractor_policy(POLICY_PATH)
        record = canonical_record("UNKNOWN-1", "Unconfigured Vendor", "TSS")
        partitions = create_pr._partition_records([record], "TSS", policy)
        self.assertEqual(partitions["candidates"], [record])
        self.assertEqual(partitions["ignored"], [])

    def test_missing_policy_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(SafetyControlError) as context:
                load_subcontractor_policy(Path(temp_dir) / "missing.json")
        self.assertEqual(context.exception.code, "SUBCONTRACTOR_POLICY_NOT_FOUND")

    def test_malformed_policy_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "policy.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(SafetyControlError) as context:
                load_subcontractor_policy(path)
        self.assertEqual(context.exception.code, "SUBCONTRACTOR_POLICY_INVALID")

    def test_contract_reference_contains_approved_new_and_existing_mappings(self):
        mappings = load_contract_reference(CONTRACT_PATH)
        self.assertEqual(mappings["NERA"]["contract_number"], "S1MY2023083002WBF1")
        self.assertEqual(mappings["PERWIRA"]["contract_number"], "S1MY2023062002WBF1")
        self.assertEqual(mappings["CCSMY"]["contract_number"], "S1MY2024071004WBF1")

    def test_contract_reference_rejects_placeholder_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "contracts.md"
            path.write_text(
                "## Subcontractor to Contract Number\n\n"
                "| Subcontractor* | Contract Number * | Company Full Name |\n"
                "|---|---|---|\n"
                "| Unsafe | UNKNOWN | Unsafe |\n",
                encoding="utf-8",
            )
            with self.assertRaises(SafetyControlError) as context:
                load_contract_reference(path)
        self.assertEqual(context.exception.code, "CONTRACT_REFERENCE_INVALID")

    def test_missing_contract_moves_candidate_to_review_required(self):
        record = canonical_record("MISSING-1", "Unconfigured Vendor", "TSS")
        valid, missing = validate_candidate_contracts([record], "TSS", load_contract_reference(CONTRACT_PATH))
        self.assertEqual(valid, [])
        self.assertEqual(missing, [record])
        decision = record["pr_generation_decision"]
        self.assertEqual(decision["classification"], "REVIEW_REQUIRED")
        self.assertEqual(decision["reason_code"], CONTRACT_MISSING_REASON_CODE)
        self.assertEqual(decision["required_action"], CONTRACT_MISSING_ACTION)

    def test_approved_contract_is_attached_and_canonicalizes_renderer_subcontractor(self):
        record = canonical_record("NERA-1", " nera ", "TSS")
        valid, missing = validate_candidate_contracts([record], "TSS", load_contract_reference(CONTRACT_PATH))
        self.assertEqual(missing, [])
        self.assertEqual(valid, [record])
        self.assertEqual(record["approved_contract"]["contract_number"], "S1MY2023083002WBF1")
        self.assertEqual(record["approved_contract"]["scope"], "TSS")
        renderer_row = create_pr._renderer_row(record)
        self.assertEqual(renderer_row["SubCon - TSS Team"], "Nera")

    def test_sm_is_not_counted_as_contract_mapping_missing(self):
        policy = load_subcontractor_policy(POLICY_PATH)
        sm_record = canonical_record("SM-1", "SM", "TI")
        missing_record = canonical_record("MISS-1", "Unknown Vendor", "TI")
        partitions = create_pr._partition_records([sm_record, missing_record], "TI", policy)
        valid, missing = validate_candidate_contracts(
            partitions["candidates"],
            "TI",
            load_contract_reference(CONTRACT_PATH),
        )
        self.assertEqual(valid, [])
        self.assertEqual(missing, [missing_record])
        self.assertEqual(partitions["ignored"], [sm_record])

    def test_contract_review_report_contains_required_business_fields(self):
        record = canonical_record("MISS-2", "Unknown Vendor", "TSS")
        _, missing = validate_candidate_contracts([record], "TSS", load_contract_reference(CONTRACT_PATH))
        with tempfile.TemporaryDirectory() as temp_dir:
            path = create_pr._write_contract_review_report(
                Path(temp_dir),
                "TSS",
                missing,
                create_pr.RUN_MODE_NON_PRODUCTION_UAT,
            )
            self.assertIsNotNone(path)
            text = path.read_text(encoding="utf-8-sig")
        for header in create_pr.CONTRACT_REVIEW_FIELDS:
            self.assertIn(header, text)
        self.assertIn(CONTRACT_MISSING_REASON_CODE, text)
        self.assertIn(CONTRACT_MISSING_ACTION, text)


if __name__ == "__main__":
    unittest.main()
