"""Deterministic TI subtype selection for the MW Hardware Upgrade PR model.

The PR model contains one mandatory three-way choice:

* IDU work, without bundled site survey;
* ODU work, without bundled site survey;
* ODU work, with bundled site survey.

Selection is driven by approved canonical evidence passed through the legacy
bridge. Missing or contradictory evidence is never guessed.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


REASON_CODE = "MW_HARDWARE_UPGRADE_TYPE_UNRESOLVED"

SUBTYPE_PBOM_CODES = {
    "IDU_WITHOUT_SITE_SURVEY": "350001095419",
    "ODU_WITHOUT_SITE_SURVEY": "350001095418",
    "ODU_WITH_SITE_SURVEY": "350001095417",
}

EVIDENCE_FIELDS = (
    "BOQ Configuration",
    "TX SOW Details",
    "NE SOW Details",
    "FE SOW Details",
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _evidence_texts(row: Mapping[str, Any]) -> list[str]:
    return [
        _text(row.get(field, ""))
        for field in EVIDENCE_FIELDS
        if _text(row.get(field, ""))
    ]


def _has_any(patterns: Sequence[str], texts: Sequence[str]) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for text in texts
        for pattern in patterns
    )


def _component_signals(row: Mapping[str, Any]) -> dict[str, bool]:
    evidence_texts = _evidence_texts(row)
    idu_component = r"(?:IDU|RTN\w*|ISM\d*|MD\d+|ISV\d*)"
    odu_component = r"(?:ODU|XMC[\w-]*|SRU[\w-]*)"
    new_action = r"(?:new|insert|install|add|replace|swap|change|upgrade)\w*"
    completed_action = r"(?:inserted|installed|added|replaced|swapped|changed|upgraded)"

    new_idu = _has_any(
        (
            rf"\bnew\s+(?:\d+\s*[xX]\s*)?{idu_component}\b",
            rf"\b{new_action}\b[^.;\n]{{0,60}}\b{idu_component}\b",
            rf"\b{idu_component}\b[^.;\n]{{0,45}}\b{completed_action}\b",
        ),
        evidence_texts,
    )
    new_odu = _has_any(
        (
            rf"\bnew\s+(?:\d+\s*[xX]\s*)?{odu_component}\b",
            rf"\b{new_action}\b[^.;\n]{{0,60}}\b{odu_component}\b",
            rf"\b{odu_component}\b[^.;\n]{{0,45}}\b{completed_action}\b",
        ),
        evidence_texts,
    )

    reuse_idu = _has_any(
        (
            rf"\bre[- ]?use\w*\b.{{0,45}}\b{idu_component}\b",
            rf"\bexisting\s+{idu_component}\b",
        ),
        evidence_texts,
    )
    reuse_odu = _has_any(
        (
            rf"\bre[- ]?use\w*\b.{{0,45}}\b{odu_component}\b",
            rf"\bexisting\s+{odu_component}\b",
        ),
        evidence_texts,
    )

    return {
        "new_idu": new_idu,
        "new_odu": new_odu,
        "reuse_idu": reuse_idu,
        "reuse_odu": reuse_odu,
        "has_evidence": bool(evidence_texts),
    }


def _survey_mode(upgrade_scope: Any) -> str | None:
    tokens = {
        token
        for token in re.split(r"[^A-Z0-9]+", _text(upgrade_scope).upper())
        if token
    }
    if "TSS" in tokens:
        return "WITH_SITE_SURVEY"
    if "TI" in tokens:
        return "WITHOUT_SITE_SURVEY"
    return None


def resolve_mw_hardware_upgrade_subtype(row: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve one approved subtype or return a fail-closed review result."""
    signals = _component_signals(row)
    upgrade_scope = _text(row.get("TX Upgrade Scope", ""))

    if signals["new_idu"] and not signals["new_odu"]:
        subtype = "IDU_WITHOUT_SITE_SURVEY"
    elif signals["new_odu"] and not signals["new_idu"]:
        survey_mode = _survey_mode(upgrade_scope)
        if survey_mode is None:
            return _unresolved(
                row,
                signals,
                "ODU work is identified, but TX Upgrade Scope does not state whether TSS is included.",
            )
        subtype = (
            "ODU_WITH_SITE_SURVEY"
            if survey_mode == "WITH_SITE_SURVEY"
            else "ODU_WITHOUT_SITE_SURVEY"
        )
    elif signals["new_idu"] and signals["new_odu"]:
        return _unresolved(
            row,
            signals,
            "Both IDU and ODU new-work evidence is present; the mandatory three-way choice is not unique.",
        )
    else:
        return _unresolved(
            row,
            signals,
            "No approved IDU or ODU new-work evidence could be resolved from the bridged source fields.",
        )

    return {
        "status": "RESOLVED",
        "subtype": subtype,
        "pbom_code": SUBTYPE_PBOM_CODES[subtype],
        "signals": signals,
        "tx_upgrade_scope": upgrade_scope,
    }


def _unresolved(
    row: Mapping[str, Any],
    signals: Mapping[str, bool],
    description: str,
) -> dict[str, Any]:
    site_code = _text(
        row.get("customer site code")
        or row.get("Site ID")
        or row.get("Site Code")
    )
    return {
        "status": "REVIEW_REQUIRED",
        "reason_code": REASON_CODE,
        "reason_description": description,
        "required_action": (
            "Confirm whether the hardware work is IDU or ODU and, for ODU work, "
            "whether TX Upgrade Scope includes TSS."
        ),
        "technical_detail": (
            f"site={site_code}; tx_upgrade_scope={_text(row.get('TX Upgrade Scope', ''))}; "
            f"new_idu={signals.get('new_idu')}; new_odu={signals.get('new_odu')}; "
            f"reuse_idu={signals.get('reuse_idu')}; reuse_odu={signals.get('reuse_odu')}"
        ),
        "signals": dict(signals),
        "tx_upgrade_scope": _text(row.get("TX Upgrade Scope", "")),
    }


def select_mw_hardware_upgrade_item(
    group_items: Sequence[Mapping[str, Any]],
    row: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    """Select exactly one PR-model row from the approved three-way group."""
    result = resolve_mw_hardware_upgrade_subtype(row)
    if result["status"] != "RESOLVED":
        return [], result

    pbom_code = result["pbom_code"]
    matches = [
        item
        for item in group_items
        if str(item.get("PBOM_Code", "")).strip() == pbom_code
    ]
    if len(matches) != 1:
        result = dict(result)
        result.update(
            {
                "status": "REVIEW_REQUIRED",
                "reason_code": REASON_CODE,
                "reason_description": (
                    "The resolved MW Hardware Upgrade subtype does not map to exactly one PR-model row."
                ),
                "required_action": "Confirm the approved PR-model three-way group and PBOM codes.",
                "technical_detail": (
                    f"subtype={result.get('subtype')}; pbom_code={pbom_code}; "
                    f"matching_rows={len(matches)}; group_rows={len(group_items)}"
                ),
            }
        )
        return [], result

    return [matches[0]], result
