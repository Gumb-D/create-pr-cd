#!/usr/bin/env python3
"""
TSS PR ECC File Generation - Amendment Implementation
Amended version incorporating:
- Amendment 1: Separate contract info reference (Markdown)
- Amendment 2: Single 'details' sheet only
- Amendment 3: Sequential SN, Region→Purchasing Area, Subcon→Contract, 30-site split, fuzzy matching
"""

import pandas as pd
import openpyxl
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from difflib import SequenceMatcher
import re

print("=" * 100)
print("TSS PR ECC GENERATION - AMENDED IMPLEMENTATION")
print("=" * 100)
print(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ===== HELPER FUNCTIONS =====

def load_region_mapping(ref_file):
    """Load Region to Purchasing Area mapping from reference file."""
    mapping = {}
    with open(ref_file, 'r') as f:
        lines = f.readlines()
    in_section = False
    for line in lines:
        if '## Region to Purchasing Area' in line:
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if in_section and '|' in line:
            # Skip header row (contains "Region*") and separator row (contains "---")
            if 'Region*' in line or '---' in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            # parts = ['', region, purchasing_area, '']
            if len(parts) >= 3 and parts[1] and parts[2] and parts[1] != '':
                mapping[parts[1]] = parts[2]
    return mapping

def load_subcon_mapping(ref_file):
    """Load Subcontractor to Contract mapping from reference file."""
    mapping = {}
    with open(ref_file, 'r') as f:
        lines = f.readlines()
    in_section = False
    for line in lines:
        if '## Subcontractor to Contract Number' in line:
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if in_section and '|' in line:
            # Skip header row (contains "Subcontractor*") and separator row (contains "---")
            if 'Subcontractor*' in line or '---' in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            # parts = ['', subcon, contract_number, company_name, '']
            if len(parts) >= 4 and parts[1] and parts[2] and parts[1] != '':
                mapping[parts[1]] = {
                    'contract_number': parts[2],
                    'company_name': parts[3]
                }
    return mapping

def fuzzy_match_subcon(subcon_name, subcon_mapping, threshold=0.6):
    """
    Fuzzy match a subcontractor name against known list.
    Returns matched subcon key or None.
    """
    if subcon_name in subcon_mapping:
        return subcon_name  # Exact match
    
    best_match = None
    best_score = threshold
    
    for known_subcon in subcon_mapping.keys():
        score = SequenceMatcher(None, subcon_name.lower(), known_subcon.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = known_subcon
    
    return best_match

# ===== STEP 0: LOAD REFERENCE DATA =====
print("[STEP 0] Loading Reference Data from Markdown...")

ref_file = 'Info/contract_info_reference.md'
region_mapping = load_region_mapping(ref_file)
subcon_mapping = load_subcon_mapping(ref_file)

print(f"✓ Loaded {len(region_mapping)} region mappings")
print(f"  Regions: {', '.join(sorted(region_mapping.keys()))}")
print(f"✓ Loaded {len(subcon_mapping)} subcontractor mappings")
print(f"  Subcons: {', '.join(sorted(subcon_mapping.keys()))[:80]}...")

# ===== STEP 1: EXTRACT PR MODEL DATA =====
print("\n[STEP 1] Extracting PR Model Data...")

pr_file = 'Info/Celcomdigi TX PR Model & Line Item 20250416 Rev 2.0.xlsx'
df_pr = pd.read_excel(pr_file, sheet_name="TX Line Item (After 21-Apr 26)", header=None)

# Extract TSS models (starting from row 7 = index 7)
tss_models = []

for idx in range(7, len(df_pr)):
    sow = df_pr.iloc[idx, 0]
    pbom = df_pr.iloc[idx, 1]
    desc = df_pr.iloc[idx, 2]
    unit = df_pr.iloc[idx, 3]
    qty = df_pr.iloc[idx, 4]
    rules = df_pr.iloc[idx, 5]
    
    # Stop at next section
    if pd.isna(sow) or str(sow).strip() == '':
        break
    
    # Check if mandatory
    is_mandatory = 'Mandatory' in str(rules) if pd.notna(rules) else False
    
    if pd.notna(pbom) and pd.notna(desc):
        tss_models.append({
            'SOW': str(sow).strip(),
            'PBOM_Code': str(pbom).strip(),
            'Description': str(desc).strip(),
            'Unit': str(unit).strip() if pd.notna(unit) else 'Hop',
            'Quantity': float(qty) if pd.notna(qty) else 1,
            'Is_Mandatory': is_mandatory
        })

print(f"✓ Extracted {len(tss_models)} TSS line items")

# Group by SOW
sow_groups = {}
for item in tss_models:
    sow = item['SOW']
    if sow not in sow_groups:
        sow_groups[sow] = []
    sow_groups[sow].append(item)

print(f"✓ Found {len(sow_groups)} unique TSS SOWs:")
for sow in sorted(sow_groups.keys()):
    mandatory_count = len([x for x in sow_groups[sow] if x['Is_Mandatory']])
    print(f"  - {sow[:50]}: {len(sow_groups[sow])} items ({mandatory_count} mandatory)")

# ===== STEP 2: LOAD SITE DATA =====
print("\n[STEP 2] Loading Site Data...")

site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'
df_site = pd.read_excel(site_file, sheet_name='data', header=3)

# Filter TSS candidates
tss_candidates = df_site[
    (df_site['SubCon - TSS Team'].notna()) & 
    (df_site['SubCon - TSS Team'].astype(str).str.strip() != '')
].copy().reset_index(drop=True)

print(f"✓ Found {len(tss_candidates)} TSS candidates")

# Display first 5 for dry run
print(f"✓ First 5 candidates:")
for i in range(min(5, len(tss_candidates))):
    site_id = tss_candidates.iloc[i]['customer site code']
    site_name = tss_candidates.iloc[i]['customer site name']
    region = tss_candidates.iloc[i]['region']
    subcon = tss_candidates.iloc[i]['SubCon - TSS Team']
    sow = tss_candidates.iloc[i]['Tx SOW']
    print(f"  {i+1}. {site_id} ({site_name}) - Region: {region}, SubCon: {subcon}, SOW: {sow[:40]}")

# ===== STEP 3: BUILD ECC OUTPUT ROWS =====
print("\n[STEP 3] Building ECC Output Rows...")

ecc_rows = []
fuzzy_matches = {}

for idx in range(min(5, len(tss_candidates))):
    row = tss_candidates.iloc[idx]
    
    site_id = str(row['customer site code']).strip()
    site_name = str(row['customer site name']).strip()
    region = str(row['region']).strip()
    subcon = str(row['SubCon - TSS Team']).strip()
    sow = str(row['Tx SOW']).strip()
    delivery_unit = str(row.get('du code', '')).strip() if pd.notna(row.get('du code')) else ''
    logical_site = str(row.get('customer site code', '')).strip() if pd.notna(row.get('customer site code')) else ''
    
    # Get Purchasing Area from Region
    purchasing_area = region_mapping.get(region, f"UNKNOWN ({region})")
    
    # Get Contract Number from Subcontractor (with fuzzy matching)
    matched_subcon = subcon
    if subcon in subcon_mapping:
        contract_info = subcon_mapping[subcon]
    else:
        # Try fuzzy match
        fuzzy_match = fuzzy_match_subcon(subcon, subcon_mapping)
        if fuzzy_match:
            matched_subcon = fuzzy_match
            contract_info = subcon_mapping[fuzzy_match]
            fuzzy_matches[subcon] = fuzzy_match
            print(f"  ⚠ Fuzzy matched '{subcon}' → '{fuzzy_match}'")
        else:
            contract_info = {'contract_number': 'UNKNOWN', 'company_name': 'Unknown'}
            print(f"  ✗ No match for subcontractor: {subcon}")
    
    contract_number = contract_info['contract_number']
    
    # Match SOW to PBOM items (use substring/fuzzy match for variations)
    matched_items = []
    sow_upper = sow.upper()
    for item in tss_models:
        item_sow_upper = item['SOW'].upper()
        # Check for exact match or if sow contains item SOW as substring
        if item['Is_Mandatory'] and (item_sow_upper == sow_upper or item_sow_upper in sow_upper or sow_upper in item_sow_upper):
            matched_items.append(item)
    
    if not matched_items:
        print(f"  ✗ No mandatory items found for SOW: {sow[:50]}")
        continue
    
    # Create one ECC row per mandatory item
    for item in matched_items:
        ecc_row = {
            'Site_ID': site_id,
            'Site_Name': site_name,
            'Region': region,
            'Purchasing_Area': purchasing_area,
            'Subcontractor': matched_subcon,
            'Contract_Number': contract_number,
            'PBOM_Code': item['PBOM_Code'],
            'SOW': item['SOW'],
            'Description': item['Description'],
            'Unit': item['Unit'],
            'Quantity': item['Quantity'],
            'Delivery_Unit_Code': delivery_unit,
            'Logical_Site_Name': logical_site,
            'Remarks': ''
        }
        ecc_rows.append(ecc_row)

print(f"✓ Built {len(ecc_rows)} ECC output rows")

# ===== STEP 4: GROUP BY REGION-SUBCON AND CREATE EXCEL FILES =====
print("\n[STEP 4] Grouping and Creating Excel Files...")

# Group by (Region, Subcontractor)
grouped = {}
for ecc_row in ecc_rows:
    group_key = (ecc_row['Region'], ecc_row['Subcontractor'])
    if group_key not in grouped:
        grouped[group_key] = []
    grouped[group_key].append(ecc_row)

file_count = 0
total_rows = 0

for (region, subcon), rows in sorted(grouped.items()):
    # Check if split needed (max 30 unique sites per file)
    unique_sites = set([r['Site_ID'] for r in rows])
    num_files = (len(unique_sites) + 29) // 30  # Ceiling division
    
    print(f"\n  Group: {region}-{subcon}")
    print(f"    Unique sites: {len(unique_sites)}")
    print(f"    Total rows: {len(rows)}")
    print(f"    Files needed: {num_files}")
    
    # Distribute rows across files
    if num_files == 1:
        # Single file
        parts = [rows]
        file_parts = [1]
    else:
        # Multiple files - split by unique sites
        sites_list = sorted(list(unique_sites))
        parts = []
        file_parts = []
        
        for part_num in range(num_files):
            start_idx = part_num * 30
            end_idx = (part_num + 1) * 30
            part_sites = set(sites_list[start_idx:end_idx])
            part_rows = [r for r in rows if r['Site_ID'] in part_sites]
            parts.append(part_rows)
            file_parts.append(part_num + 1)
    
    # Create Excel file(s)
    for part_rows, part_num in zip(parts, file_parts):
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'details'
        
        # Write headers
        headers = ['SN.', 'Purchasing Area*', 'Region*', 'Site ID*', 'Site Name*', 
                   'Delivery Unit Code*', 'Logical Site Name', 'Contract Number *',
                   'Subcontractor*', 'PBOM Code*', 'SOW*', 'Unit*', 'Quantity*', 
                   'Remarks', '', 'Contract Number']
        
        # Header styling
        header_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        header_font = Font(bold=True)
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(1, col_idx, header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Write data rows with sequential SN
        for sn, ecc_row in enumerate(part_rows, 1):
            row_data = [
                sn,  # SN. - Sequential from 1
                ecc_row['Purchasing_Area'],
                ecc_row['Region'],
                ecc_row['Site_ID'],
                ecc_row['Site_Name'],
                ecc_row['Delivery_Unit_Code'],
                ecc_row['Logical_Site_Name'],
                ecc_row['Contract_Number'],  # Contract Number *
                ecc_row['Subcontractor'],
                ecc_row['PBOM_Code'],
                ecc_row['SOW'],
                ecc_row['Unit'],
                ecc_row['Quantity'],
                ecc_row['Remarks'],
                '',  # Column O (empty)
                ecc_row['Contract_Number']  # Column P - Contract Number (same as *)
            ]
            
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(2 + sn - 1, col_idx, value)
                if col_idx in [1, 13]:  # SN and Quantity - numeric
                    cell.alignment = Alignment(horizontal='center')
        
        # Set column widths
        column_widths = [5, 20, 12, 15, 20, 15, 20, 18, 15, 15, 40, 8, 10, 15, 5, 18]
        for col_idx, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col_idx)].width = width
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        if num_files == 1:
            filename = f"output/outputs/{region}-{subcon} TX Mini Project TSS PR {timestamp}.xls"
        else:
            filename = f"output/outputs/{region}-{subcon} TX Mini Project TSS PR {timestamp} Part {part_num}.xls"
        
        # Save file
        wb.save(filename)
        
        file_count += 1
        total_rows += len(part_rows)
        print(f"    ✓ Created: {filename} ({len(part_rows)} rows)")

# ===== SUMMARY =====
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Total files generated: {file_count}")
print(f"Total ECC rows: {total_rows}")
print(f"Fuzzy matched subcontractors: {len(fuzzy_matches)}")
if fuzzy_matches:
    for original, matched in fuzzy_matches.items():
        print(f"  - '{original}' → '{matched}'")
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
