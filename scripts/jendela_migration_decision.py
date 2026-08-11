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


_POLARIZATION_MARKER = re.compile(r"\b(?:SP|DP|XPIC)\b", re.IGNORECASE)
_ANTENNA_BEFORE_POLARIZATION = re.compile(
    r"(?<![A-Za-z0-9_.,+\-])(\d+(?:\.\d+)?)\s*[mM]?(?=[\s_/-]+(?:SP|DP|XPIC)\b)",
    re.IGNORECASE,
)
_FREQUENCY_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*[gG](?![A-Za-z0-9])"
)
_RADIO_CONFIGURATION_TOKEN = re.compile(r"(?<!\d)\d+\s*\+\s*\d+(?!\d)")
_STANDARD_MW_LINK = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*[gG](?![A-Za-z0-9])"
    r"(?P<body>.*?)"
    r"(?<!\d)\d+\s*\+\s*\d+(?!\d)",
    re.IGNORECASE,
)
_UNPOLARIZED_NUMERIC_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_.,+\-])(\d+(?:\.\d+)?)(?:\s*[mM])?(?![\w.])"
)
_DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d{1,2}(?:\D|$))")

# Exact antenna diameters represented by the approved Jendela v4.1
# `MW Dismantle` choose-one rows. The set prevents bandwidth values such as
# 3.5M from being mistaken for a dish diameter while keeping polarization
# wording optional.
_JENDELA_V41_DISMANTLE_ANTENNA_SIZES_M = frozenset(
    {0.3, 0.6, 0.9, 1.2, 1.8, 2.4, 3.2}
)


def _supported_dismantle_antenna_size(value: float) -> bool:
    return value in _JENDELA_V41_DISMANTLE_ANTENNA_SIZES_M


def _polarized_antenna_size(text: str) -> float | None:
    polarization_markers = list(_POLARIZATION_MARKER.finditer(text))
    if not polarization_markers:
        return None

    polarized_matches = [
        float(match.group(1))
        for match in _ANTENNA_BEFORE_POLARIZATION.finditer(text)
    ]
    if len(polarized_matches) != len(polarization_markers):
        return None
    if any(not _supported_dismantle_antenna_size(size) for size in polarized_matches):
        return None

    polarized_sizes = set(polarized_matches)
    if len(polarized_sizes) == 1:
        return next(iter(polarized_sizes))
    return None


def _unpolarized_standard_antenna_size(body: str) -> float | None:
    candidates = [
        float(match.group(1))
        for match in _UNPOLARIZED_NUMERIC_TOKEN.finditer(body)
    ]
    if len(candidates) != 1:
        return None

    candidate = candidates[0]
    if not _supported_dismantle_antenna_size(candidate):
        return None
    return candidate


def parse_jendela_before_mw_antenna_size(value: Any) -> float | None:
    """Extract existing-MW antenna size from unambiguous MW Config evidence.

    Polarization wording (SP/DP/XPIC) is optional. When present, it is the
    strongest structural hint: every marker must have one standalone parseable
    antenna value immediately before it, and every resolved value must be
    represented by the approved Jendela v4.1 MW Dismantle model. When
    polarization wording is absent, the parser accepts only a standard
    GHz -> body -> N+N link shape whose body contains exactly one standalone
    supported numeric antenna candidate. Decimal-comma notation is normalized
    before parsing. Signed, identifier-embedded, ambiguous, unsupported,
    missing, or conflicting evidence fails closed.
    """
    text = " ".join(str(value or "").strip().split())
    if not text:
        return None
    text = _DECIMAL_COMMA.sub(".", text)

    frequency_matches = list(_FREQUENCY_TOKEN.finditer(text))
    radio_matches = list(_RADIO_CONFIGURATION_TOKEN.finditer(text))
    link_matches = list(_STANDARD_MW_LINK.finditer(text))

    if link_matches:
        if not (
            len(link_matches) == len(frequency_matches) == len(radio_matches)
        ):
            return None

        resolved_sizes: list[float] = []
        for link_match in link_matches:
            link_text = link_match.group(0)
            if _POLARIZATION_MARKER.search(link_text):
                link_size = _polarized_antenna_size(link_text)
            else:
                link_size = _unpolarized_standard_antenna_size(
                    link_match.group("body")
                )
            if link_size is None:
                return None
            resolved_sizes.append(link_size)

        unique_sizes = set(resolved_sizes)
        if len(unique_sizes) == 1:
            return next(iter(unique_sizes))
        return None

    # Preserve structurally qualified legacy formatting that may omit explicit
    # GHz or N+N tokens. Polarization remains an optional hint, not a mandatory
    # prerequisite for standard MW Config values.
    if _POLARIZATION_MARKER.search(text):
        return _polarized_antenna_size(text)
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
