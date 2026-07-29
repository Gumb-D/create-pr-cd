#!/usr/bin/env python3
"""Fail-closed subcontractor and contract controls for PR generation."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


EXCLUDED_REASON_CODE = "PR_NOT_REQUIRED_OUTSOURCED_TO_OTHER_VENDOR"
CONTRACT_MISSING_REASON_CODE = "CONTRACT_MAPPING_NOT_FOUND"
CONTRACT_MISSING_ACTION = "Provide and approve the subcontractor contract number before PR generation."
DISALLOWED_CONTRACT_VALUES = {"", "UNKNOWN", "N/A", "NA", "NONE", "NULL", "TBD", "PLACEHOLDER"}


class SafetyControlError(RuntimeError):
    """Structured configuration or commercial-safety error."""

    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def normalize_subcontractor(value: Any) -> str:
    """Trim, collapse internal whitespace, and compare subcontractors case-insensitively."""

    return " ".join(str(value or "").strip().split()).upper()


def _read_text(path: Path, error_code: str, label: str) -> str:
    candidate = Path(path)
    if not candidate.is_file():
        raise SafetyControlError(
            error_code,
            f"{label} file is missing: {candidate}",
            {"path": str(candidate), "required_action": f"Restore a valid approved {label.lower()} file."},
        )
    try:
        return candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise SafetyControlError(
            error_code,
            f"{label} file could not be read: {candidate}",
            {"path": str(candidate), "error": str(error)},
        ) from error


def load_subcontractor_policy(path: Path) -> dict[str, Any]:
    """Load and validate the explicit subcontractor PR-exclusion policy."""

    text = _read_text(path, "SUBCONTRACTOR_POLICY_NOT_FOUND", "Subcontractor PR policy")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise SafetyControlError(
            "SUBCONTRACTOR_POLICY_INVALID",
            "Subcontractor PR policy is malformed JSON.",
            {"path": str(path), "error": str(error)},
        ) from error

    if not isinstance(payload, dict) or str(payload.get("schema_version", "")).strip() != "1.0":
        raise SafetyControlError(
            "SUBCONTRACTOR_POLICY_INVALID",
            "Subcontractor PR policy must be an object with schema_version 1.0.",
            {"path": str(path)},
        )
    raw_exclusions = payload.get("excluded_from_pr")
    if not isinstance(raw_exclusions, dict) or not raw_exclusions:
        raise SafetyControlError(
            "SUBCONTRACTOR_POLICY_INVALID",
            "Subcontractor PR policy must define at least one excluded_from_pr entry.",
            {"path": str(path)},
        )

    exclusions: dict[str, dict[str, Any]] = {}
    for raw_name, raw_rule in raw_exclusions.items():
        name = normalize_subcontractor(raw_name)
        if not name or not isinstance(raw_rule, dict):
            raise SafetyControlError(
                "SUBCONTRACTOR_POLICY_INVALID",
                "Every excluded subcontractor must have a non-blank name and object rule.",
                {"path": str(path), "subcontractor": raw_name},
            )
        raw_scopes = raw_rule.get("scopes")
        if not isinstance(raw_scopes, list):
            raise SafetyControlError(
                "SUBCONTRACTOR_POLICY_INVALID",
                "Excluded subcontractor scopes must be a list.",
                {"path": str(path), "subcontractor": raw_name},
            )
        scopes = sorted({str(scope).strip().upper() for scope in raw_scopes if str(scope).strip()})
        if not scopes or any(scope not in {"TSS", "TI"} for scope in scopes):
            raise SafetyControlError(
                "SUBCONTRACTOR_POLICY_INVALID",
                "Excluded subcontractor scopes may contain only TSS and TI.",
                {"path": str(path), "subcontractor": raw_name, "scopes": scopes},
            )
        classification = str(raw_rule.get("classification", "")).strip().upper()
        reason_code = str(raw_rule.get("reason_code", "")).strip().upper()
        reason = str(raw_rule.get("reason", "")).strip()
        if classification != "IGNORED" or not reason_code or not reason:
            raise SafetyControlError(
                "SUBCONTRACTOR_POLICY_INVALID",
                "Excluded subcontractor rules require classification IGNORED, reason_code, and reason.",
                {"path": str(path), "subcontractor": raw_name},
            )
        if name in exclusions:
            raise SafetyControlError(
                "SUBCONTRACTOR_POLICY_INVALID",
                "Subcontractor PR policy contains duplicate normalized subcontractor names.",
                {"path": str(path), "subcontractor": raw_name},
            )
        exclusions[name] = {
            "scopes": scopes,
            "classification": classification,
            "reason_code": reason_code,
            "reason": reason,
        }

    return {"schema_version": "1.0", "excluded_from_pr": exclusions, "path": str(Path(path).resolve())}


def get_exclusion_rule(policy: Mapping[str, Any], subcontractor: Any, scope: str) -> dict[str, Any] | None:
    """Return an explicit exclusion rule for a scope, or None."""

    key = normalize_subcontractor(subcontractor)
    rule = policy.get("excluded_from_pr", {}).get(key)
    if not isinstance(rule, dict):
        return None
    return dict(rule) if str(scope).strip().upper() in set(rule.get("scopes", [])) else None


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(cell and set(cell) <= {"-", ":"} for cell in cells)


def load_contract_reference(path: Path) -> dict[str, dict[str, str]]:
    """Parse approved subcontractor contract mappings from the Markdown reference."""

    text = _read_text(path, "CONTRACT_REFERENCE_NOT_FOUND", "Contract reference")
    in_section = False
    mappings: dict[str, dict[str, str]] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            in_section = stripped.casefold() == "## subcontractor to contract number".casefold()
            continue
        if not in_section or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or _is_separator_row(cells):
            continue
        if cells[0].casefold().startswith("subcontractor"):
            continue
        subcontractor, contract_number, company_name = cells[:3]
        key = normalize_subcontractor(subcontractor)
        normalized_contract = str(contract_number).strip()
        if not key or normalized_contract.upper() in DISALLOWED_CONTRACT_VALUES:
            raise SafetyControlError(
                "CONTRACT_REFERENCE_INVALID",
                "Contract reference contains a blank or placeholder subcontractor/contract value.",
                {"path": str(path), "subcontractor": subcontractor, "contract_number": contract_number},
            )
        existing = mappings.get(key)
        if existing and existing["contract_number"] != normalized_contract:
            raise SafetyControlError(
                "CONTRACT_REFERENCE_INVALID",
                "Contract reference contains conflicting duplicate subcontractor mappings.",
                {
                    "path": str(path),
                    "subcontractor": subcontractor,
                    "contract_numbers": [existing["contract_number"], normalized_contract],
                },
            )
        mappings[key] = {
            "subcontractor": subcontractor,
            "contract_number": normalized_contract,
            "company_name": str(company_name).strip(),
        }

    if not mappings:
        raise SafetyControlError(
            "CONTRACT_REFERENCE_INVALID",
            "No subcontractor contract mappings were found in the approved contract reference.",
            {"path": str(path)},
        )
    return mappings


def set_generation_decision(
    record: dict[str, Any],
    classification: str,
    reason_code: str,
    reason: str,
    required_action: str = "",
) -> dict[str, Any]:
    """Attach an auditable PR-generation decision without changing canonical evidence."""

    decision = {
        "classification": str(classification).strip().upper(),
        "reason_code": str(reason_code).strip().upper(),
        "reason": str(reason).strip(),
        "required_action": str(required_action).strip(),
    }
    record["pr_generation_decision"] = decision
    return record


def validate_candidate_contracts(
    records: list[dict[str, Any]],
    scope: str,
    contract_mappings: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split candidates into approved-contract records and review-required records."""

    normalized_scope = str(scope).strip().upper()
    field = "subcontractor_tss" if normalized_scope == "TSS" else "subcontractor_ti"
    valid: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for record in records:
        subcontractor = record.get("pr_context", {}).get(field, "")
        key = normalize_subcontractor(subcontractor)
        mapping = contract_mappings.get(key)
        contract_number = str((mapping or {}).get("contract_number", "")).strip()
        if not mapping or contract_number.upper() in DISALLOWED_CONTRACT_VALUES:
            set_generation_decision(
                record,
                "REVIEW_REQUIRED",
                CONTRACT_MISSING_REASON_CODE,
                "No approved subcontractor contract mapping was found.",
                CONTRACT_MISSING_ACTION,
            )
            missing.append(record)
            continue
        record["approved_contract"] = dict(mapping)
        valid.append(record)
    return valid, missing


def reason_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    """Return deterministic decision reason counts for reporting."""

    counts = Counter(
        str(record.get("pr_generation_decision", {}).get("reason_code", "UNSPECIFIED")).strip().upper()
        or "UNSPECIFIED"
        for record in records
    )
    return dict(sorted(counts.items()))
