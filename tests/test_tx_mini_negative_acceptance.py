"""Phase 1 negative-test acceptance sweep for the live TX Mini profile.

Covers the plan's Section 8 minimum test matrix against `tx_mini_pr_v1`:
changed header hash, unknown model/view, missing required fields, ambiguous
fingerprints, unverified mappings, unverified normalization, invalid required
values, and the raw-source block. The positive golden-parity scenario is
evidenced separately by scripts/run_tx_mini_golden_parity.py.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import ALLOW_ECC_OUTPUT, QUARANTINE_NO_ECC
from du_export_adapter import build_canonical_site_record, resolve_profile_field_mappings
from du_profile_loader import load_du_profile
from pr_input_guard import block_raw_source, evaluate_record
from profile_du_export import fingerprint_key
from sow_normalization import load_canonical_sow_registry

PROFILE_PATH = ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml"
SOW_REGISTRY = load_canonical_sow_registry(ROOT / "config" / "registries" / "canonical_sow_registry.yaml")

COMPLETE_ROW = {
    "site_code": "A0001",
    "site_name": "Synthetic Site",
    "du_key": "DU0001",
    "tx_sow_raw": "MW Swap",
    "tx_upgrade_scope_raw": "TSS",
    "region": "Northern",
    "state": "Penang",
    "subcontractor_ti": "GTSB",
    "subcontractor_tss": "GTSB",
    "subcontractor_planning": "GTSB",
    "existing_tss_pr_status": "",
    "existing_ti_pr_status": "",
    "latitude": 5.1234,
    "longitude": 100.1234,
    "antenna_size_ne": "0.6",
    "antenna_size_fe": "0.6",
    "tx_sow_details": "detail",
}


def _load_profile():
    return load_du_profile(PROFILE_PATH)


def _inventory_from_profile(profile, duplicate_field=None):
    """Synthetic header inventory whose columns are the profile's own fingerprints."""
    columns = []
    for field, config in profile["field_mapping"].items():
        for candidate in config.get("source_candidates", []):
            column = {
                "fingerprint": candidate["fingerprint"],
                "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
            }
            columns.append(column)
            if field == duplicate_field:
                columns.append(dict(column))
    return {"sheets": [{"sheet_name": "data", "columns": columns}]}


def _raw_values(profile, overrides=None):
    values = dict(COMPLETE_ROW)
    if overrides:
        values.update(overrides)
    raw = {}
    for field, config in profile["field_mapping"].items():
        for candidate in config.get("source_candidates", []):
            if field in values:
                raw[fingerprint_key(candidate["fingerprint"])] = values[field]
    return raw


def _context(profile, header_hash=None):
    identity = profile["identity"]
    return {
        "project_key": identity["project_key"],
        "du_model_name": identity["accepted_du_models"][0],
        "du_model_id": identity["accepted_du_model_ids"][0],
        "view_id": identity["accepted_view_ids"][0],
        "source_file_name": "synthetic-acceptance.xlsx",
        "source_file_hash": "synthetic-source-hash",
        "header_hash": header_hash or profile["export_structure"]["approved_header_hashes"][0],
        "source_row_number": 5,
    }


def _build_record(profile, overrides=None, header_hash=None, inventory=None, sow_registry=SOW_REGISTRY):
    inventory = inventory or _inventory_from_profile(profile)
    resolved = resolve_profile_field_mappings(inventory, profile)
    return build_canonical_site_record(
        _raw_values(profile, overrides),
        profile,
        _context(profile, header_hash=header_hash),
        scope="TSS",
        resolved_mappings=resolved,
        sow_registry=sow_registry,
    )


def _production_copy(profile):
    """A promoted-profile simulation: PRODUCTION status and no UNVERIFIED
    candidates left (a real promotion must resolve or drop them, because the
    guard blocks output on any unverified evidence field — see the dedicated
    unverified-mapping test)."""
    clone = json.loads(json.dumps(profile))
    clone["status"] = "PRODUCTION"
    for config in clone["field_mapping"].values():
        config["source_candidates"] = [
            candidate
            for candidate in config.get("source_candidates", [])
            if candidate.get("mapping_status") == "APPROVED"
        ]
    return clone




class TestTxMiniNegativeAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = _load_profile()

    def test_complete_record_is_ready_but_nonproduction_profile_blocks_output(self):
        nonproduction = json.loads(json.dumps(self.profile))
        nonproduction["status"] = "PR_INPUT_READY"
        record = _build_record(nonproduction)
        self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_READY")
        gate = evaluate_record(record, nonproduction, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])
        self.assertEqual(gate["output_decision"], QUARANTINE_NO_ECC)

    def test_positive_control_requires_production_and_approved_normalization(self):
        production = _production_copy(self.profile)
        record = _build_record(production)
        # The registry normalizes the PR_TRIGGER value with APPROVED status.
        self.assertEqual(record["pr_context"]["tx_sow_normalized"], "MW SWAP")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertTrue(gate["allow_output"])
        self.assertEqual(gate["output_decision"], ALLOW_ECC_OUTPUT)

    def test_changed_header_hash_quarantines_even_for_production(self):
        production = _production_copy(self.profile)
        record = _build_record(production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])

    def test_unknown_du_model_or_view_quarantines(self):
        production = _production_copy(self.profile)
        record = _build_record(production)
        record["identity"]["view_id"] = "9999999999999999999"
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("UNKNOWN_DU_MODEL_OR_VIEW", gate["blocking_reasons"])

    def test_unknown_profile_quarantines(self):
        record = _build_record(self.profile)
        gate = evaluate_record(record, None, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("UNKNOWN_DU_PROFILE", gate["blocking_reasons"])

    def test_missing_required_field_is_incomplete_and_blocked(self):
        record = _build_record(self.profile, overrides={"tx_sow_raw": ""})
        self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_INCOMPLETE")
        self.assertIn("MISSING_PR_CRITICAL_FIELD:tx_sow_raw", record["validation"]["blocking_reasons"])
        self.assertEqual(record["validation"]["output_decision"], QUARANTINE_NO_ECC)

    def test_blank_required_site_code_is_invalid_and_blocked(self):
        record = _build_record(self.profile, overrides={"site_code": "   "})
        self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_INCOMPLETE")
        self.assertIn("MISSING_PR_CRITICAL_FIELD:site_code", record["validation"]["blocking_reasons"])

    def test_ambiguous_source_fingerprint_quarantines(self):
        inventory = _inventory_from_profile(self.profile, duplicate_field="tx_sow_raw")
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "AMBIGUOUS")
        record = build_canonical_site_record(
            _raw_values(self.profile),
            self.profile,
            _context(self.profile),
            scope="TSS",
            resolved_mappings=resolved,
        )
        self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_QUARANTINED")
        self.assertIn("AMBIGUOUS_HEADER_MAPPING:tx_sow_raw", record["validation"]["blocking_reasons"])

    def test_unverified_source_mapping_blocks_output_for_production(self):
        production = _production_copy(self.profile)
        record = _build_record(production)
        record["source_evidence"]["fields"]["region"]["mapping_status"] = "UNVERIFIED"
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("UNVERIFIED_SOURCE_MAPPING:region", gate["blocking_reasons"])

    def test_unverified_normalization_blocks_output_for_production(self):
        production = _production_copy(self.profile)
        # No registry supplied: the adapter fallback leaves normalization UNVERIFIED.
        record = _build_record(production, sow_registry=None)
        self.assertEqual(
            record["source_evidence"]["fields"]["tx_sow_normalized"]["normalization_status"], "UNVERIFIED"
        )
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("UNVERIFIED_NORMALIZATION:tx_sow_normalized", gate["blocking_reasons"])

    def test_no_pr_trigger_sow_is_intentionally_blocked_for_production(self):
        production = _production_copy(self.profile)
        record = _build_record(production, overrides={"tx_sow_raw": "Cancel / Drop"})
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("SOW_NO_PR_TRIGGER:tx_sow_normalized", gate["blocking_reasons"])

    def test_review_required_sow_blocks_output_for_production(self):
        production = _production_copy(self.profile)
        record = _build_record(production, overrides={"tx_sow_raw": "MW Remote Upgrade"})
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("SOW_NORMALIZATION_REVIEW_REQUIRED:tx_sow_normalized", gate["blocking_reasons"])

    def test_raw_source_export_cannot_reach_ecc(self):
        gate = block_raw_source("any raw export payload")
        self.assertFalse(gate["allow_output"])
        self.assertEqual(gate["output_decision"], QUARANTINE_NO_ECC)
        self.assertIn("RAW_SOURCE_BLOCKED", gate["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
