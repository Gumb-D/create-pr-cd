"""Approved TI-only Jendela migration decision matrix."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


JENDELA_PROFILE_ID = "jendela_tx_migration_pr_v1"

_WORK_ITEMS = {
    "Dismantle Starlink": {
        "work_item": "Dismantle Starlink",
        "model_sow": "Starlink Dismantle (Return/MRCF included) & Migration",
        "required_pbom_codes": ["350000597850", "350000597852"],
    },
    "Dismantle MW": {
        "work_item": "Dismantle MW",
        "model_sow": "MW Dismantle",
        "required_pbom_codes": [],
    },
    "MW New Link": {
        "work_item": "MW New Link",
        "model_sow": "MW Installation",
        "required_pbom_codes": [],
    },
    "BBU Patching": {
        "work_item": "BBU Patching",
        "model_sow": "BBU Patching",
        "required_pbom_codes": [],
    },
}

_MATRIX = {
    ("starlink", "fiber own build"): (
        "STARLINK_TO_FIBER_OWN_BUILD",
        ("Dismantle Starlink", "BBU Patching"),
    ),
    ("microwave", "fiber own build"): (
        "MICROWAVE_TO_FIBER_OWN_BUILD",
        ("Dismantle MW", "BBU Patching"),
    ),
    ("starlink", "microwave"): (
        "STARLINK_TO_MICROWAVE",
        ("Dismantle Starlink", "MW New Link"),
    ),
    ("microwave", "microwave"): (
        "MICROWAVE_TO_MICROWAVE",
        ("Dismantle MW", "MW New Link"),
    ),
}


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split()).casefold()


def derive_jendela_migration_decision(
    *, profile_id: str, scope: str, pr_context: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Return a structured decision only for the approved Jendela TI path."""
    if profile_id != JENDELA_PROFILE_ID or str(scope).upper() != "TI":
        return None

    before_raw = pr_context.get("tx_before_migration")
    final_raw = pr_context.get("final_backhaul")
    before = _normalized(before_raw)
    final = _normalized(final_raw)
    source_values = {
        "tx_before_migration": before_raw,
        "final_backhaul": final_raw,
    }
    if not before or not final:
        return {
            "classification": "REVIEW_REQUIRED",
            "reason_code": "JENDELA_MIGRATION_SOURCE_MISSING",
            "decision_code": "",
            "source_values": source_values,
            "work_items": [],
        }

    branch = _MATRIX.get((before, final))
    if branch is None:
        return {
            "classification": "REVIEW_REQUIRED",
            "reason_code": "JENDELA_MIGRATION_COMBINATION_NOT_APPROVED",
            "decision_code": "",
            "source_values": source_values,
            "work_items": [],
        }

    decision_code, work_item_names = branch
    return {
        "classification": "APPROVED",
        "reason_code": "JENDELA_MIGRATION_COMBINATION_APPROVED",
        "decision_code": decision_code,
        "source_values": source_values,
        "work_items": [deepcopy(_WORK_ITEMS[name]) for name in work_item_names],
    }
