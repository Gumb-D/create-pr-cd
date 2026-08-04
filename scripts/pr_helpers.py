#!/usr/bin/env python3
"""
Production-ready helper functions for PR generation logic.
These functions are imported by both generate_tss_pr_ecc.py and unit tests.
"""

from decimal import Decimal, InvalidOperation
import math
import numbers
import re
from typing import Dict, List, Tuple, Optional, Any, Iterable


PR_MODEL_SHEET_NAME = "TX Line Item (After 21-Apr 26)"


def load_pr_model_items(path: Any) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load TSS and every valid TI model row, including named sections after blank separators."""
    import pandas as pd

    dataframe = pd.read_excel(path, sheet_name=PR_MODEL_SHEET_NAME, header=None)

    tss_models: List[Dict[str, Any]] = []
    for index in range(7, len(dataframe)):
        sow = dataframe.iloc[index, 0]
        if pd.isna(sow) or not str(sow).strip():
            break
        pbom = dataframe.iloc[index, 1]
        description = dataframe.iloc[index, 2]
        if pd.notna(pbom) and pd.notna(description):
            rules = dataframe.iloc[index, 5]
            remarks = dataframe.iloc[index, 6] if len(dataframe.columns) > 6 else None
            tss_models.append(
                {
                    "SOW": str(sow).strip(),
                    "PBOM_Code": normalize_pbom_code(pbom),
                    "Description": str(description).strip(),
                    "Unit": str(dataframe.iloc[index, 3]).strip() if pd.notna(dataframe.iloc[index, 3]) else "Hop",
                    "Quantity": float(dataframe.iloc[index, 4]) if pd.notna(dataframe.iloc[index, 4]) else 1,
                    "Is_Mandatory": "Mandatory" in str(rules) if pd.notna(rules) else False,
                    "Remarks": str(remarks).strip() if pd.notna(remarks) else "",
                }
            )

    ti_header_index = next(
        (
            index
            for index in range(len(dataframe))
            if isinstance(dataframe.iloc[index, 0], str) and "TI Model" in dataframe.iloc[index, 0]
        ),
        None,
    )
    ti_models: List[Dict[str, Any]] = []
    if ti_header_index is None:
        return tss_models, ti_models

    for index in range(ti_header_index + 1, len(dataframe)):
        sow = dataframe.iloc[index, 0]
        pbom = dataframe.iloc[index, 1]
        description = dataframe.iloc[index, 2]
        if pd.isna(sow) or not str(sow).strip() or pd.isna(pbom) or pd.isna(description):
            continue
        if str(pbom).strip().casefold() == "code":
            continue
        rules = dataframe.iloc[index, 5]
        ti_models.append(
            {
                "SOW": str(sow).strip(),
                "PBOM_Code": normalize_pbom_code(pbom),
                "Description": str(description).strip(),
                "Unit": str(dataframe.iloc[index, 3]).strip() if pd.notna(dataframe.iloc[index, 3]) else "Hop",
                "Quantity": float(dataframe.iloc[index, 4]) if pd.notna(dataframe.iloc[index, 4]) else 1,
                "Is_Mandatory": "Mandatory" in str(rules) if pd.notna(rules) else False,
                "Rules": str(rules).strip() if pd.notna(rules) else "",
            }
        )

    return tss_models, ti_models


def optional_cell_text(value: Any) -> str:
    """Return trimmed text while treating spreadsheet numeric NaN as blank."""
    if value is None:
        return ""
    if isinstance(value, numbers.Real) and math.isnan(float(value)):
        return ""
    return str(value).strip()


def normalize_pbom_code(value: Any) -> str:
    """
    Normalize PBOM/material codes into a canonical string form.

    Excel-derived numeric cells can surface as floats such as 350000062773.0.
    This helper strips only the numeric formatting artifact while preserving
    legitimate non-numeric codes unchanged.
    """
    if value is None:
        return ''

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() == 'nan':
            return ''
        candidate = stripped
    elif isinstance(value, numbers.Integral):
        return str(int(value))
    elif isinstance(value, numbers.Real):
        if math.isnan(value) or not math.isfinite(value):
            return ''
        candidate = str(value)
    else:
        candidate = str(value).strip()
        if not candidate or candidate.lower() == 'nan':
            return ''

    try:
        decimal_value = Decimal(candidate)
    except InvalidOperation:
        return candidate

    if not decimal_value.is_finite():
        return ''

    if decimal_value == decimal_value.to_integral_value():
        return format(decimal_value.quantize(Decimal('1')), 'f')

    return format(decimal_value.normalize(), 'f')


def normalize_ti_sow(value: Any) -> str:
    """
    Normalize TI SOW text into a canonical uppercase form.

    Matching intentionally allows only exact canonical equality with harmless
    case and whitespace variation. Blank, NaN-like, and invalid values
    normalize to an empty string.
    """
    if value is None:
        return ''

    if isinstance(value, str):
        candidate = value.strip()
    elif isinstance(value, numbers.Real):
        if math.isnan(value) or not math.isfinite(value):
            return ''
        candidate = str(value).strip()
    else:
        candidate = str(value).strip()

    if not candidate or candidate.lower() in {'nan', '<na>'}:
        return ''

    return ' '.join(candidate.split()).upper()


def _normalize_ti_sow_alias_map(alias_map: Optional[Dict[str, Iterable[str]]]) -> Dict[str, set[str]]:
    normalized: Dict[str, set[str]] = {}
    if not alias_map:
        return normalized

    for raw_input, raw_aliases in alias_map.items():
        normalized_input = normalize_ti_sow(raw_input)
        if not normalized_input:
            continue
        aliases = {
            alias
            for alias in (normalize_ti_sow(value) for value in raw_aliases)
            if alias
        }
        if aliases:
            normalized[normalized_input] = aliases

    return normalized


def validate_required_pbom_selection(
    matched_items: List[Dict[str, Any]], required_codes: Iterable[Any]
) -> tuple[bool, Optional[str]]:
    """Require every declared PBOM exactly once and reject extra selections."""
    required = [normalize_pbom_code(code) for code in required_codes]
    selected = [normalize_pbom_code(item.get("PBOM_Code")) for item in matched_items]
    if not required:
        return True, None
    if sorted(selected) != sorted(required) or any(selected.count(code) != 1 for code in required):
        return False, "JENDELA_REQUIRED_PBOM_NOT_UNIQUE"
    return True, None


def filter_failed_migration_decisions(
    ecc_rows: List[Dict[str, Any]], failed_decision_ids: Iterable[Any]
) -> List[Dict[str, Any]]:
    """Drop every line belonging to an atomic migration decision that failed."""
    failed = {str(value).strip() for value in failed_decision_ids if str(value).strip()}
    if not failed:
        return list(ecc_rows)
    return [
        row
        for row in ecc_rows
        if str(row.get("Migration_Decision_ID") or "").strip() not in failed
    ]


TI_SOW_ALIAS_MAP: Dict[str, set[str]] = _normalize_ti_sow_alias_map({})


def ti_sow_matches_model(
    input_sow: Any,
    model_sow: Any,
    alias_map: Optional[Dict[str, Iterable[str]]] = None,
) -> bool:
    """
    Return True only when a TI input SOW canonically matches a model SOW.

    Matching is strict exact equality after normalization, with optional
    explicit alias support if real model data ever requires it.
    """
    normalized_input = normalize_ti_sow(input_sow)
    normalized_model = normalize_ti_sow(model_sow)

    if not normalized_input or not normalized_model:
        return False

    if normalized_input == normalized_model:
        return True

    normalized_aliases = TI_SOW_ALIAS_MAP if alias_map is None else _normalize_ti_sow_alias_map(alias_map)
    allowed_aliases = normalized_aliases.get(normalized_input, set())
    return normalized_model in allowed_aliases


def is_mw_reroute_row(row: Dict[str, Any]) -> bool:
    """
    Determine if a TI row should be processed as MW Reroute.
    This function is used by the TI matching logic and checks the Tx SOW field.

    Args:
        row: Dictionary representing a site data row

    Returns:
        True if the row qualifies as MW Reroute based on Tx SOW, False otherwise
    """
    sow = str(row.get('Tx SOW', '')).strip().lower()
    return "mw" in sow and 'reroute' in sow


def parse_mw_new_link_reroute(sow: str, upgrade_scope: str) -> bool:
    """
    For TSS: Determine if a MW New Link / Reroute SOW should be treated as Reroute.

    Args:
        sow: Tx SOW string
        upgrade_scope: TX Upgrade Scope string

    Returns:
        True if this is a reroute (has 'dismantle' in upgrade_scope), False for new link
    """
    sow_upper = sow.upper()
    if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
        return 'dismantle' in upgrade_scope.lower()
    return False


def filter_tss_mw_new_link_reroute_items(
    matched_items: List[Dict[str, Any]],
    is_mw_reroute: bool,
    site_id: str
) -> List[Dict[str, Any]]:
    """
    Apply the MW New Link / Reroute filtering rules to TSS model items.

    Args:
        matched_items: List of initially matched TSS model items
        is_mw_reroute: True if this is a reroute, False if new link
        site_id: Site identifier for LOS detection

    Returns:
        Filtered list of items that should be included
    """
    filtered = []

    for item in matched_items:
        pbom = normalize_pbom_code(item.get('PBOM_Code'))
        qty = item['Quantity']
        remarks = (item.get('Remarks') or '').strip().lower()

        # 1. Model-driven filtering via Remarks
        if remarks:
            if remarks == 'reroute' and not is_mw_reroute:
                continue
            if remarks == 'new link' and is_mw_reroute:
                continue

        # 2. LOS Survey selection exception (items may have empty remarks)
        if pbom in ['350000062773', '350000062776']:
            if is_mw_reroute:
                # Reroute: use 350000062776 for LOS sites, exclude 350000062773 for LOS sites
                if pbom == '350000062776' and '_LOS' not in site_id.upper():
                    continue
                if pbom == '350000062773' and '_LOS' in site_id.upper():
                    continue
            else:
                # New Link: only use 350000062773
                if pbom != '350000062773':
                    continue

        # 3. Quantity verification for specific items
        if pbom in ['350000589343', '350000589344']:
            expected_qty = 1.5 if is_mw_reroute else 1.0
            if qty != expected_qty:
                continue

        filtered.append(item)

    return filtered


def has_duplicate_pbom(items: List[Dict[str, Any]]) -> bool:
    """
    Check if there are duplicate PBOM codes in the item list.

    Args:
        items: List of items to check

    Returns:
        True if any PBOM appears more than once, False otherwise
    """
    pboms = [normalize_pbom_code(item.get('PBOM_Code')) for item in items]
    return len(pboms) != len(set(pboms))


def select_tss_items_for_site(
    site_id: str,
    sow: str,
    upgrade_scope: str,
    tss_models: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Complete TSS item selection for a site, including initial matching and MW filtering.

    Args:
        site_id: Site identifier
        sow: Tx SOW value
        upgrade_scope: TX Upgrade Scope
        tss_models: List of all TSS model items

    Returns:
        List of selected items for this site
    """
    sow_upper = sow.upper()
    is_mw_reroute = parse_mw_new_link_reroute(sow, upgrade_scope)

    # Initial matching
    matched = []
    for item in tss_models:
        if not item['Is_Mandatory']:
            continue
        item_sow_upper = item['SOW'].upper()
        if not (item_sow_upper == sow_upper or item_sow_upper in sow_upper or sow_upper in item_sow_upper):
            continue
        matched.append(item)

    # Apply MW New Link / Reroute filtering if applicable
    if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
        matched = filter_tss_mw_new_link_reroute_items(matched, is_mw_reroute, site_id)

    return matched
