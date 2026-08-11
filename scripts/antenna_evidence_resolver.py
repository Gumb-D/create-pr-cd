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
_INSTALL_INTENT_RE = r"(?:install(?:ation|ed|ing)?|new|target|proposed|replacement|build|upgrade)"
_NON_INSTALL_INTENT_RE = (
    r"(?:dismantl(?:e|ed|ing)?|decom(?:mission(?:ed|ing)?)?|remove|removed|removal|"
    r"existing|old|reuse|reused|retain|retained)"
)
_ACTION_INTENT_RE = rf"(?:{_INSTALL_INTENT_RE}|{_NON_INSTALL_INTENT_RE})"
_INSTALL_INTENT_PATTERN = re.compile(rf"\b{_INSTALL_INTENT_RE}\b", re.IGNORECASE)
_NON_INSTALL_INTENT_PATTERN = re.compile(rf"\b{_NON_INSTALL_INTENT_RE}\b", re.IGNORECASE)
_SOURCE_SIDE_INTENT_PATTERN = re.compile(
    rf"\b(?:upgrade|replac(?:e|ed|ing|ement)?|swap(?:ped|ping)?|chang(?:e|ed|ing)?|"
    rf"migrat(?:e|ed|ing|ion)?|{_NON_INSTALL_INTENT_RE})\b",
    re.IGNORECASE,
)

_TARGET_MODIFIER_RE = r"(?:(?:new|target|proposed|replacement)\s+)?"
_METRE_SUFFIX_RE = r"(?:\s*m(?:eters?|etres?)?\b)?"
_FORWARD_ANTENNA_SIZE_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}(?:antenna|dish)\b\s*"
    rf"(?:(?:(?:with|of)\s+)?(?:size|diameter)\b\s*[:=]?\s*)?"
    rf"\d+(?:[.,]\d+)?{_METRE_SUFFIX_RE}"
)
_REVERSE_ANTENNA_SIZE_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}\d+(?:[.,]\d+)?{_METRE_SUFFIX_RE}\s+(?:antenna|dish)\b"
)
_ANTENNA_SIZE_TARGET_RE = (
    rf"(?:{_FORWARD_ANTENNA_SIZE_TARGET_RE}|{_REVERSE_ANTENNA_SIZE_TARGET_RE})"
)

# Generic reverse target detection is intentionally broader than accepted size
# grammar. It exists only to identify the old/source side of a directional
# change. Invalid explicit units therefore suppress the old size and fail closed
# rather than falling back to an existing antenna PBOM.
_GENERIC_REVERSE_ANTENNA_TARGET_RE = (
    rf"{_TARGET_MODIFIER_RE}\d+(?:[.,]\d+)?"
    rf"(?:\s*(?:(?:[-–—/:|]\s*)|(?:[\(\[]\s*))?(?:[A-Za-z]+|[\"′″]))?"
    rf"\s+(?:antenna|dish)\b"
)

# Generic directional transition is used to identify the source side even when
# the following antenna phrase is invalid as a size target (for example a height
# statement or a reverse target with an unsupported unit). The strict separator
# below remains responsible for deciding whether the target itself is usable.
_DIRECTIONAL_ANTENNA_TRANSITION_RE = (
    rf"\b(?:with|by|to)\b(?=\s+(?:"
    rf"{_TARGET_MODIFIER_RE}(?:antenna|dish)\b|{_GENERIC_REVERSE_ANTENNA_TARGET_RE}))"
)
_DIRECTIONAL_ANTENNA_TRANSITION_PATTERN = re.compile(
    _DIRECTIONAL_ANTENNA_TRANSITION_RE,
    re.IGNORECASE,
)

# Strict directional separator is shared by forward and reverse accepted target
# grammar. This keeps source/target binding aligned with the same size forms the
# candidate parser accepts.
_DIRECTIONAL_ANTENNA_SEPARATOR_RE = (
    rf"\b(?:with|by|to)\b(?=\s+{_ANTENNA_SIZE_TARGET_RE})"
)
_DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN = re.compile(
    _DIRECTIONAL_ANTENNA_SEPARATOR_RE,
    re.IGNORECASE,
)

# All action-aware punctuation uses the same action vocabulary as the intent
# resolver. Colon, slash, pipe and dashes split only when they introduce a real
# action; therefore `antenna size: 0.6m` remains one valid size phrase.
_CLAUSE_SEPARATOR_PATTERN = re.compile(
    rf"(?:[;,\n&]|\.(?=\s|$)|\b(?:and|then)\b|"
    rf"(?:[:/|]|[-–—])(?=\s*{_ACTION_INTENT_RE}\b)|{_DIRECTIONAL_ANTENNA_SEPARATOR_RE})",
    re.IGNORECASE,
)

_EXPLICIT_NON_METRE_UNIT_SUFFIX_PATTERN = re.compile(
    r"\s*(?:(?:[-–—/:|]\s*)|(?:[\(\[]\s*))?(?:[A-Za-z]|[\"′″])",
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
    status_field = _SOURCE_STATUS_FIELDS[source_field]
    return str(row.get(status_field, "") or "").strip().upper()


def _source_is_approved(row: Mapping[str, Any], source_field: str) -> bool:
    """Require APPROVED mappings in canonical mode; preserve legacy direct CLI inputs."""
    if not _canonical_governance_enabled(row):
        return True
    return _mapping_status(row, source_field) == "APPROVED"


def _parse_direct_size(value: Any) -> float | None:
    """Parse a dedicated antenna-size field while ignoring radio-rate numbers."""
    if _is_blank(value):
        return None
    text = str(value).strip().replace(",", ".")
    candidates: list[float] = []

    # Dedicated fields commonly contain `0.6`, `0.6m`, `0.6 meter/metre`, or
    # compact strings such as `18G_1.2M(MAC)`. Values above 5m are rejected.
    for match in re.finditer(
        r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)(?=\s*(?:m(?:eters?|etres?)?\b|$|[_/;,)]))",
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
    """Return action-clause bounds around one candidate size token."""
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


def _intent_clause(text: str, start: int, end: int) -> tuple[str, int]:
    """Return the local action clause containing one candidate size token."""
    clause_start, clause_end = _clause_bounds(text, start, end)
    return text[clause_start:clause_end], clause_start


def _is_directional_target_clause(text: str, clause_start: int) -> bool:
    """Return True when this clause begins immediately after an explicit sized antenna target."""
    return any(
        match.end() == clause_start
        for match in _DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN.finditer(text)
    )


def _candidate_is_antenna_size_phrase(text: str, start: int, end: int) -> bool:
    """Bind one numeric token to an antenna/dish size expression, not a nearby measurement."""
    left = text[max(0, start - 72):start]
    right = text[end:min(len(text), end + 40)]

    # Forward forms: `antenna 0.6m`, `dish size 1.2`,
    # `antenna with size: 0.6m`, `antenna diameter 1.2m`.
    if re.search(
        r"\b(?:antenna|dish)\b\s*(?:(?:(?:with|of)\s+)?(?:size|diameter)\b\s*[:=]?\s*)?$",
        left,
        re.IGNORECASE,
    ):
        return True

    # Reverse forms: `0.6m antenna` / `1.2 metre dish`. For metre-suffixed
    # candidates `end` already includes the unit, while bare decimals may have
    # a unit immediately after the numeric token.
    reverse = right
    unit = re.match(r"\s*m(?:eters?|etres?)?\b", reverse, re.IGNORECASE)
    if unit:
        reverse = reverse[unit.end():]
    return re.match(r"\s*(?:antenna|dish)\b", reverse, re.IGNORECASE) is not None


def _has_source_side_transition(text: str, start: int, end: int, clause_start: int, clause_end: int) -> bool:
    """Reject an old/source antenna size before a directional antenna transition."""
    for transition in _DIRECTIONAL_ANTENNA_TRANSITION_PATTERN.finditer(text):
        if transition.start() < end:
            continue
        if transition.start() > clause_end:
            break
        source_phrase = text[clause_start:transition.start()]
        return _SOURCE_SIDE_INTENT_PATTERN.search(source_phrase) is not None
    return False


def _has_installation_intent(text: str, start: int, end: int) -> bool:
    """Accept only sizes governed by an installation/new/target action."""
    clause_start, clause_end = _clause_bounds(text, start, end)
    clause = text[clause_start:clause_end]
    token_center = ((start + end) / 2) - clause_start

    if clause_end < len(text) and _DIRECTIONAL_ANTENNA_SEPARATOR_PATTERN.match(text, clause_end):
        return False
    if _has_source_side_transition(text, start, end, clause_start, clause_end):
        return False
    if _is_directional_target_clause(text, clause_start):
        return True

    positive = list(_INSTALL_INTENT_PATTERN.finditer(clause))
    if not positive:
        return False
    negative = list(_NON_INSTALL_INTENT_PATTERN.finditer(clause))

    nearest_positive = min(
        abs(((match.start() + match.end()) / 2) - token_center)
        for match in positive
    )
    if not negative:
        return True
    nearest_negative = min(
        abs(((match.start() + match.end()) / 2) - token_center)
        for match in negative
    )
    return nearest_positive < nearest_negative


def _has_antenna_specific_context(text: str, start: int, end: int) -> bool:
    """Require both antenna-size syntax and installation/target intent."""
    if not _candidate_is_antenna_size_phrase(text, start, end):
        return False
    if not _has_installation_intent(text, start, end):
        return False

    suffix = text[end:min(len(text), end + 16)].casefold()
    if re.match(r"\s*(?:ghz|mhz|mbps|gbps|kbps)\b", suffix):
        return False
    return True


def _parse_detail_sizes(value: Any, *, require_antenna_context: bool) -> list[float]:
    """Extract supported installation antenna sizes from governed SOW details."""
    if _is_blank(value):
        return []
    # Convert only decimal commas; preserve ordinary comma punctuation so it
    # remains an intent-clause boundary.
    text = re.sub(r"(?<=\d),(?=\d)", ".", str(value))
    candidates: list[float] = []
    consumed: list[tuple[int, int]] = []

    for match in re.finditer(
        r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*m(?:eters?|etres?)?\b",
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

    # Bare decimals are accepted only when they form an explicit antenna-size
    # phrase. Supported metre spellings are consumed above. Any remaining
    # alphabetic or quote-style unit suffix, including a unit introduced by
    # punctuation or brackets, fails closed instead of being treated as metres.
    for match in re.finditer(r"(?<![\d.])(\d+\.\d+)(?!\d)(?!\.\d)", text):
        if any(consumed_start <= match.start() < consumed_end for consumed_start, consumed_end in consumed):
            continue
        suffix = text[match.end():min(len(text), match.end() + 24)]
        if _EXPLICIT_NON_METRE_UNIT_SUFFIX_PATTERN.match(suffix):
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


def _endpoint_resolution(
    row: Mapping[str, Any],
    direct_field: str,
    detail_field: str,
) -> dict[str, Any]:
    direct_raw = row.get(direct_field, "")
    if _source_is_approved(row, direct_field):
        direct_size = _parse_direct_size(direct_raw)
        if direct_size is not None:
            return {
                "size": direct_size,
                "source": direct_field,
                "raw_value": direct_raw,
                "priority": "DIRECT",
                "mapping_status": _mapping_status(row, direct_field) or None,
            }

    detail_raw = row.get(detail_field, "")
    if _source_is_approved(row, detail_field):
        # SOW-detail fields are free text. Even though endpoint-specific, they
        # must prove antenna installation intent so old/dismantle/cable values
        # cannot select the installation PBOM.
        detail_sizes = _parse_detail_sizes(detail_raw, require_antenna_context=True)
        if detail_sizes:
            return {
                "size": max(detail_sizes),
                "source": detail_field,
                "raw_value": detail_raw,
                "priority": "ENDPOINT_SOW_DETAIL",
                "mapping_status": _mapping_status(row, detail_field) or None,
            }
    return {
        "size": None,
        "source": None,
        "raw_value": None,
        "priority": None,
        "mapping_status": None,
    }


def resolve_installation_antenna_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve NE/FE installation evidence and one governed PR-model group size.

    Canonical rows consume only APPROVED mappings. Legacy direct-generator rows
    have no governance marker and retain their historical direct-field contract.
    SOW-detail fallbacks remain fail-closed unless the value is both antenna-
    specific and governed by installation intent.
    """
    ne = _endpoint_resolution(row, DIRECT_NE, DETAIL_NE)
    fe = _endpoint_resolution(row, DIRECT_FE, DETAIL_FE)
    endpoint_sizes = [value for value in (ne["size"], fe["size"]) if value is not None]

    common_raw = row.get(COMMON_DETAIL, "")
    common_sizes: list[float] = []
    if _source_is_approved(row, COMMON_DETAIL):
        common_sizes = _parse_detail_sizes(common_raw, require_antenna_context=True)
    common_size = max(common_sizes) if common_sizes else None

    if ne["size"] is not None and fe["size"] is not None:
        status = "RESOLVED"
        selected_size = max(endpoint_sizes)
        group_source = "ENDPOINT_EVIDENCE"
    elif common_size is not None:
        status = "RESOLVED_COMMON"
        selected_size = max(endpoint_sizes + [common_size])
        group_source = COMMON_DETAIL if not endpoint_sizes else "ENDPOINT_AND_TX_SOW_DETAILS"
    elif endpoint_sizes:
        status = "INCOMPLETE"
        selected_size = max(endpoint_sizes)
        group_source = "INCOMPLETE_ENDPOINT_EVIDENCE"
    else:
        status = "MISSING"
        selected_size = None
        group_source = None

    evidence = []
    for endpoint, resolved in (("NE", ne), ("FE", fe)):
        if resolved["size"] is not None:
            evidence.append(
                {
                    "endpoint": endpoint,
                    "source": resolved["source"],
                    "raw_value": resolved["raw_value"],
                    "size": resolved["size"],
                    "priority": resolved["priority"],
                    "mapping_status": resolved["mapping_status"],
                }
            )
    if common_size is not None:
        evidence.append(
            {
                "endpoint": "GROUP",
                "source": COMMON_DETAIL,
                "raw_value": common_raw,
                "size": common_size,
                "priority": "COMMON_SOW_DETAIL",
                "mapping_status": _mapping_status(row, COMMON_DETAIL) or None,
            }
        )

    return {
        "status": status,
        "ne_size": ne["size"],
        "fe_size": fe["size"],
        "selected_size": selected_size,
        "ne_source": ne["source"],
        "fe_source": fe["source"],
        "group_source": group_source,
        "common_size": common_size,
        "evidence": evidence,
    }
