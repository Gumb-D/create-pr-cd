#!/usr/bin/env python3
"""
Production-ready helper functions for PR generation logic.
These functions are imported by both generate_tss_pr_ecc.py and unit tests.
"""

from decimal import Decimal, InvalidOperation
import math
import numbers
import re
from typing import Dict, List, Tuple, Optional, Any


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
        remarks = item.get('Remarks', '').strip().lower()

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
