"""Deterministic Planning PR line-item selection for Issue #34.

This module is intentionally pure.  It receives only the canonical DU Model
identity and Planning subcontractor value; Tx SOW, TX Planning Remarks, antenna,
and other TSS/TI inputs are not part of the selector contract.
"""
from __future__ import annotations

from dataclasses import dataclass


FULL_PLANNING_DUS = frozenset(
    {
        "2023 TX Rollout",
        "2023 Celcomdigi BAU",
        "2024 Celcomdigi BAU",
        "Celcomdigi USP",
        "Jendela TX Migration",
    }
)

SINGLE_HOP_PLANNING_DUS = frozenset(
    {
        "TX Mini Project",
        "MW EOS Swap",
        "ZTE TX MINI",
    }
)

SUPPORTED_PLANNING_DUS = FULL_PLANNING_DUS | SINGLE_HOP_PLANNING_DUS

FULL_PLANNING_PBOM = "350001143904"
SINGLE_HOP_PLANNING_PBOM = "350001143905"
AA_PLANNING_PBOM = "350001042321"


@dataclass(frozen=True)
class PlanningSelection:
    status: str
    pbom_code: str | None
    quantity: int | None
    unit: str | None
    contract_subcontractor: str | None
    reason_code: str | None = None


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def select_planning_item(du_model_name: str, subcontractor_planning: str) -> PlanningSelection:
    """Select exactly one approved Planning PBOM or fail closed.

    `_AA` is a line-item selector only.  For contract lookup it normalizes to
    the base GCI/GTSB identity, while the selected PBOM remains the AA-only item.
    """
    du_model = _normalize_text(du_model_name)
    source_subcontractor = _normalize_text(subcontractor_planning).upper()

    if not source_subcontractor:
        return PlanningSelection(
            status="NOT_APPLICABLE",
            pbom_code=None,
            quantity=None,
            unit=None,
            contract_subcontractor=None,
            reason_code="PLANNING_SUBCONTRACTOR_BLANK",
        )

    if du_model not in SUPPORTED_PLANNING_DUS:
        return PlanningSelection(
            status="REVIEW_REQUIRED",
            pbom_code=None,
            quantity=None,
            unit=None,
            contract_subcontractor=None,
            reason_code="PLANNING_DU_MODEL_NOT_APPROVED",
        )

    if source_subcontractor in {"GCI_AA", "GTSB_AA"}:
        return PlanningSelection(
            status="RESOLVED",
            pbom_code=AA_PLANNING_PBOM,
            quantity=1,
            unit="Hop",
            contract_subcontractor=source_subcontractor.removesuffix("_AA"),
        )

    if source_subcontractor not in {"GCI", "GTSB"}:
        return PlanningSelection(
            status="REVIEW_REQUIRED",
            pbom_code=None,
            quantity=None,
            unit=None,
            contract_subcontractor=None,
            reason_code="PLANNING_SUBCONTRACTOR_NOT_APPROVED",
        )

    pbom_code = (
        FULL_PLANNING_PBOM
        if du_model in FULL_PLANNING_DUS
        else SINGLE_HOP_PLANNING_PBOM
    )
    return PlanningSelection(
        status="RESOLVED",
        pbom_code=pbom_code,
        quantity=1,
        unit="Hop",
        contract_subcontractor=source_subcontractor,
    )
