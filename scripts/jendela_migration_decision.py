"""Jendela TX Migration TI work-plan derivation.

Issue #77 retires the historical TX Before Migration + Final Backhaul matrix.
For the Jendela profile only, dismantle work is derived from TX Before Migration,
additional work is derived independently from Tx SOW, and both parts are then
combined into one atomic work plan. Final Backhaul remains audit evidence only.
"""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


JENDELA_PROFILE_ID = "jendela_tx_migration_pr_v1"

# These SOW names and fixed PBOM requirements are taken from PR Model v4.1.
# Dynamic choose-one PBOMs (MW geography/antenna groups) deliberately stay
# model-driven and therefore are not hardcoded here.
_WORK_ITEMS = {
    "Dismantle Starlink": {
        "work_item": "Dismantle Starlink",
        "model_sow": "Starlink Dismanle",
        "required_pbom_codes": ["350000597850", "350000597852"],
    },
    "Dismantle MW": {
        "work_item": "Dismantle MW",
        "model_sow": "MW Dismantle",
        "required_pbom_codes": [],
    },
    "BBU Patching / MW IDU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        # v4.1 split the historical combined patching model into BBU Patching
        # and MW IDU Patching. Their mandatory business row is identical
        # (PBOM 350001095420), so the combined source wording resolves to the
        # BBU Patching model while retaining an explicit PBOM invariant.
        "model_sow": "BBU Patching",
        "required_pbom_codes": ["350001095420"],
    },
    "BBU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        "model_sow": "BBU Patching",
        "required_pbom_codes": ["350001095420"],
    },
    "MW IDU Patching": {
        "work_item": "BBU Patching / MW IDU Patching",
        "model_sow": "MW IDU Patching",
        "required_pbom_codes": ["350001095420"],
    },
    "MW New Link": {
        "work_item": "MW New Link",
        "model_sow": "MW New Link / Reroute",
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
    "cancel / drop": None,
    "-": None,
    "": None,
}


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split()).casefold()


_EXPLICIT_ANTENNA_SIZE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[mM]\b")
_ANTENNA_BEFORE_POLARIZATION = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*[mM]?(?=[\s_/-]+(?:SP|DP|XPIC)\b)",
    re.IGNORECASE,
)


def _valid_antenna_size(value: float) -> bool:
    return 0.1 <= value <= 5.0


def parse_jendela_before_mw_antenna_size(value: Any) -> float | None:
    """Extract existing-MW antenna size without mistaking bandwidth for antenna.

    Jendela MW Config places antenna diameter immediately before the
    polarization token (SP/DP/XPIC). That structural evidence takes precedence
    over generic ``M``-suffixed tokens, which may represent channel bandwidth.
    If polarization structure is unavailable, a generic explicit-metre fallback
    is accepted only when exactly one in-range token is present.
    """
    text = " ".join(str(value or "").strip().split())
    if not text:
        return None

    for match in _ANTENNA_BEFORE_POLARIZATION.finditer(text):
        size = float(match.group(1))
        if _valid_antenna_size(size):
            return size

    fallback_sizes = [
        float(match.group(1))
        for match in _EXPLICIT_ANTENNA_SIZE.finditer(text)
        if _valid_antenna_size(float(match.group(1)))
    ]
    if len(fallback_sizes) == 1:
        return fallback_sizes[0]
    return None


def derive_jendela_migration_decision(
    *,
    profile_id: str,
    scope: str,
    pr_context: Mapping[str, Any],
    technical_context: Mapping[str, Any] | None = None,
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
    technical_context = technical_context or {}
    before_mw_config_raw = technical_context.get("before_mw_config_raw")

    before = _normalized(before_raw)
    tx_sow = _normalized(tx_sow_raw)
    source_values = {
        "tx_before_migration": before_raw,
        "tx_sow_raw": tx_sow_raw,
        "final_backhaul": final_backhaul_raw,
        "before_mw_config_raw": before_mw_config_raw,
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

    # Blank, '-', MW by others and Cancel / Drop are explicit no-additional-work
    # states. Cancel / Drop remains subject to the existing higher-priority
    # partition hard stop, so the decision must not make the canonical record
    # REVIEW_REQUIRED before that global rule is applied.
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

    if not work_item_names:
        return {
            "classification": "APPROVED_NO_OUTPUT",
            "reason_code": "JENDELA_TI_NO_WORK_REQUIRED",
            "decision_code": "JENDELA_TI_NO_WORK",
            "source_values": source_values,
            "work_items": [],
        }

    work_items = [deepcopy(_WORK_ITEMS[name]) for name in work_item_names]
    if dismantle_work == "Dismantle MW":
        before_mw_antenna_size = parse_jendela_before_mw_antenna_size(before_mw_config_raw)
        if before_mw_antenna_size is None:
            missing = before_mw_config_raw is None or not str(before_mw_config_raw).strip()
            return {
                "classification": "REVIEW_REQUIRED",
                "reason_code": (
                    "JENDELA_BEFORE_MW_ANTENNA_MISSING"
                    if missing
                    else "JENDELA_BEFORE_MW_ANTENNA_UNRESOLVED"
                ),
                "decision_code": "",
                "source_values": source_values,
                "work_items": [],
            }
        for item in work_items:
            if item.get("work_item") == "Dismantle MW":
                item["before_mw_config_raw"] = before_mw_config_raw
                item["before_mw_antenna_size_m"] = before_mw_antenna_size
                break

    return {
        "classification": "APPROVED",
        "reason_code": "JENDELA_TI_WORK_PLAN_APPROVED",
        "decision_code": "JENDELA_TI_WORK_PLAN",
        "source_values": source_values,
        "work_items": work_items,
    }
