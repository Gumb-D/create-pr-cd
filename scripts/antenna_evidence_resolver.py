"""Deterministic antenna-installation evidence resolution for TI PR selection.

Direct canonical antenna fields remain authoritative. Endpoint SOW details are
allowed only as fallback evidence, followed by the common TX SOW Details source
when it contains explicit antenna-size evidence. Canonical production rows must
also prove that every consumed source mapping is APPROVED.
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


def _context_window(text: str, start: int, end: int, radius: int = 48) -> str:
    left_boundary = max(text.rfind(";", 0, start), text.rfind("\n", 0, start))
    right_candidates = [
        value for value in (text.find(";", end), text.find("\n", end)) if value != -1
    ]
    segment_start = 0 if left_boundary == -1 else left_boundary + 1
    segment_end = min(right_candidates) if right_candidates else len(text)
    return text[max(segment_start, start - radius):min(segment_end, end + radius)].casefold()


def _has_antenna_specific_context(text: str, start: int, end: int) -> bool:
    """Tie a numeric token to antenna semantics, not generic install/upgrade text."""
    window = _context_window(text, start, end)
    if not any(word in window for word in _ANTENNA_WORDS):
        return False

    suffix = text[end:min(len(text), end + 16)].casefold()
    if re.match(r"\s*(?:ghz|mhz|mbps|gbps|kbps)\b", suffix):
        return False

    # `antenna cable 3.0m` describes cable length, not dish diameter. Reject
    # when cable is the nearest semantic noun to the numeric token.
    token_center = (start + end) // 2
    lowered = text.casefold()
    antenna_positions = [
        match.start()
        for word in _ANTENNA_WORDS
        for match in re.finditer(rf"\b{re.escape(word)}\b", lowered)
        if abs(match.start() - token_center) <= 48
    ]
    cable_positions = [
        match.start()
        for match in re.finditer(r"\bcable\b", lowered)
        if abs(match.start() - token_center) <= 48
    ]
    if cable_positions and antenna_positions:
        nearest_cable = min(abs(position - token_center) for position in cable_positions)
        nearest_antenna = min(abs(position - token_center) for position in antenna_positions)
        if nearest_cable < nearest_antenna:
            return False
    return True


def _parse_detail_sizes(value: Any, *, require_antenna_context: bool) -> list[float]:
    """Extract supported antenna sizes from governed SOW-detail evidence."""
    if _is_blank(value):
        return []
    text = str(value).replace(",", ".")
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

    # Bare decimals are accepted only when the number itself has antenna-
    # specific context. The guards also prevent partial matches inside IPs.
    for match in re.finditer(r"(?<![\d.])(\d+\.\d+)(?![\d.])", text):
        if any(start <= match.start() < end for start, end in consumed):
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
        # SOW-detail fields are free text. Even though they are endpoint-specific,
        # require antenna/dish context so cable lengths cannot select antenna PBOMs.
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
    SOW-detail fallbacks remain fail-closed unless the value is antenna-specific.
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
