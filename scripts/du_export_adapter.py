"""Exact-fingerprint adapter primitives for Canonical PR Site Record v1.

The foundation intentionally accepts only values supplied by an approved mapping
resolution. It never imports or invokes the ECC generator.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from canonical_site_validator import FIELD_PATHS, apply_validation_result, empty_canonical_site_record, validate_canonical_site_record
from profile_du_export import fingerprint_key, structural_fingerprint, structural_fingerprint_key
from sow_normalization import normalize_tx_sow
from jendela_migration_decision import derive_jendela_migration_decision


PR_STATUS_EXISTS = "PR_EXISTS"
PR_STATUS_NOT_REQUIRED = "NO_PR_REQUIRED"
PR_STATUS_NONE = "NO_PR"

_SUPPORTED_TRANSFORMS = {"trim", "uppercase", "parse_decimal", "normalize_pr_reference_status"}
_MAPPING_STATUS_RANK = {"UNVERIFIED": 0, "VERIFIED": 1, "APPROVED": 2}


def normalize_pr_reference_status(value: Any) -> str:
    """Reference-presence rule approved by JJ on 2026-07-07 for existing_*_pr_status.

    The source columns carry PR references, not statuses: a non-blank reference
    means a PR already exists (duplicate prevention must block), an explicit
    "No PR required..." marker means no PR is needed, and blank means no PR yet.
    """
    text = "" if value is None else str(value).strip()
    if not text or text.lower() in {"nan", "<na>"}:
        return PR_STATUS_NONE
    if text.lower().startswith("no pr required"):
        return PR_STATUS_NOT_REQUIRED
    return PR_STATUS_EXISTS


def _apply_transforms(value: Any, transforms: list[str]) -> tuple[Any, str]:
    result = value
    applied = []
    for transform in transforms:
        if transform == "trim" and isinstance(result, str):
            result = result.strip()
        elif transform == "uppercase" and isinstance(result, str):
            result = result.strip().upper()
        elif transform == "parse_decimal" and result not in (None, ""):
            result = float(result)
        elif transform == "normalize_pr_reference_status":
            result = normalize_pr_reference_status(result)
        elif transform not in _SUPPORTED_TRANSFORMS:
            raise ValueError(f"Unsupported foundation transform: {transform}")
        applied.append(transform)
    return result, "+".join(applied) if applied else "none"


def _select_first_non_empty_match(matches: list[Mapping[str, Any]], raw_values_by_fingerprint: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for source in matches:
        raw_value = raw_values_by_fingerprint.get(fingerprint_key(source["fingerprint"]))
        if isinstance(raw_value, str):
            if raw_value.strip():
                return source
        elif raw_value not in (None, ""):
            return source
    return None


def _apply_geography_correction(record: Dict[str, Any]) -> None:
    """Apply the one approved global Region/State correction with audit evidence."""
    context = record.get("pr_context", {})
    normalized_region = " ".join(str(context.get("region") or "").strip().split()).casefold()
    original_state = " ".join(str(context.get("state") or "").strip().split())
    normalized_state = original_state.casefold()
    if normalized_region != "northern" or normalized_state != "pahang":
        return
    context["state"] = "Perak"
    record.setdefault("source_evidence", {}).setdefault("geography_corrections", []).append(
        {
            "reason_code": "NORTHERN_PAHANG_CORRECTED_TO_PERAK",
            "field": "state",
            "original_value": original_state,
            "corrected_value": "Perak",
        }
    )


def _stronger_mapping_status(first: str, second: str) -> str:
    return max(
        (first, second),
        key=lambda value: _MAPPING_STATUS_RANK.get(str(value), -1),
    )


def resolve_profile_field_mappings(
    header_inventory: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    semantic_fallback_fields: set[str] | None = None,
) -> Dict[str, Any]:
    """Resolve approved source columns without relying on column position.

    Exact four-layer matching remains the default. Runtime-required fields may
    fall back to stable field code plus display header when a View changes only
    WBS/task placement. Matches retain the actual runtime fingerprint for row
    lookup and audit, and duplicate physical columns remain ambiguous.
    """
    if semantic_fallback_fields is None:
        semantic_fallback_fields = {
            name
            for name, config in profile.get("field_mapping", {}).items()
            if config.get("required")
        }
    available: Dict[str, list[Dict[str, Any]]] = {}
    semantic_available: Dict[tuple[str, str], list[Dict[str, Any]]] = {}
    for sheet_index, sheet in enumerate(header_inventory.get("sheets", [])):
        for column_index, column in enumerate(sheet.get("columns", [])):
            fingerprint = column["fingerprint"]
            source = {
                "sheet_name": sheet["sheet_name"],
                "fingerprint": fingerprint,
                "_source_identity": (sheet_index, column_index),
            }
            key = structural_fingerprint_key(fingerprint)
            available.setdefault(key, []).append(source)
            stable = structural_fingerprint(fingerprint)
            semantic_available.setdefault(
                (stable["field_code"], stable["display_header"]), []
            ).append(source)

    results: Dict[str, Any] = {}
    for canonical_field, config in profile.get("field_mapping", {}).items():
        matches_by_source: Dict[tuple[int, int], Dict[str, Any]] = {}
        for candidate in config.get("source_candidates", []):
            structural_key = structural_fingerprint_key(candidate["fingerprint"])
            candidate_status = str(candidate.get("mapping_status", "UNVERIFIED"))
            sources = available.get(structural_key, [])
            if not sources and canonical_field in semantic_fallback_fields and candidate_status == "APPROVED":
                stable = structural_fingerprint(candidate["fingerprint"])
                sources = semantic_available.get(
                    (stable["field_code"], stable["display_header"]), []
                )
            for source in sources:
                source_key = source["_source_identity"]
                existing = matches_by_source.get(source_key)
                if existing is None:
                    matches_by_source[source_key] = {
                        "sheet_name": source["sheet_name"],
                        "fingerprint": source["fingerprint"],
                        "mapping_status": candidate_status,
                    }
                    continue
                existing["mapping_status"] = _stronger_mapping_status(
                    str(existing.get("mapping_status", "UNVERIFIED")),
                    candidate_status,
                )
        matches = list(matches_by_source.values())
        if len(matches) == 1:
            status = "RESOLVED"
        elif len(matches) == 0:
            status = "MISSING"
        elif config.get("selection_mode") == "first_non_empty":
            status = "RESOLVED"
        else:
            status = "AMBIGUOUS"
        results[canonical_field] = {"status": status, "matches": matches}
    return results


def build_canonical_site_record(
    raw_values_by_fingerprint: Mapping[str, Any],
    profile: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    scope: str,
    resolved_mappings: Mapping[str, Any],
    sow_registry: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build one traceable record from exact resolved mappings, then validate it."""
    record = empty_canonical_site_record()
    record["identity"].update(
        {
            "project_key": context.get("project_key", profile.get("identity", {}).get("project_key", "")),
            "project_id": context.get("project_id", ""),
            "du_model_name": context.get("du_model_name", ""),
            "du_model_id": str(context.get("du_model_id", "")),
            "view_id": str(context.get("view_id", "")),
            "source_file_name": context.get("source_file_name", ""),
            "source_file_hash": context.get("source_file_hash", ""),
            "header_hash": context.get("header_hash", ""),
            "raw_header_hash": context.get("raw_header_hash", context.get("header_hash", "")),
            "structural_header_hash": context.get("structural_header_hash", ""),
            "approved_header_hash": context.get("approved_header_hash", ""),
            "header_hash_approval_basis": context.get("header_hash_approval_basis", ""),
            "source_row_number": context.get("source_row_number"),
        }
    )
    record["validation"]["profile_id"] = profile.get("profile_id", "")
    record["validation"]["profile_version"] = profile.get("profile_version", "")
    record["validation"]["mapping_version"] = profile.get("mapping_version", "")

    for canonical_field, mapping in resolved_mappings.items():
        status = mapping.get("status")
        if status == "AMBIGUOUS":
            record["source_evidence"]["ambiguous_fields"].append(canonical_field)
            continue
        if status != "RESOLVED":
            continue
        config = profile.get("field_mapping", {}).get(canonical_field, {})
        matches = list(mapping.get("matches", []))
        if not matches:
            continue
        if config.get("selection_mode") == "first_non_empty":
            source = _select_first_non_empty_match(matches, raw_values_by_fingerprint)
            if source is None:
                continue
        else:
            source = matches[0]
        key = fingerprint_key(source["fingerprint"])
        raw_value = raw_values_by_fingerprint.get(key)
        transformed_value, transformation = _apply_transforms(raw_value, list(config.get("transforms", [])))
        path = FIELD_PATHS.get(canonical_field)
        if path:
            record[path[0]][path[1]] = transformed_value
        record["source_evidence"]["fields"][canonical_field] = {
            "source_header_fingerprint": deepcopy(source["fingerprint"]),
            "source_value": raw_value,
            "transformation": transformation,
            "mapping_status": source.get("mapping_status", "UNVERIFIED"),
        }

    if not record["pr_context"]["tx_sow_normalized"]:
        raw_sow = record["pr_context"]["tx_sow_raw"]
        raw_evidence = record["source_evidence"]["fields"].get("tx_sow_raw")
        if sow_registry is not None:
            normalized = normalize_tx_sow(raw_sow, sow_registry)
            record["pr_context"]["tx_sow_normalized"] = normalized["canonical_sow"]
            if raw_evidence:
                record["source_evidence"]["fields"]["tx_sow_normalized"] = {
                    **raw_evidence,
                    "transformation": "canonical_sow_registry",
                    "normalization_status": normalized["normalization_status"],
                    "sow_classification": normalized["classification"],
                }
        elif isinstance(raw_sow, str) and raw_sow.strip():
            record["pr_context"]["tx_sow_normalized"] = raw_sow.strip()
            if raw_evidence:
                record["source_evidence"]["fields"]["tx_sow_normalized"] = {
                    **raw_evidence,
                    "transformation": "trim",
                    "normalization_status": "UNVERIFIED",
                }

    _apply_geography_correction(record)
    migration_decision = derive_jendela_migration_decision(
        profile_id=str(profile.get("profile_id", "")),
        scope=scope,
        pr_context=record["pr_context"],
        technical_context=record["technical_context"],
    )
    if migration_decision is not None:
        record["pr_context"]["migration_decision"] = migration_decision

    result = validate_canonical_site_record(record, scope)
    return apply_validation_result(record, result)
