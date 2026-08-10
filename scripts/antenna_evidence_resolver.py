"""Deterministic antenna-installation evidence resolution for TI PR selection.

Direct canonical antenna fields remain authoritative. Endpoint SOW details are
allowed only as fallback evidence, followed by the existing common TX SOW
Details source when it contains explicit installation/antenna-size evidence.
No site, region, subcontractor, or default-size inference is permitted.
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

_INSTALL_KEYWORDS = (
    "antenna",
    "install",
    "installation",
    "new",
    "target",
    "build",
    "upgrade",
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


def _parse_direct_size(value: Any) -> float | None:
    """Parse a dedicated antenna-size field while ignoring radio-rate numbers."""
    if _is_blank(value):
        return None
    text = str(value).strip().replace(",", ".")
    candidates: list[float] = []

    # Dedicated fields commonly contain `0.6`, `0.6m`, or strings such as
    # `18G_1.2M(MAC)`. Values above 5m are never valid antenna diameters here.
    for match in re.finditer(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)(?=\s*(?:m\b|$|[_/;,)]))", text, re.IGNORECASE):
        try:
            candidates.append(float(match.group(1)))
        except ValueError:
            continue
    supported = _unique_sorted(candidates)
    return max(supported) if supported else None


def _context_window(text: str, start: int, end: int, radius: int = 80) -> str:
    return text[max(0, start - radius):min(len(text), end + radius)].casefold()


def _parse_detail_sizes(value: Any) -> list[float]:
    """Extract explicit antenna sizes from governed SOW-detail evidence only."""
    if _is_blank(value):
        return []
    text = str(value).replace(",", ".")
    candidates: list[float] = []

    # Explicit metre suffix is strong enough evidence by itself.
    consumed: list[tuple[int, int]] = []
    for match in re.finditer(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*m\b", text, re.IGNORECASE):
        try:
            size = float(match.group(1))
        except ValueError:
            continue
        if _supported_size(size):
            candidates.append(size)
            consumed.append((match.start(), match.end()))

    # Bare decimal sizes are accepted only near installation/antenna language.
    for match in re.finditer(r"(?<![A-Za-z0-9])(\d+\.\d+)(?![A-Za-z0-9])", text):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        window = _context_window(text, match.start(), match.end())
        if not any(keyword in window for keyword in _INSTALL_KEYWORDS):
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
    direct_size = _parse_direct_size(direct_raw)
    if direct_size is not None:
        return {
            "size": direct_size,
            "source": direct_field,
            "raw_value": direct_raw,
            "priority": "DIRECT",
        }

    detail_raw = row.get(detail_field, "")
    detail_sizes = _parse_detail_sizes(detail_raw)
    if detail_sizes:
        return {
            "size": max(detail_sizes),
            "source": detail_field,
            "raw_value": detail_raw,
            "priority": "ENDPOINT_SOW_DETAIL",
        }
    return {"size": None, "source": None, "raw_value": None, "priority": None}


def resolve_installation_antenna_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve NE/FE installation size evidence and one governed group size.

    Status meanings:
    - RESOLVED: both endpoint sizes resolve from direct/endpoint detail evidence.
    - RESOLVED_COMMON: endpoint evidence is incomplete, but governed common
      `TX SOW Details` contains explicit antenna installation size evidence.
    - INCOMPLETE: exactly one endpoint resolves and no common fallback exists.
    - MISSING: no supported evidence resolves.
    """
    ne = _endpoint_resolution(row, DIRECT_NE, DETAIL_NE)
    fe = _endpoint_resolution(row, DIRECT_FE, DETAIL_FE)
    endpoint_sizes = [value for value in (ne["size"], fe["size"]) if value is not None]

    common_raw = row.get(COMMON_DETAIL, "")
    common_sizes = _parse_detail_sizes(common_raw)
    common_size = max(common_sizes) if common_sizes else None

    if ne["size"] is not None and fe["size"] is not None:
        status = "RESOLVED"
        selected_size = max(endpoint_sizes)
        group_source = "ENDPOINT_EVIDENCE"
    elif common_size is not None:
        status = "RESOLVED_COMMON"
        selected_size = common_size
        group_source = COMMON_DETAIL
        # The existing PR model needs one choose-group category. A common
        # governed detail size is group evidence, not invented endpoint data.
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
