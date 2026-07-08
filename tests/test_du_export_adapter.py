import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_site_validator import QUARANTINE_NO_ECC, empty_canonical_site_record
from du_export_adapter import (
    PR_STATUS_EXISTS,
    PR_STATUS_NONE,
    PR_STATUS_NOT_REQUIRED,
    build_canonical_site_record,
    normalize_pr_reference_status,
    resolve_profile_field_mappings,
)
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


class TestPrReferenceStatusTransform(unittest.TestCase):
    """Reference-presence rule approved by JJ on 2026-07-07."""

    def test_non_blank_reference_means_pr_exists(self):
        self.assertEqual(normalize_pr_reference_status("SQ202506180613-GTSB"), PR_STATUS_EXISTS)
        self.assertEqual(normalize_pr_reference_status("  SQ202506160540-GCI  "), PR_STATUS_EXISTS)

    def test_explicit_no_pr_required_marker(self):
        self.assertEqual(
            normalize_pr_reference_status("No PR required-Work at TSS only"), PR_STATUS_NOT_REQUIRED
        )
        self.assertEqual(normalize_pr_reference_status("NO PR REQUIRED"), PR_STATUS_NOT_REQUIRED)

    def test_blank_and_nan_like_mean_no_pr(self):
        self.assertEqual(normalize_pr_reference_status(""), PR_STATUS_NONE)
        self.assertEqual(normalize_pr_reference_status("   "), PR_STATUS_NONE)
        self.assertEqual(normalize_pr_reference_status(None), PR_STATUS_NONE)
        self.assertEqual(normalize_pr_reference_status("nan"), PR_STATUS_NONE)

    def test_transform_is_applied_through_profile_mapping_with_provenance(self):
        status_fp = fp("SUBCON_PR_TSS")
        profile = {
            "profile_id": "test_profile",
            "profile_version": "1.0.0",
            "mapping_version": "test-mapping-v1",
            "identity": {"project_key": "CelcomDigi_MW"},
            "field_mapping": {
                "existing_tss_pr_status": {"transforms": ["normalize_pr_reference_status"]},
            },
        }
        resolved = {
            "existing_tss_pr_status": {"status": "RESOLVED", "matches": [{"fingerprint": status_fp}]},
        }
        values = {fingerprint_key(status_fp): "SQ202506180613-GTSB"}
        record = build_canonical_site_record(
            values,
            profile,
            {"source_file_name": "source.xlsx", "source_file_hash": "hash", "header_hash": "header"},
            scope="TSS",
            resolved_mappings=resolved,
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        evidence = record["source_evidence"]["fields"]["existing_tss_pr_status"]
        self.assertEqual(evidence["source_value"], "SQ202506180613-GTSB")
        self.assertEqual(evidence["transformation"], "normalize_pr_reference_status")
        # The transform never unlocks output by itself.
        self.assertEqual(record["validation"]["output_decision"], QUARANTINE_NO_ECC)

    def test_unknown_transform_still_fails_closed(self):
        profile = {
            "profile_id": "p",
            "profile_version": "1",
            "mapping_version": "m",
            "field_mapping": {"site_code": {"transforms": ["invent_data"]}},
        }
        status_fp = fp("SITE_CODE")
        resolved = {"site_code": {"status": "RESOLVED", "matches": [{"fingerprint": status_fp}]}}
        with self.assertRaises(ValueError):
            build_canonical_site_record(
                {fingerprint_key(status_fp): "A0001"},
                profile,
                {},
                scope="TSS",
                resolved_mappings=resolved,
            )


class TestSowRegistryWiring(unittest.TestCase):
    REGISTRY = {
        "registry_type": "canonical_sow_registry",
        "entries": [
            {"raw_value": "MW Swap", "canonical_sow": "MW SWAP", "classification": "PR_TRIGGER"},
            {"raw_value": "Cancel / Drop", "canonical_sow": "CANCEL / DROP", "classification": "NO_PR_TRIGGER"},
            {"raw_value": "Under NIC", "canonical_sow": "UNDER NIC", "classification": "REVIEW_REQUIRED"},
        ],
    }

    def _record_for(self, raw_sow, registry=None):
        sow_fp = fp("TX_SOW")
        profile = {
            "profile_id": "p",
            "profile_version": "1",
            "mapping_version": "m",
            "field_mapping": {"tx_sow_raw": {"transforms": ["trim"]}},
        }
        resolved = {"tx_sow_raw": {"status": "RESOLVED", "matches": [{"fingerprint": sow_fp, "mapping_status": "APPROVED"}]}}
        return build_canonical_site_record(
            {fingerprint_key(sow_fp): raw_sow},
            profile,
            {"source_file_name": "s.xlsx", "source_file_hash": "h", "header_hash": "hh"},
            scope="TSS",
            resolved_mappings=resolved,
            sow_registry=registry,
        )

    def test_pr_trigger_value_normalizes_with_approved_status(self):
        record = self._record_for(" mw   swap ", self.REGISTRY)
        self.assertEqual(record["pr_context"]["tx_sow_normalized"], "MW SWAP")
        evidence = record["source_evidence"]["fields"]["tx_sow_normalized"]
        self.assertEqual(evidence["normalization_status"], "APPROVED")
        self.assertEqual(evidence["sow_classification"], "PR_TRIGGER")
        self.assertEqual(evidence["transformation"], "canonical_sow_registry")

    def test_no_pr_trigger_value_marks_intentional_no_output(self):
        record = self._record_for("Cancel / Drop", self.REGISTRY)
        evidence = record["source_evidence"]["fields"]["tx_sow_normalized"]
        self.assertEqual(evidence["normalization_status"], "APPROVED_NO_OUTPUT")
        self.assertEqual(evidence["sow_classification"], "NO_PR_TRIGGER")

    def test_unknown_value_stays_review_required_and_blank(self):
        record = self._record_for("MW Teleportation", self.REGISTRY)
        self.assertEqual(record["pr_context"]["tx_sow_normalized"], "")
        evidence = record["source_evidence"]["fields"]["tx_sow_normalized"]
        self.assertEqual(evidence["normalization_status"], "REVIEW_REQUIRED")

    def test_without_registry_fallback_stays_unverified(self):
        record = self._record_for("MW Swap", None)
        self.assertEqual(record["pr_context"]["tx_sow_normalized"], "MW Swap")
        evidence = record["source_evidence"]["fields"]["tx_sow_normalized"]
        self.assertEqual(evidence["normalization_status"], "UNVERIFIED")


class TestSubcontractorTssSchemaExtension(unittest.TestCase):
    def test_canonical_record_carries_optional_subcontractor_tss(self):
        record = empty_canonical_site_record()
        self.assertIn("subcontractor_tss", record["pr_context"])
        self.assertEqual(record["pr_context"]["subcontractor_tss"], "")

    def test_subcontractor_tss_maps_through_adapter_with_provenance(self):
        tss_fp = fp("SUBCON_TSS_TEAM")
        profile = {
            "profile_id": "test_profile",
            "profile_version": "1.0.0",
            "mapping_version": "test-mapping-v1",
            "field_mapping": {"subcontractor_tss": {"transforms": ["trim"]}},
        }
        resolved = {"subcontractor_tss": {"status": "RESOLVED", "matches": [{"fingerprint": tss_fp}]}}
        record = build_canonical_site_record(
            {fingerprint_key(tss_fp): " GTSB "},
            profile,
            {"source_file_name": "source.xlsx", "source_file_hash": "hash", "header_hash": "header"},
            scope="TSS",
            resolved_mappings=resolved,
        )
        self.assertEqual(record["pr_context"]["subcontractor_tss"], "GTSB")
        evidence = record["source_evidence"]["fields"]["subcontractor_tss"]
        self.assertEqual(evidence["source_value"], " GTSB ")
        # Optional field: its absence elsewhere must not change required-field rules.
        self.assertNotIn(
            "MISSING_PR_CRITICAL_FIELD:subcontractor_tss",
            record["validation"]["blocking_reasons"],
        )


if __name__ == "__main__":
    unittest.main()
