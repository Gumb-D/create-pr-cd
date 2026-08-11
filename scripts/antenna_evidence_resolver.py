"""Deterministic antenna-installation evidence resolution for TI PR selection.

Direct canonical antenna fields remain authoritative. Endpoint SOW details are
allowed only as fallback evidence, followed by the common TX SOW Details source
when it contains explicit antenna-installation-size evidence. Canonical
production rows must also prove that every consumed source mapping is APPROVED.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

DIRECT_NE = "MW Config Antenna Size NE"
DIRECT_FE = "MW Config Antenna Size FE"
DETAIL_NE = "NE SOW Details"
DETAIL_FE = "FE SOW Details"
COMMON_DETAIL = "TX SOW Details"
GOVERNANCE_FIELD = "Antenna Evidence Governance"
CANONICAL_GOVERNANCE = "CANONICAL_MAPPING_STATUS"
_SOURCE_STATUS_FIELDS = {
    DIRECT_NE: "Antenna Size NE Mapping Status",
    DIRECT_FE: "Antenna Size FE Mapping Status",
    DETAIL_NE: "NE SOW Details Mapping Status",
    DETAIL_FE: "FE SOW Details Mapping Status",
    COMMON_DETAIL: "TX SOW Details Mapping Status",
}

_ANTENNA_WORDS = ("antenna", "dish")
_INSTALL_INTENT_RE = r"(?:install(?:ation|ed|ing)?|replac(?:e|ed|ing)?|swap(?:ped|ping)?|new|target|proposed|replacement|build|upgrade)"
_NON_INSTALL_INTENT_RE = (
    r"(?:dismantl(?:e|ed|ing)?|decom(?:mission(?:ed|ing)?)?|remove|removed|removal|"
    r"existing|old|reuse|reused|retain|retained)"
)
_ACTION_INTENT_RE = rf"(?:{_INSTALL_INTENT_RE}|{_NON_INSTALL_INTENT_RE})"
_INSTALL_INTENT_PATTERN = re.compile(rf"\b{_INSTALL_INTENT_RE}\b", re.IGNORECASE)
_NON_INSTALL_INTENT_PATTERN = re.compile(rf"\b{_NON_INSTALL_INTENT_RE}\b", re.IGNORECASE)
_DIRECTIONAL_GOVERNING_ACTION_PATTERN = re.compile(
    r"\b(?:upgrade|replac(?:e|ed|ing|ement)?|swap(?:ped|ping)?|chang(?:e|ed|ing)?|"
    r"migrat(?:e|ed|ing|ion)?)\b",
    re.IGNORECASE,
)
_SOURCE_SIDE_INTENT_PATTERN = re.compile(
    rf"\b(?:upgrade|replac(?:e|ed|ing|ement)?|swap(?:ped|ping)?|chang(?:e|ed|ing)?|"
    rf"migrat(?:e|ed|ing|ion)?|{_NON_INSTALL_INTENT_RE})\b",
    re.IGNORECASE,
)

_HWS_RE = r"[ \t]*"
_HWS1_RE = r"[ \t]+"
_TARGET_MODIFIER_RE = rf"(?:(?:install(?:ed|ing)?){_HWS1_RE}(?:(?:a|an|the){_HWS1_RE})?)?(?:(?:new|target|proposed|replacement){_HWS1_RE})?"
_METRE_SUFFIX_RE = rf"(?:{_HWS_RE}m(?:eters?|etres?)?\b)?"
_QUOTE_UNIT_RE = r'''['"′″’‘“”]'''
_TARGET_FIRST_SOURCE_PATTERN = re.compile(
    rf"\b(?:replacing|to{_HWS1_RE}replace)\b", re.IGNORECASE
)
_NEGATED_INTENT_PREFIX_PATTERN = re.compile(
    rf"(?:\b(?:do{_HWS1_RE}not|does{_HWS1_RE}not|did{_HWS1_RE}not|"
    rf"must{_HWS1_RE}not|should{_HWS1_RE}not|cannot|can['’]t|don['’]t|"
    rf"doesn['’]t|didn['’]t|without|no|not(?:{_HWS1_RE}required{_HWS1_RE}to)?)"
    rf"{_HWS_RE})$",
    re.IGNORECASE,
)
_POSTPOSITIVE_NOT_REQUIRED_PATTERN = re.compile(
    rf"\b(?:is{_HWS1_RE})?not{_HWS1_RE}required\b",
    re.IGNORECASE,
)
_FORWARD_ANTENNA_SIZE_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}(?:antenna|dish)\b{_HWS_RE}"
    rf"(?:(?:(?:with|of){_HWS1_RE})?(?:size|diameter)\b{_HWS_RE}[:=]?{_HWS_RE})?"
    rf"\d+(?:[.,]\d+)?{_METRE_SUFFIX_RE}"
)
_REVERSE_ANTENNA_SIZE_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}\d+(?:[.,]\d+)?{_METRE_SUFFIX_RE}{_HWS1_RE}(?:antenna|dish)\b"
)
_ANTENNA_SIZE_TARGET_RE = rf"(?:{_FORWARD_ANTENNA_SIZE_TARGET_RE}|{_REVERSE_ANTENNA_SIZE_TARGET_RE})"
_GENERIC_REVERSE_ANTENNA_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}(?:[\(\[]{_HWS_RE})?\d+(?:[.,]\d+)?"
    rf"[^;,\r\n&!?]{{0,48}}?\b(?:antenna|dish)\b"
)
_DIRECTIONAL_ANTENNA_TRANSITION_RE = (
    rf"\b(?:with|by|to)\b(?={_HWS1_RE}(?:"
    rf"{_TARGET_MODIFIER_RE}(?:antenna|dish)\b|{_GENERIC_REVERSE_ANTENNA_TARGET_RE}))"
)
_DIRECTIONAL_ANTENNA_TRANSITION_PATTERN = re.compile(
    _DIRECTIONAL_ANTENNA_TRANSITION_RE, re.IGNORECASE
)
_DIRECTIONAL_ANTENNA_SEPARATOR_RE = (
    rf"\b(?:with|by|to)\b(?={_HWS1_RE}{_ANTENNA_SIZE_TARGET_RE})"
)
_DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN = re.compile(
    _DIRECTIONAL_ANTENNA_SEPARATOR_RE, re.IGNORECASE
)
_CLAUSE_SEPARATOR_PATTERN = re.compile(
    rf"(?:[;,\r\n&!?]|\.(?=\s|$)|\b(?:and|then)\b|"
    rf"(?:[:/|]|[-–—])(?={_HWS_RE}{_ACTION_INTENT_RE}\b)|{_DIRECTIONAL_ANTENNA_SEPARATOR_RE})",
    re.IGNORECASE,
)
_EXPLICIT_NON_METRE_UNIT_SUFFIX_PATTERN = re.compile(
    rf"{_HWS_RE}(?:(?:[-–—/:|]{_HWS_RE})|(?:[\(\[]{_HWS_RE}))?(?:[A-Za-z]|{_QUOTE_UNIT_RE})",
    re.IGNORECASE,
)
_MULTI_DOT_NUMERIC_TOKEN_PATTERN = re.compile(r"(?<![\d.])\d+(?:\.\d+){2,}(?:/\d+)?(?![\d./])")
_BROKEN_MULTILINE_INSTALL_TARGET_PATTERN = re.compile(
    rf"\b(?:with|by|to)\b[ \t\r\n]+install(?:ed|ing)?"
    rf"(?:[ \t\r\n]+(?:a|an|the))?"
    rf"(?:[ \t\r\n]+(?:new|target|proposed|replacement))?"
    rf"[ \t\r\n]+(?:antenna|dish)\b",
    re.IGNORECASE,
)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def _supported_size(value: float) -> bool:
    return 0 < value <= 5.0


def _unique_sorted(values: list[float]) -> list[float]:
    return sorted(set(round(value, 6) for value in values if _supported_size(value)))


def _canonical_governance_enabled(row: Mapping[str, Any]) -> bool:
    return str(row.get(GOVERNANCE_FIELD, "") or "").strip().upper() == CANONICAL_GOVERNANCE


def _mapping_status(row: Mapping[str, Any], source_field: str) -> str:
    return str(row.get(_SOURCE_STATUS_FIELDS[source_field], "") or "").strip().upper()


def _source_is_approved(row: Mapping[str, Any], source_field: str) -> bool:
    if not _canonical_governance_enabled(row):
        return True
    return _mapping_status(row, source_field) == "APPROVED"


def _parse_direct_size(value: Any) -> float | None:
    if _is_blank(value):
        return None
    text = str(value).strip().replace(",", ".")
    text = _MULTI_DOT_NUMERIC_TOKEN_PATTERN.sub(" ", text)
    candidates: list[float] = []
    for match in re.finditer(
        r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)(?=[ \t]*(?:m(?:eters?|etres?)?\b|$|[_/;,)]))",
        text,
        re.IGNORECASE,
    ):
        try:
            candidates.append(float(match.group(1)))
        except ValueError:
            continue
    supported = _unique_sorted(candidates)
    return max(supported) if supported else None


def _clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    clause_start = 0
    clause_end = len(text)
    for match in _CLAUSE_SEPARATOR_PATTERN.finditer(text):
        if match.end() <= start:
            clause_start = match.end()
            continue
        if match.start() >= end:
            clause_end = match.start()
            break
    return clause_start, clause_end


def _is_directional_target_clause(text: str, clause_start: int) -> bool:
    return any(match.end() == clause_start for match in _DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN.finditer(text))


def _candidate_is_antenna_size_phrase(text: str, start: int, end: int) -> bool:
    left = text[max(0, start - 72):start]
    right = text[end:min(len(text), end + 40)]
    if re.search(
        r"\b(?:antenna|dish)\b[ \t]*(?:(?:(?:with|of)[ \t]+)?(?:size|diameter)\b[ \t]*[:=]?[ \t]*)?$",
        left,
        re.IGNORECASE,
    ):
        return True
    reverse = right
    unit = re.match(r"[ \t]*m(?:eters?|etres?)?\b", reverse, re.IGNORECASE)
    if unit:
        reverse = reverse[unit.end():]
    return re.match(r"[ \t]*(?:antenna|dish)\b", reverse, re.IGNORECASE) is not None


def _has_source_side_transition(text: str, start: int, end: int, clause_start: int, clause_end: int) -> bool:
    for transition in _DIRECTIONAL_ANTENNA_TRANSITION_PATTERN.finditer(text):
        if transition.start() < end:
            continue
        if transition.start() > clause_end:
            break
        return _SOURCE_SIDE_INTENT_PATTERN.search(text[clause_start:transition.start()]) is not None
    return False


def _is_target_first_source(text: str, start: int, clause_start: int) -> bool:
    return _TARGET_FIRST_SOURCE_PATTERN.search(text[clause_start:start]) is not None


def _intent_is_negated(clause: str, intent_start: int) -> bool:
    prefix = clause[:intent_start]
    return _NEGATED_INTENT_PREFIX_PATTERN.search(prefix) is not None


def _directional_target_has_valid_governing_action(text: str, clause_start: int) -> bool:
    separator = next(
        (
            match
            for match in _DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN.finditer(text)
            if match.end() == clause_start
        ),
        None,
    )
    if separator is None:
        return False

    source_clause_start = 0
    for boundary in _CLAUSE_SEPARATOR_PATTERN.finditer(text, 0, separator.start()):
        source_clause_start = boundary.end()
    source_clause = text[source_clause_start:separator.start()]
    actions = list(_DIRECTIONAL_GOVERNING_ACTION_PATTERN.finditer(source_clause))
    if not actions:
        return False
    governing_action = actions[-1]
    if _intent_is_negated(source_clause, governing_action.start()):
        return False
    if _POSTPOSITIVE_NOT_REQUIRED_PATTERN.search(source_clause[governing_action.end():]):
        return False
    return True


def _has_installation_intent(text: str, start: int, end: int) -> bool:
    clause_start, clause_end = _clause_bounds(text, start, end)
    clause = text[clause_start:clause_end]
    token_center = ((start + end) / 2) - clause_start
    candidate_end = end - clause_start
    if _POSTPOSITIVE_NOT_REQUIRED_PATTERN.search(clause[candidate_end:]):
        return False
    if clause_end < len(text) and _DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN.match(text, clause_end):
        return False
    if _has_source_side_transition(text, start, end, clause_start, clause_end):
        return False
    if _is_target_first_source(text, start, clause_start):
        return False
    if _is_directional_target_clause(text, clause_start):
        return _directional_target_has_valid_governing_action(text, clause_start)
    positive = [
        match for match in _INSTALL_INTENT_PATTERN.finditer(clause)
        if not _intent_is_negated(clause, match.start())
    ]
    if not positive:
        return False
    negative = list(_NON_INSTALL_INTENT_PATTERN.finditer(clause))
    nearest_positive = min(abs(((m.start() + m.end()) / 2) - token_center) for m in positive)
    if not negative:
        return True
    nearest_negative = min(abs(((m.start() + m.end()) / 2) - token_center) for m in negative)
    return nearest_positive < nearest_negative


def _has_antenna_specific_context(text: str, start: int, end: int) -> bool:
    if not _candidate_is_antenna_size_phrase(text, start, end):
        return False
    if not _has_installation_intent(text, start, end):
        return False
    suffix = text[end:min(len(text), end + 16)].casefold()
    return re.match(r"[ \t]*(?:ghz|mhz|mbps|gbps|kbps)\b", suffix) is None


def _parse_detail_sizes(value: Any, *, require_antenna_context: bool) -> list[float]:
    if _is_blank(value):
        return []
    text = re.sub(r"(?<=\d),(?=\d)", ".", str(value))
    for broken_multiline_target in _BROKEN_MULTILINE_INSTALL_TARGET_PATTERN.finditer(text):
        matched_target = broken_multiline_target.group(0)
        if "\r" in matched_target or "\n" in matched_target:
            return []
    candidates: list[float] = []
    consumed: list[tuple[int, int]] = []
    for match in re.finditer(
        r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)[ \t]*m(?:eters?|etres?)?\b",
        text,
        re.IGNORECASE,
    ):
        if require_antenna_context and not _has_antenna_specific_context(text, match.start(), match.end()):
            continue
        try:
            size = float(match.group(1))
        except ValueError:
            continue
        if _supported_size(size):
            candidates.append(size)
            consumed.append((match.start(), match.end()))
    for match in re.finditer(r"(?<![\d.])(\d+\.\d+)(?!\d)(?!\.\d)", text):
        if any(a <= match.start() < b for a, b in consumed):
            continue
        suffix = text[match.end():min(len(text), match.end() + 24)]
        reverse_antenna_noun = re.match(r"[ \t]*(?:antenna|dish)\b", suffix, re.IGNORECASE)
        if not reverse_antenna_noun and _EXPLICIT_NON_METRE_UNIT_SUFFIX_PATTERN.match(suffix):
            continue
        if not _has_antenna_specific_context(text, match.start(), match.end()):
            continue
        try:
            size = float(match.group(1))
        except ValueError:
            continue
        if _supported_size(size):
            candidates.append(size)
    return _unique_sorted(candidates)


def _endpoint_resolution(row: Mapping[str, Any], direct_field: str, detail_field: str) -> dict[str, Any]:
    direct_raw = row.get(direct_field, "")
    if _source_is_approved(row, direct_field):
        direct_size = _parse_direct_size(direct_raw)
        if direct_size is not None:
            return {"size": direct_size, "source": direct_field, "raw_value": direct_raw, "priority": "DIRECT", "mapping_status": _mapping_status(row, direct_field) or None}
    detail_raw = row.get(detail_field, "")
    if _source_is_approved(row, detail_field):
        detail_sizes = _parse_detail_sizes(detail_raw, require_antenna_context=True)
        if detail_sizes:
            return {"size": max(detail_sizes), "source": detail_field, "raw_value": detail_raw, "priority": "ENDPOINT_SOW_DETAIL", "mapping_status": _mapping_status(row, detail_field) or None}
    return {"size": None, "source": None, "raw_value": None, "priority": None, "mapping_status": None}


def resolve_installation_antenna_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    ne = _endpoint_resolution(row, DIRECT_NE, DETAIL_NE)
    fe = _endpoint_resolution(row, DIRECT_FE, DETAIL_FE)
    endpoint_sizes = [v for v in (ne["size"], fe["size"]) if v is not None]
    common_raw = row.get(COMMON_DETAIL, "")
    common_sizes = _parse_detail_sizes(common_raw, require_antenna_context=True) if _source_is_approved(row, COMMON_DETAIL) else []
    common_size = max(common_sizes) if common_sizes else None
    if ne["size"] is not None and fe["size"] is not None:
        status, selected_size, group_source = "RESOLVED", max(endpoint_sizes), "ENDPOINT_EVIDENCE"
    elif common_size is not None:
        status = "RESOLVED_COMMON"
        selected_size = max(endpoint_sizes + [common_size])
        group_source = COMMON_DETAIL if not endpoint_sizes else "ENDPOINT_AND_TX_SOW_DETAILS"
    elif endpoint_sizes:
        status, selected_size, group_source = "INCOMPLETE", max(endpoint_sizes), "INCOMPLETE_ENDPOINT_EVIDENCE"
    else:
        status, selected_size, group_source = "MISSING", None, None
    evidence = []
    for endpoint, resolved in (("NE", ne), ("FE", fe)):
        if resolved["size"] is not None:
            evidence.append({"endpoint": endpoint, "source": resolved["source"], "raw_value": resolved["raw_value"], "size": resolved["size"], "priority": resolved["priority"], "mapping_status": resolved["mapping_status"]})
    if common_size is not None:
        evidence.append({"endpoint": "GROUP", "source": COMMON_DETAIL, "raw_value": common_raw, "size": common_size, "priority": "COMMON_SOW_DETAIL", "mapping_status": _mapping_status(row, COMMON_DETAIL) or None})
    return {"status": status, "ne_size": ne["size"], "fe_size": fe["size"], "selected_size": selected_size, "ne_source": ne["source"], "fe_source": fe["source"], "group_source": group_source, "common_size": common_size, "evidence": evidence}