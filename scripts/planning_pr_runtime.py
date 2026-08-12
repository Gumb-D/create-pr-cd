"""Planning-scope runtime helpers for Issue #34.

The legacy create_pr_impl remains the execution engine for existing TSS/TI
behavior.  These helpers provide only the Planning-specific eligibility and
contract-normalization behavior injected by the official create_pr.py wrapper.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from canonical_site_validator import PR_INPUT_READY
from du_export_adapter import PR_STATUS_EXISTS, PR_STATUS_NOT_REQUIRED
from planning_pr_selector import select_planning_item
from pr_safety_controls import (
    CONTRACT_MISSING_ACTION,
    CONTRACT_MISSING_REASON_CODE,
    DISALLOWED_CONTRACT_VALUES,
    normalize_subcontractor,
    set_generation_decision,
)

PLANNING_SCOPE = "PLANNING"


def planning_scope_subcontractor(record: Mapping[str, Any]) -> str:
    return str(record.get("pr_context", {}).get("subcontractor_planning", "") or "").strip()


def partition_planning_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Apply approved Planning eligibility without consulting Tx SOW."""
    partitions: dict[str, list[dict[str, Any]]] = {
        "candidates": [],
        "duplicates": [],
        "ignored": [],
        "review_required": [],
    }
    for record in records:
        context = record.get("pr_context", {})
        subcontractor = planning_scope_subcontractor(record)
        if not subcontractor:
            set_generation_decision(
                record,
                "IGNORED",
                "MISSING_SUBCONTRACTOR",
                "No Planning subcontractor was provided.",
            )
            partitions["ignored"].append(record)
            continue

        status = context.get("existing_planning_pr_status")
        if status == PR_STATUS_EXISTS:
            set_generation_decision(
                record,
                "DUPLICATE_BLOCKED",
                "EXISTING_PR_REFERENCE",
                "An existing Planning PR reference is already present.",
            )
            partitions["duplicates"].append(record)
            continue
        if status == PR_STATUS_NOT_REQUIRED:
            set_generation_decision(
                record,
                "IGNORED",
                "PR_STATUS_NOT_REQUIRED",
                "The approved Planning PR status states that a PR is not required.",
            )
            partitions["ignored"].append(record)
            continue

        if record.get("validation", {}).get("pr_input_classification") != PR_INPUT_READY:
            set_generation_decision(
                record,
                "REVIEW_REQUIRED",
                "CANONICAL_INPUT_NOT_READY",
                "The canonical record is not classified PR_INPUT_READY.",
                "Resolve canonical validation blockers before Planning PR generation.",
            )
            partitions["review_required"].append(record)
            continue

        selection = select_planning_item(
            str(record.get("identity", {}).get("du_model_name", "") or ""),
            subcontractor,
        )
        if selection.status != "RESOLVED":
            set_generation_decision(
                record,
                "REVIEW_REQUIRED",
                str(selection.reason_code or "PLANNING_SELECTION_UNRESOLVED"),
                "Planning PR line item could not be resolved from the approved DU/subcontractor matrix.",
                "Review the DU Model and Planning subcontractor value before rerunning create-pr.",
            )
            partitions["review_required"].append(record)
            continue

        record["planning_selection"] = asdict(selection)
        set_generation_decision(
            record,
            "CANDIDATE",
            "ELIGIBLE",
            "All Planning pre-contract eligibility checks passed.",
        )
        partitions["candidates"].append(record)
    return partitions


def validate_planning_candidate_contracts(
    records: list[dict[str, Any]],
    contract_mappings: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate contracts using the base GCI/GTSB identity selected for Planning."""
    valid: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for record in records:
        selection = record.get("planning_selection", {})
        contract_subcontractor = str(selection.get("contract_subcontractor", "") or "").strip()
        key = normalize_subcontractor(contract_subcontractor)
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
        approved_contract = dict(mapping)
        approved_contract["scope"] = PLANNING_SCOPE
        record["approved_contract"] = approved_contract
        valid.append(record)
    return valid, missing
