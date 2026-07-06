"""Canonical PR Site Record v1 contract and safe validation helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, Tuple

CANONICAL_SCHEMA_VERSION = "1.0"
PR_INPUT_READY = "PR_INPUT_READY"
PR_INPUT_READY_WITH_REVIEW = "PR_INPUT_READY_WITH_REVIEW"
PR_INPUT_INCOMPLETE = "PR_INPUT_INCOMPLETE"
PR_INPUT_QUARANTINED = "PR_INPUT_QUARANTINED"

SCOPE_REQUIRED_FIELDS = {
    "TSS": (
        "site_code",
        "tx_sow_raw",
        "tx_sow_normalized",
        "region",
        "subcontractor_ti",
        "existing_tss_pr_status",
    ),
    "TI": (
        "site_code",
        "tx_sow_raw",
        "tx_sow_normalized",
        "region",
        "subcontractor_ti",
        "existing_ti_pr_status",
    ),
}

FIELD_PATHS = {
    "site_code": ("site", "site_code"),
    "site_name": ("site", "site_name"),
    "du_key": ("site", "du_key"),
    "tx_sow_raw": ("pr_context", "tx_sow_raw"),
    "tx_sow_normalized": ("pr_context", "tx_sow_normalized"),
    "tx_upgrade_scope_raw": ("pr_context", "tx_upgrade_scope_raw"),
    "region": ("pr_context", "region"),
    "state": ("pr_context", "state"),
    "subcontractor_ti": ("pr_context", "subcontractor_ti"),
    "subcontractor_planning": ("pr_context", "subcontractor_planning"),
    "existing_tss_pr_status": ("pr_context", "existing_tss_pr_status"),
    "existing_ti_pr_status": ("pr_context", "existing_ti_pr_status"),
    "latitude": ("technical_context", "latitude"),
    "longitude": ("technical_context", "longitude"),
    "antenna_size_ne": ("technical_context", "antenna_size_ne"),
    "antenna_size_fe": ("technical_context", "antenna_size_fe"),
    "boq_configuration": ("technical_context", "boq_configuration"),
    "tx_sow_details": ("technical_context", "tx_sow_details"),
    "ne_sow_details": ("technical_context", "ne_sow_details"),
    "fe_sow_details": ("technical_context", "fe_sow_details"),
}


def empty_canonical_site_record() -> Dict[str, Any]:
    """Return a complete v1 shape with no source values or production approval."""
    return {
        "schema_version": CANONICAL_SCHEMA_VERSION,
        "identity": {
            "project_key": "",
            "project_id": "",
            "du_model_name": "",
            "du_model_id": "",
            "view_id": "",
            "source_file_name": "",
            "source_file_hash": "",
            "header_hash": "",
            "source_row_number": None,
        },
        "site": {"site_code": "", "site_name": "", "du_key": ""},
        "pr_context": {
            "tx_sow_raw": "",
            "tx_sow_normalized": "",
            "tx_upgrade_scope_raw": "",
            "region": "",
            "state": "",
            "subcontractor_ti": "",
            "subcontractor_planning": "",
            "existing_tss_pr_status": "",
            "existing_ti_pr_status": "",
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
        "source_evidence": {"fields": {}, "ambiguous_fields": []},
        "validation": {
            "profile_id": "",
            "profile_version": "",
            "pr_input_classification": PR_INPUT_QUARANTINED,
            "blocking_reasons": [],
            "warnings": [],
        },
    }


def _get_path(value: Mapping[str, Any], path: Tuple[str, str]) -> Any:
    section = value.get(path[0], {})
    return section.get(path[1]) if isinstance(section, Mapping) else None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _append_unique(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def validate_canonical_site_record(record: Mapping[str, Any], scope: str) -> Dict[str, Any]:
    """Validate the structural/provenance contract without invoking PR business rules."""
    scope = str(scope).upper()
    if scope not in SCOPE_REQUIRED_FIELDS:
        raise ValueError("scope must be TSS or TI")

    blocking_reasons: list[str] = []
    warnings: list[str] = []
    required_top_level = ("identity", "site", "pr_context", "technical_context", "source_evidence", "validation")
    for section in required_top_level:
        if not isinstance(record.get(section), Mapping):
            blocking_reasons.append(f"MISSING_CANONICAL_SECTION:{section}")

    if blocking_reasons:
        classification = PR_INPUT_INCOMPLETE
        return {"classification": classification, "blocking_reasons": blocking_reasons, "warnings": warnings}

    identity = record["identity"]
    validation = record["validation"]
    evidence_fields = record["source_evidence"].get("fields", {})
    ambiguous_fields = record["source_evidence"].get("ambiguous_fields", [])

    if _is_blank(validation.get("profile_id")) or _is_blank(validation.get("profile_version")):
        blocking_reasons.append("UNKNOWN_OR_UNVERSIONED_DU_PROFILE")
    if _is_blank(identity.get("header_hash")):
        blocking_reasons.append("MISSING_HEADER_HASH")
    if _is_blank(identity.get("source_file_hash")):
        blocking_reasons.append("MISSING_SOURCE_FILE_HASH")

    if ambiguous_fields:
        _append_unique(blocking_reasons, [f"AMBIGUOUS_HEADER_MAPPING:{field}" for field in ambiguous_fields])

    for field in SCOPE_REQUIRED_FIELDS[scope]:
        value = _get_path(record, FIELD_PATHS[field])
        # Existing PR status is allowed to be blank, but its source must remain
        # mapped for duplicate prevention to be trustworthy.
        if field not in {"existing_tss_pr_status", "existing_ti_pr_status"} and _is_blank(value):
            blocking_reasons.append(f"MISSING_PR_CRITICAL_FIELD:{field}")
        evidence = evidence_fields.get(field) if isinstance(evidence_fields, Mapping) else None
        if not isinstance(evidence, Mapping) or not evidence.get("source_header_fingerprint"):
            blocking_reasons.append(f"MISSING_SOURCE_EVIDENCE:{field}")

    raw_warnings = validation.get("warnings", [])
    if isinstance(raw_warnings, list):
        _append_unique(warnings, [str(item) for item in raw_warnings if str(item).strip()])

    if any(reason.startswith("AMBIGUOUS_HEADER_MAPPING") or reason.startswith("UNKNOWN_") for reason in blocking_reasons):
        classification = PR_INPUT_QUARANTINED
    elif blocking_reasons:
        classification = PR_INPUT_INCOMPLETE
    elif warnings:
        classification = PR_INPUT_READY_WITH_REVIEW
    else:
        classification = PR_INPUT_READY

    return {"classification": classification, "blocking_reasons": blocking_reasons, "warnings": warnings}


def apply_validation_result(record: Mapping[str, Any], result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copied record with validation fields updated; never mutates source evidence."""
    updated = deepcopy(dict(record))
    updated["validation"] = dict(updated.get("validation", {}))
    updated["validation"]["pr_input_classification"] = result["classification"]
    updated["validation"]["blocking_reasons"] = list(result.get("blocking_reasons", []))
    updated["validation"]["warnings"] = list(result.get("warnings", []))
    return updated
