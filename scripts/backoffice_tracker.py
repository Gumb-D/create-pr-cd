"""Operation Backoffice external tracker domain rules for Issue #94."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


class BackofficeTrackerError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


_TRACKER_SOW_EVENTS = {
    "cd consolidation 2023-mocn": "CD_CONSOLIDATION_MOCN",
    "cd consolidation 2023-decom": "CD_CONSOLIDATION_DECOM",
    "2023 tx rollout": "TX_ROLLOUT_INTEGRATION",
    "2023 tx rollout-decom": "TX_ROLLOUT_DECOM",
    "tx mini project": "TX_MINI_INTEGRATION",
    "2023 celcomdigi bau": "BAU_2023_CUTOVER",
    "2024 celcomdigi bau": "BAU_2024_CUTOVER",
    "celcomdigi usp": "USP_CUTOVER",
    "jendela tx migration": "JENDELA_CUTOVER",
    "mw eos swap": "MW_EOS_INTEGRATION",
    "zte tx mini": "ZTE_TX_MINI_INTEGRATION",
}
_DATE_RE = re.compile(r"(?<!\d)(20\d{6})(?!\d)")
_BACKOFFICE_BILLING_MONTH_RE = re.compile(r"\bBackoffice\s+(?:MAIN|SUPPLEMENTARY)\s+(20\d{2}-(?:0[1-9]|1[0-2]))\s+PR\b", re.IGNORECASE)


@dataclass(frozen=True)
class TrackerIndex:
    duplicate_keys: frozenset[tuple[str, str]]
    rows_by_key: Mapping[tuple[str, str], Mapping[str, object]]
    month_pbom: Mapping[str, str]
    month_entitlement_keys: Mapping[str, frozenset[tuple[str, str]]] = field(default_factory=dict)


_REQUIRED_TRACKER_COLUMNS = {"Delivery Unit Code", "SOW", "PBOM Code", "File Name"}

def read_tracker_rows(path: Path) -> list[dict[str, object]]:
    path = Path(path)
    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    try:
        frame = pd.read_excel(path, sheet_name="TX Outsource Details", engine=engine, dtype=object)
    except Exception as error:
        raise BackofficeTrackerError("BACKOFFICE_TRACKER_UNREADABLE", f"Cannot read TX Outsource Details from {path}: {error}") from error
    missing = sorted(_REQUIRED_TRACKER_COLUMNS - set(str(c) for c in frame.columns))
    if missing:
        raise BackofficeTrackerError("BACKOFFICE_TRACKER_REQUIRED_COLUMNS_MISSING", "Missing tracker columns: " + ", ".join(missing))
    return frame.to_dict(orient="records")

def _text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"nan", "<na>", "none"} else " ".join(text.split())


def _pbom(value: object) -> str:
    text = _text(value)
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text


def canonical_event_from_tracker_sow(sow: object) -> str | None:
    return _TRACKER_SOW_EVENTS.get(_text(sow).casefold())


def duplicate_key(delivery_unit_code: object, event_code: object) -> tuple[str, str]:
    du = _text(delivery_unit_code).upper()
    event = _text(event_code).upper()
    if not du or not event:
        raise BackofficeTrackerError("BACKOFFICE_TRACKER_IDENTITY_MISSING", "Delivery Unit Code and canonical event are required.")
    return du, event


def issue_date_from_filename(file_name: object) -> date | None:
    match = _DATE_RE.search(_text(file_name))
    if not match:
        return None
    raw = match.group(1)
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:
        return None


def billing_month_from_filename(file_name: object) -> str | None:
    text = _text(file_name)
    explicit = _BACKOFFICE_BILLING_MONTH_RE.search(text)
    if explicit:
        return explicit.group(1)
    issued = issue_date_from_filename(text)
    if issued is None:
        return None
    year, month = issued.year, issued.month - 1
    if month == 0:
        year, month = year - 1, 12
    return f"{year:04d}-{month:02d}"


def build_tracker_index(rows: Iterable[Mapping[str, object]]) -> TrackerIndex:
    by_key: dict[tuple[str, str], Mapping[str, object]] = {}
    month_rows: dict[str, list[tuple[date, str]]] = {}
    month_entitlement_keys: dict[str, set[tuple[str, str]]] = {}
    for row in rows:
        du = row.get("Delivery Unit Code")
        sow = row.get("SOW")
        if not _text(du) and not _text(sow):
            continue
        event = canonical_event_from_tracker_sow(sow)
        if event is None:
            raise BackofficeTrackerError("BACKOFFICE_TRACKER_SOW_UNMAPPED", f"Tracker SOW is not mapped to a canonical Backoffice event: {_text(sow)}")
        key = duplicate_key(du, event)
        pbom = _pbom(row.get("PBOM Code"))
        file_name = row.get("File Name")
        issued = issue_date_from_filename(file_name)
        month = billing_month_from_filename(file_name)
        if not pbom:
            raise BackofficeTrackerError("BACKOFFICE_TRACKER_PBOM_MISSING", f"PBOM Code is missing for {key}.")
        if issued is None or month is None:
            raise BackofficeTrackerError("BACKOFFICE_TRACKER_ISSUE_DATE_MISSING", f"File Name does not contain a valid issue date for {key}.")
        if key in by_key:
            prior = by_key[key]
            prior_pbom = _pbom(prior.get("PBOM Code"))
            prior_file = _text(prior.get("File Name"))
            if prior_pbom != pbom or prior_file != _text(file_name):
                raise BackofficeTrackerError("BACKOFFICE_TRACKER_DUPLICATE_IDENTITY_AMBIGUOUS", f"Tracker contains conflicting history for {key}.")
            continue
        by_key[key] = dict(row)
        month_rows.setdefault(month, []).append((issued, pbom))
        month_entitlement_keys.setdefault(month, set()).add(key)

    month_pbom: dict[str, str] = {}
    for month, values in month_rows.items():
        first_date = min(item[0] for item in values)
        first_pboms = {pbom for issued, pbom in values if issued == first_date}
        if len(first_pboms) != 1:
            raise BackofficeTrackerError("BACKOFFICE_TRACKER_MONTH_PBOM_AMBIGUOUS", f"More than one PBOM appears on the first issue date for {month}.")
        month_pbom[month] = next(iter(first_pboms))
    return TrackerIndex(
        frozenset(by_key),
        by_key,
        month_pbom,
        {month: frozenset(keys) for month, keys in month_entitlement_keys.items()},
    )


def frozen_pbom_for_month(index: TrackerIndex, billing_month: str) -> str | None:
    return index.month_pbom.get(str(billing_month))


def load_backoffice_tracker(path: Path) -> TrackerIndex:
    """Load the authoritative TX Outsource Details sheet into a governed snapshot."""
    return build_tracker_index(read_tracker_rows(Path(path)))
