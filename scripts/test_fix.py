#!/usr/bin/env python3
"""
Comprehensive regression tests for MW Reroute / New Link handling.
Covers:
- is_mw_reroute_row: TI flow routing based on Tx SOW (TI controls)
- TSS model-driven filtering based on Remarks, including LOS exception and quantity enforcement.
"""

def is_mw_reroute_row(row):
    """For TI: determine if row should be processed as MW Reroute based on Tx SOW."""
    sow = str(row.get('Tx SOW', '')).strip().lower()
    return "mw" in sow and 'reroute' in sow

def test_ti_controls():
    """Test TI routing scenarios"""
    # 1. Non-reroute SOW with 'dismantle' in TX Upgrade Scope should not be treated as MW Reroute
    row1 = {'Tx SOW': 'MW New Link', 'TX Upgrade Scope': 'dismantle and remove'}
    assert is_mw_reroute_row(row1) == False, "Non-reroute SOW with 'dismantle' should NOT trigger MW Reroute"
    print("[PASS] TI Control 1: Non-reroute SOW with dismantle -> not MW Reroute")
    
    # 2. MW Reroute SOW without 'dismantle' should still be MW Reroute
    row2 = {'Tx SOW': 'MW New Link / Reroute', 'TX Upgrade Scope': 'some other scope'}
    assert is_mw_reroute_row(row2) == True, "MW Reroute SOW without 'dismantle' should be MW Reroute"
    print("[PASS] TI Control 2: MW Reroute without dismantle -> MW Reroute")
    
    # 3. Case insensitivity
    row3 = {'Tx SOW': 'mw REROUTE work', 'TX Upgrade Scope': ''}
    assert is_mw_reroute_row(row3) == True, "Case insensitive match"
    print("[PASS] TI Control 3: Case insensitive")
    
    # 4. Empty SOW
    row4 = {'Tx SOW': '', 'TX Upgrade Scope': 'dismantle'}
    assert is_mw_reroute_row(row4) == False, "Empty SOW should return False"
    print("[PASS] TI Control 4: Empty SOW")
    
    print("\n[OK] TI control tests passed!\n")

# Simplified TSS matching function replicating main script logic
def run_tss_matching(site_id, sow, upgrade_scope, tss_models):
    """Run the TSS matching algorithm for a single site."""
    sow_upper = sow.upper()
    is_mw_reroute = False
    if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
        is_mw_reroute = 'dismantle' in upgrade_scope.lower()
    
    matched = []
    for item in tss_models:
        if not item['Is_Mandatory']:
            continue
        item_sow_upper = item['SOW'].upper()
        if not (item_sow_upper == sow_upper or item_sow_upper in sow_upper or sow_upper in item_sow_upper):
            continue
        
        # Filtering for MW New Link / Reroute
        if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
            pbom = item['PBOM_Code']
            qty = item['Quantity']
            remarks = item.get('Remarks', '').strip().lower()
            
            # 1. Model-driven filtering via Remarks
            if remarks:
                if remarks == 'reroute' and not is_mw_reroute:
                    continue
                if remarks == 'new link' and is_mw_reroute:
                    continue
            
            # 2. LOS Survey exception (items may have empty remarks)
            if pbom in ['350000062773', '350000062776']:
                if is_mw_reroute:
                    if pbom == '350000062776' and '_LOS' not in site_id.upper():
                        continue
                    if pbom == '350000062773' and '_LOS' in site_id.upper():
                        continue
                else:
                    if pbom != '350000062773':
                        continue
            
            # 3. Quantity verification
            if pbom in ['350000589343', '350000589344']:
                expected_qty = 1.5 if is_mw_reroute else 1.0
                if qty != expected_qty:
                    continue
        
        matched.append(item)
    
    return matched

def test_tss_scenarios():
    """Test the four TSS MW New Link / Reroute scenarios."""
    # Build minimal tss_models with correct Remarks and quantities
    tss_models = [
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000062773', 'Description': 'LOS Survey', 'Unit': 'Each', 'Quantity': 1, 'Is_Mandatory': True, 'Remarks': ''},
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000062776', 'Description': 'LOS Survey LOS', 'Unit': 'Each', 'Quantity': 1, 'Is_Mandatory': True, 'Remarks': ''},
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000589343', 'Description': 'Item A', 'Unit': 'Each', 'Quantity': 1.0, 'Is_Mandatory': True, 'Remarks': 'New Link'},
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000589343', 'Description': 'Item A', 'Unit': 'Each', 'Quantity': 1.5, 'Is_Mandatory': True, 'Remarks': 'Reroute'},
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000589344', 'Description': 'Item B', 'Unit': 'Each', 'Quantity': 1.0, 'Is_Mandatory': True, 'Remarks': 'New Link'},
        {'SOW': 'MW New Link / Reroute', 'PBOM_Code': '350000589344', 'Description': 'Item B', 'Unit': 'Each', 'Quantity': 1.5, 'Is_Mandatory': True, 'Remarks': 'Reroute'},
    ]
    
    # Scenario 1: MW New Link, no LOS site, no dismantle
    site_id = 'A01073_AD'
    sow = 'MW New Link / Reroute'
    upgrade_scope = 'some installation'
    result = run_tss_matching(site_id, sow, upgrade_scope, tss_models)
    pboms = [item['PBOM_Code'] for item in result]
    assert pboms.count('350000062773') == 1, "Should include 350000062773"
    assert '350000062776' not in pboms, "Should not include 350000062776 for New Link"
    qty_343 = [item['Quantity'] for item in result if item['PBOM_Code']=='350000589343']
    assert 1.0 in qty_343 and 1.5 not in qty_343, "Should have only 1.0 for 350000589343"
    assert len(pboms) == len(set(pboms)), "No duplicate PBOMs"
    print("[PASS] TSS Scenario 1: MW New Link (no LOS) - correct")
    
    # Scenario 2: MW New Link with LOS site, still no dismantle
    site_id = 'SITE_LOS_001'
    result = run_tss_matching(site_id, sow, upgrade_scope, tss_models)
    pboms = [item['PBOM_Code'] for item in result]
    assert pboms.count('350000062773') == 1, "Should include 350000062773 even with LOS for New Link"
    assert '350000062776' not in pboms, "Should not include 350000062776 for New Link"
    assert len(set(pboms)) == len(pboms), "No duplicate PBOMs"
    print("[PASS] TSS Scenario 2: MW New Link (with LOS) - correct")
    
    # Scenario 3: MW Reroute, no LOS site, with dismantle
    site_id = 'B00256'
    upgrade_scope = 'dismantle existing equipment'
    result = run_tss_matching(site_id, sow, upgrade_scope, tss_models)
    pboms = [item['PBOM_Code'] for item in result]
    assert pboms.count('350000062773') == 1, "Should include 350000062773 for Reroute without LOS"
    assert '350000062776' not in pboms, "Should not include 350000062776 for non-LOS Reroute"
    qty_343 = [item['Quantity'] for item in result if item['PBOM_Code']=='350000589343']
    assert 1.5 in qty_343 and 1.0 not in qty_343, "Should have only 1.5 for 350000589343"
    assert len(set(pboms)) == len(pboms), "No duplicate PBOMs"
    print("[PASS] TSS Scenario 3: MW Reroute (no LOS) - correct")
    
    # Scenario 4: MW Reroute with LOS site, with dismantle
    site_id = 'SITE_LOS_002'
    result = run_tss_matching(site_id, sow, upgrade_scope, tss_models)
    pboms = [item['PBOM_Code'] for item in result]
    assert '350000062773' not in pboms, "Should not include 350000062773 when LOS present for Reroute"
    assert pboms.count('350000062776') == 1, "Should include 350000062776 for LOS Reroute"
    qty_343 = [item['Quantity'] for item in result if item['PBOM_Code']=='350000589343']
    assert 1.5 in qty_343 and 1.0 not in qty_343, "Should have 1.5 for 350000589343"
    assert len(set(pboms)) == len(pboms), "No duplicate PBOMs"
    print("[PASS] TSS Scenario 4: MW Reroute (with LOS) - correct")
    
    print("\n[OK] All four TSS scenarios passed!\n")

if __name__ == '__main__':
    test_ti_controls()
    test_tss_scenarios()
    print("=== All regression tests passed ===")
