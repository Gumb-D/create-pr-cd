"""Jendela TX Migration TI work-plan derivation.

Issue #77 retires the historical TX Before Migration + Final Backhaul matrix.
For the Jendela profile only, dismantle work is derived from TX Before Migration,
additional work is derived independently from Tx SOW, and both parts are then
combined into one atomic work plan. Final Backhaul remains audit evidence only.
"""
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
    "BBU Patching / MW IDU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        "model_sow": "BBU Patching / MW IDU Patching",
        "required_pbom_codes": [],
    },
    "BBU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        "model_sow": "BBU Patching",
        "required_pbom_codes": [],
    },
    "MW IDU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        "model_sow": "MW IDU Patching",
        "required_pbom_codes": [],
    },
    "MW New Link": {
        "work_item": "MW New Link",
        "model_sow": "MW Installation",
        "required_pbom_codes": [],
    },
}

_BEFORE_MIGRATION_WORK = {
    "starlink": "Dismantle Starlink",
    "mw": "Dismantle MW",
    "microwave": "Dismantle MW",
    "fiber own build": None,
}

_TX_SOW_WORK = {
    "bbu patching / mw idu patching": "BBU Patching / MW IDU Patching",
    "bbu patching": "BBU Patching",
    "mw idu patching": "MW IDU Patching",
    "mw new link / reroute": "MW New Link",
    "mw by others": None,
    "-": None,
    "": None,
}


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split()).casefold()


def derive_jendela_migration_decision(
    *, profile_id: str, scope: str, pr_context: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Return the Issue #77 atomic TI work plan for Jendela only.

    `final_backhaul` is deliberately not used as an input to either decision.
    It is retained in `source_values` solely so audit output can show the raw
    iEPMS evidence when the optional field is available.
    """
    if profile_id != JENDELA_PROFILE_ID or str(scope).upper() != "TI":
        return None

    before_raw = pr_context.get("tx_before_migration")
    tx_sow_raw = pr_context.get("tx_sow_raw")
    final_backhaul_raw = pr_context.get("final_backhaul")

    before = _normalized(before_raw)
    tx_sow = _normalized(tx_sow_raw)
    source_values = {
        "tx_before_migration": before_raw,
        "tx_sow_raw": tx_sow_raw,
        "final_backhaul": final_backhaul_raw,
    }

    if not before:
        return {
            "classification": "REVIEW_REQUIRED",
            "reason_code": "JENDELA_TX_BEFORE_MIGRATION_MISSING",
            "decision_code": "",
            "source_values": source_values,
            "work_items": [],
        }
    if before not in _BEFORE_MIGRATION_WORK:
        return {
            "classification": "REVIEW_REQUIRED",
            "reason_code": "JENDELA_TX_BEFORE_MIGRATION_NOT_APPROVED",
            "decision_code": "",
            "source_values": source_values,
            "work_items": [],
        }

    # Blank and '-' are explicit no-additional-work states. Every other unknown
    # value fails closed so a dismantle item can never leak out as partial ECC.
    if tx_sow not in _TX_SOW_WORK:
        return {
            "classification": "REVIEW_REQUIRED",
            "reason_code": "JENDELA_TX_SOW_NOT_APPROVED",
            "decision_code": "",
            "source_values": source_values,
            "work_items": [],
        }

    work_item_names: list[str] = []
    dismantle_work = _BEFORE_MIGRATION_WORK[before]
    additional_work = _TX_SOW_WORK[tx_sow]
    if dismantle_work:
        work_item_names.append(dismantle_work)
    if additional_work:
        work_item_names.append(additional_work)

    return {
        "classification": "APPROVED",
        "reason_code": "JENDELA_TI_WORK_PLAN_APPROVED",
        "decision_code": "JENDELA_TI_WORK_PLAN",
        "source_values": source_values,
        "work_items": [deepcopy(_WORK_ITEMS[name]) for name in work_item_names],
    }
