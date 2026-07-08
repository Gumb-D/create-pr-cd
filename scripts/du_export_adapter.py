"""Exact-fingerprint adapter primitives for Canonical PR Site Record v1.

The foundation intentionally accepts only values supplied by an approved mapping
resolution. It never imports or invokes the ECC generator.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from canonical_site_validator import FIELD_PATHS, apply_validation_result, empty_canonical_site_record, validate_canonical_site_record
from profile_du_export import fingerprint_key
from sow_normalization import normalize_tx_sow


PR_STATUS_EXISTS = "PR_EXISTS"
PR_STATUS_NOT_REQUIRED = "NO_PR_REQUIRED"
PR_STATUS_NONE = "NO_PR"

_SUPPORTED_TRANSFORMS = {"trim", "uppercase", "parse_decimal", "normalize_pr_reference_status"}


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


def resolve_profile_field_mappings(header_inventory: Mapping[str, Any], profile: Mapping[str, Any]) -> Dict[str, Any]:
    """Resolve only exact four-layer fingerprints; never by column index or aliases."""
    available = {}
    for sheet in header_inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            available.setdefault(column["fingerprint_key"], []).append(
                {"sheet_name": sheet["sheet_name"], "fingerprint": column["fingerprint"]}
            )

    results: Dict[str, Any] = {}
    for canonical_field, config in profile.get("field_mapping", {}).items():
        matches = []
        for candidate in config.get("source_candidates", []):
            key = fingerprint_key(candidate["fingerprint"])
            for source in available.get(key, []):
                matches.append({**source, "mapping_status": candidate.get("mapping_status", "UNVERIFIED")})
        if len(matches) == 1:
            status = "RESOLVED"
        elif len(matches) == 0:
            status = "MISSING"
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
        source = mapping["matches"][0]
        key = fingerprint_key(source["fingerprint"])
        raw_value = raw_values_by_fingerprint.get(key)
        config = profile.get("field_mapping", {}).get(canonical_field, {})
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
            # Controlled normalization through the approved canonical SOW
            # registry: only PR_TRIGGER values normalize with APPROVED status;
            # everything else stays fail-closed for output.
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
            # No registry supplied: preserve the raw value as controlled
            # evidence only; the guard blocks unverified normalization.
            record["pr_context"]["tx_sow_normalized"] = raw_sow.strip()
            if raw_evidence:
                record["source_evidence"]["fields"]["tx_sow_normalized"] = {
                    **raw_evidence,
                    "transformation": "trim",
                    "normalization_status": "UNVERIFIED",
                }

    result = validate_canonical_site_record(record, scope)
    return apply_validation_result(record, result)
