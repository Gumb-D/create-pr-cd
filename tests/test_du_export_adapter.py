import sys
import unittest
from pathlib import Path
import json

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
from du_profile_loader import load_du_profile
from pr_input_guard import evaluate_record
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


class TestTxRolloutApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_rejected=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_rejected:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ0656921",
                    "wbs_stage": "Network Planning",
                    "task_name": "Microwave",
                    "display_header": "Plan TX SOW (HLD)",
                },
                {
                    "field_code": "docata|ZDCSZ00904401",
                    "wbs_stage": "Acceptance",
                    "task_name": "Microwave",
                    "display_header": "PR TSS Status",
                },
                {
                    "field_code": "docata|ZDCSZ00904402",
                    "wbs_stage": "Acceptance",
                    "task_name": "Microwave",
                    "display_header": "PR TI Status",
                },
            ):
                columns.append({"fingerprint": fingerprint, "fingerprint_key": fingerprint_key(fingerprint)})
        return {"sheets": [{"sheet_name": "TX Rollout", "columns": columns}]}

    def _resolved(self, *, include_rejected=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_rejected=include_rejected, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "",
            "tx_upgrade_scope_raw": "Upgrade",
            "region": "Northern",
            "state": "Penang",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "GTSB",
            "existing_tss_pr_status": "",
            "existing_ti_pr_status": "",
            "latitude": "5.1234",
            "longitude": "100.1234",
            "tx_sow_details": "detail",
            "ne_sow_details": "ne detail",
            "fe_sow_details": "fe detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name == "tx_sow_raw":
                tx_candidates = config.get("source_candidates", [])
                candidate_values = {
                    "Post MOCN TX SOW (LLD)": values.get("post_mocn_tx_sow_lld", ""),
                    "TX SOW (LLD)": values.get("tx_sow_lld", ""),
                }
                for candidate in tx_candidates:
                    raw[fingerprint_key(candidate["fingerprint"])] = candidate_values.get(
                        candidate["fingerprint"]["display_header"],
                        "",
                    )
                continue
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-tx-rollout.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_approved_pr_critical_fingerprints(self):
        resolved = self._resolved(include_rejected=True)
        for field_name in (
            "site_code",
            "region",
            "subcontractor_ti",
            "tx_sow_raw",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        ):
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Post MOCN TX SOW (LLD)", "TX SOW (LLD)"],
        )
        self.assertNotIn(
            "Plan TX SOW (HLD)",
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
        )

    def test_rejected_only_columns_do_not_resolve_pr_critical_fields(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Rejected only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ0656921",
                                "wbs_stage": "Network Planning",
                                "task_name": "Microwave",
                                "display_header": "Plan TX SOW (HLD)",
                            },
                            "fingerprint_key": "docata|ZDCSZ0656921|Network Planning|Microwave|Plan TX SOW (HLD)",
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ00904401",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TSS Status",
                            },
                            "fingerprint_key": "docata|ZDCSZ00904401|Acceptance|Microwave|PR TSS Status",
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ00904402",
                                "wbs_stage": "Acceptance",
                                "task_name": "Microwave",
                                "display_header": "PR TI Status",
                            },
                            "fingerprint_key": "docata|ZDCSZ00904402|Acceptance|Microwave|PR TI Status",
                        },
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["existing_tss_pr_status"]["status"], "MISSING")
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_tx_sow_rule_uses_tx_sow_lld_when_it_is_the_only_non_empty_override(self):
        record = self._build_record({"tx_sow_lld": "  MW Swap  ", "post_mocn_tx_sow_lld": ""})
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "MW Swap")
        evidence = record["source_evidence"]["fields"]["tx_sow_raw"]
        self.assertEqual(evidence["source_header_fingerprint"]["display_header"], "TX SOW (LLD)")

    def test_tx_sow_rule_uses_post_mocn_lld_when_it_is_the_only_non_empty_override(self):
        record = self._build_record({"tx_sow_lld": "", "post_mocn_tx_sow_lld": "  MW Post  "})
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "MW Post")
        evidence = record["source_evidence"]["fields"]["tx_sow_raw"]
        self.assertEqual(evidence["source_header_fingerprint"]["display_header"], "Post MOCN TX SOW (LLD)")

    def test_tx_sow_rule_prefers_post_mocn_lld_when_both_override_columns_have_values(self):
        record = self._build_record({"tx_sow_lld": "MW Base", "post_mocn_tx_sow_lld": "MW Post"})
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "MW Post")
        evidence = record["source_evidence"]["fields"]["tx_sow_raw"]
        self.assertEqual(evidence["source_header_fingerprint"]["display_header"], "Post MOCN TX SOW (LLD)")

    def test_tx_sow_rule_fails_closed_when_both_override_columns_are_blank(self):
        record = self._build_record({"tx_sow_lld": "", "post_mocn_tx_sow_lld": ""})
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "")
        self.assertIn("MISSING_PR_CRITICAL_FIELD:tx_sow_raw", record["validation"]["blocking_reasons"])
        self.assertEqual(record["validation"]["output_decision"], QUARANTINE_NO_ECC)

    def test_missing_approved_pr_critical_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(
            {"tx_sow_lld": "MW Swap", "post_mocn_tx_sow_lld": ""},
            resolved=resolved,
            scope="TI",
        )
        self.assertIn("MISSING_SOURCE_EVIDENCE:existing_ti_pr_status", record["validation"]["blocking_reasons"])

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record({"tx_sow_lld": "MW Swap", "post_mocn_tx_sow_lld": ""})
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(
            {"tx_sow_lld": "MW Swap", "post_mocn_tx_sow_lld": ""},
            profile=production,
            header_hash="changed-header-hash",
        )
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


class TestMwEosApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_alternates=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_alternates:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ01079156",
                    "wbs_stage": "Network Planning",
                    "task_name": "Microwave",
                    "display_header": "TX SOW Details",
                },
                {
                    "field_code": "site|fix00015",
                    "wbs_stage": "Site Basic Info",
                    "task_name": "Site Basic Info",
                    "display_header": "customer site name",
                },
            ):
                columns.append({"fingerprint": fingerprint, "fingerprint_key": fingerprint_key(fingerprint)})
        return {"sheets": [{"sheet_name": "MW EOS Swap", "columns": columns}]}

    def _resolved(self, *, include_alternates=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_alternates=include_alternates, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "MW Swap",
            "region": "Northern",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "GTSB",
            "existing_tss_pr_status": "SQ202506180613-GTSB",
            "existing_ti_pr_status": "No PR required-Work at TSS only",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "tx_sow_details": "detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-mw-eos.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_approved_pr_critical_fingerprints(self):
        resolved = self._resolved(include_alternates=True)
        for field_name in (
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        ):
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Microwave Tx SOW-1"],
        )

    def test_missing_approved_pr_critical_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(resolved=resolved, scope="TI")
        self.assertIn("MISSING_SOURCE_EVIDENCE:existing_ti_pr_status", record["validation"]["blocking_reasons"])

    def test_unapproved_alternate_candidates_do_not_unlock_pr_input(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Alternates only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01079156",
                                "wbs_stage": "Network Planning",
                                "task_name": "Microwave",
                                "display_header": "TX SOW Details",
                            },
                            "fingerprint_key": "docata|ZDCSZ01079156|Network Planning|Microwave|TX SOW Details",
                        },
                        {
                            "fingerprint": {
                                "field_code": "site|fix00015",
                                "wbs_stage": "Site Basic Info",
                                "task_name": "Site Basic Info",
                                "display_header": "customer site name",
                            },
                            "fingerprint_key": "site|fix00015|Site Basic Info|Site Basic Info|customer site name",
                        },
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["site_code"]["status"], "MISSING")

    def test_pr_reference_fields_normalize_consistently(self):
        record = self._build_record(
            {
                "existing_tss_pr_status": "SQ202506180613-GTSB",
                "existing_ti_pr_status": "No PR required-Work at TSS only",
            }
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        self.assertEqual(record["pr_context"]["existing_ti_pr_status"], PR_STATUS_NOT_REQUIRED)
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_tss_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_ti_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record()
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(profile=production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


class TestCelcomdigiBau2024ApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "celcomdigi_bau_2024_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_alternates=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_alternates:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ642123",
                    "wbs_stage": "TX Solution",
                    "task_name": "TX SOW Details",
                    "display_header": "TX SOW Details",
                },
                {
                    "field_code": "docata|ZDCSZ01036639",
                    "wbs_stage": "Installation",
                    "task_name": "Wireless RAN",
                    "display_header": "Subcon PR - Planning",
                },
            ):
                columns.append({"fingerprint": fingerprint, "fingerprint_key": fingerprint_key(fingerprint)})
        return {"sheets": [{"sheet_name": "2024 BAU", "columns": columns}]}

    def _resolved(self, *, include_alternates=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_alternates=include_alternates, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "MW Swap",
            "tx_upgrade_scope_raw": "Upgrade",
            "region": "Northern",
            "state": "Penang",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "Planner",
            "existing_tss_pr_status": "SQ202506180613-GTSB",
            "existing_ti_pr_status": "No PR required-Work at TSS only",
            "latitude": "5.1234",
            "longitude": "100.1234",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "boq_configuration": "1+0",
            "tx_sow_details": "detail",
            "ne_sow_details": "ne detail",
            "fe_sow_details": "fe detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-2024-bau.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_approved_pr_critical_fingerprints(self):
        resolved = self._resolved(include_alternates=True)
        for field_name in (
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        ):
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Tx SOW"],
        )

    def test_missing_approved_pr_critical_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(resolved=resolved, scope="TI")
        self.assertIn("MISSING_SOURCE_EVIDENCE:existing_ti_pr_status", record["validation"]["blocking_reasons"])

    def test_unapproved_alternate_candidates_do_not_unlock_pr_input(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Alternates only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ642123",
                                "wbs_stage": "TX Solution",
                                "task_name": "TX SOW Details",
                                "display_header": "TX SOW Details",
                            },
                            "fingerprint_key": "docata|ZDCSZ642123|TX Solution|TX SOW Details|TX SOW Details",
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01036639",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            },
                            "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                        },
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_rejected_subcon_pr_planning_does_not_map_to_existing_ti_pr_status(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Rejected only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01036639",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            },
                            "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                        }
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_pr_reference_fields_normalize_consistently(self):
        record = self._build_record(
            {
                "existing_tss_pr_status": "SQ202506180613-GTSB",
                "existing_ti_pr_status": "No PR required-Work at TSS only",
            }
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        self.assertEqual(record["pr_context"]["existing_ti_pr_status"], PR_STATUS_NOT_REQUIRED)
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_tss_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_ti_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record()
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(profile=production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


class TestCelcomdigiUspApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "celcomdigi_usp_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_alternates=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_alternates:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ642123",
                    "wbs_stage": "TX Solution",
                    "task_name": "TX SOW Details",
                    "display_header": "TX SOW Details",
                },
                {
                    "field_code": "docata|ZDCSZ01036639",
                    "wbs_stage": "Installation",
                    "task_name": "Wireless RAN",
                    "display_header": "Subcon PR - Planning",
                },
            ):
                columns.append({"fingerprint": fingerprint, "fingerprint_key": fingerprint_key(fingerprint)})
        return {"sheets": [{"sheet_name": "USP", "columns": columns}]}

    def _resolved(self, *, include_alternates=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_alternates=include_alternates, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "MW Swap",
            "tx_upgrade_scope_raw": "Upgrade",
            "region": "Northern",
            "state": "Penang",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "Planner",
            "existing_tss_pr_status": "SQ202506180613-GTSB",
            "existing_ti_pr_status": "No PR required-Work at TSS only",
            "latitude": "5.1234",
            "longitude": "100.1234",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "boq_configuration": "1+0",
            "tx_sow_details": "detail",
            "ne_sow_details": "ne detail",
            "fe_sow_details": "fe detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-usp.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_approved_pr_critical_fingerprints(self):
        resolved = self._resolved(include_alternates=True)
        for field_name in (
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        ):
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Tx SOW"],
        )

    def test_missing_approved_pr_critical_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(resolved=resolved, scope="TI")
        self.assertIn("MISSING_SOURCE_EVIDENCE:existing_ti_pr_status", record["validation"]["blocking_reasons"])

    def test_unapproved_alternate_candidates_do_not_unlock_pr_input(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Alternates only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ642123",
                                "wbs_stage": "TX Solution",
                                "task_name": "TX SOW Details",
                                "display_header": "TX SOW Details",
                            },
                            "fingerprint_key": "docata|ZDCSZ642123|TX Solution|TX SOW Details|TX SOW Details",
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01036639",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            },
                            "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                        },
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_rejected_subcon_pr_planning_does_not_map_to_existing_ti_pr_status(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Rejected only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01036639",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            },
                            "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                        }
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_pr_reference_fields_normalize_consistently(self):
        record = self._build_record(
            {
                "existing_tss_pr_status": "SQ202506180613-GTSB",
                "existing_ti_pr_status": "No PR required-Work at TSS only",
            }
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        self.assertEqual(record["pr_context"]["existing_ti_pr_status"], PR_STATUS_NOT_REQUIRED)
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_tss_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_ti_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record()
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(profile=production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


class TestJendelaApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_alternates=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_alternates:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ642123",
                    "wbs_stage": "Planner",
                    "task_name": "TX SOW Details",
                    "display_header": "TX SOW Details",
                },
                {
                    "field_code": "docata|ZDCSZ01036639",
                    "wbs_stage": "Installation",
                    "task_name": "Wireless RAN",
                    "display_header": "Subcon PR - Planning",
                },
            ):
                columns.append(
                    {
                        "fingerprint": fingerprint,
                        "fingerprint_key": fingerprint_key(fingerprint),
                    }
                )
        return {"sheets": [{"sheet_name": "Jendela TX Migration", "columns": columns}]}

    def _resolved(self, *, include_alternates=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_alternates=include_alternates, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "MW Swap",
            "region": "Northern",
            "subcontractor_tss": "GTSB",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "Planner",
            "existing_tss_pr_status": "",
            "existing_ti_pr_status": "",
            "latitude": "5.1234",
            "longitude": "100.1234",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "boq_configuration": "1+0",
            "tx_sow_details": "detail",
            "ne_sow_details": "ne detail",
            "fe_sow_details": "fe detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-jendela.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_seven_approved_runtime_fingerprints(self):
        resolved = self._resolved(include_alternates=True)
        approved_fields = (
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_tss",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        )
        for field_name in approved_fields:
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Tx SOW"],
        )
        self.assertEqual(
            resolved["existing_tss_pr_status"]["matches"][0]["fingerprint"]["wbs_stage"],
            "PR Team",
        )
        self.assertEqual(
            resolved["existing_ti_pr_status"]["matches"][0]["fingerprint"]["wbs_stage"],
            "PR team",
        )

    def test_missing_approved_pr_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(resolved=resolved, scope="TI")
        self.assertIn(
            "MISSING_SOURCE_EVIDENCE:existing_ti_pr_status",
            record["validation"]["blocking_reasons"],
        )

    def test_unapproved_alternates_do_not_unlock_required_fields(self):
        inventory = {
            "sheets": [
                {
                    "sheet_name": "Alternates only",
                    "columns": [
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ642123",
                                "wbs_stage": "Planner",
                                "task_name": "TX SOW Details",
                                "display_header": "TX SOW Details",
                            },
                            "fingerprint_key": "docata|ZDCSZ642123|Planner|TX SOW Details|TX SOW Details",
                        },
                        {
                            "fingerprint": {
                                "field_code": "docata|ZDCSZ01036639",
                                "wbs_stage": "Installation",
                                "task_name": "Wireless RAN",
                                "display_header": "Subcon PR - Planning",
                            },
                            "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                        },
                    ],
                }
            ]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_pr_reference_fields_normalize_consistently(self):
        record = self._build_record(
            {
                "existing_tss_pr_status": "SQ202506180613-GTSB",
                "existing_ti_pr_status": "No PR required-Work at TSS only",
            }
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        self.assertEqual(record["pr_context"]["existing_ti_pr_status"], PR_STATUS_NOT_REQUIRED)
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_tss_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_ti_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )

    def test_scope_specific_subcontractor_validation_remains_enforced(self):
        tss_record = self._build_record({"subcontractor_tss": ""}, scope="TSS")
        self.assertIn(
            "MISSING_PR_CRITICAL_FIELD:subcontractor_tss",
            tss_record["validation"]["blocking_reasons"],
        )
        ti_record = self._build_record({"subcontractor_ti": ""}, scope="TI")
        self.assertIn(
            "MISSING_PR_CRITICAL_FIELD:subcontractor_ti",
            ti_record["validation"]["blocking_reasons"],
        )

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record()
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(profile=production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
