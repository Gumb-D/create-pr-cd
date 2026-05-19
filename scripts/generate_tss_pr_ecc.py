import pandas as pd
import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
import json

print("=" * 100)
print("FULL IMPLEMENTATION: 5 TSS PR ECC FILE GENERATION")
print("=" * 100)
print(f"Execution Date: {datetime.now().strftime('%Y-%m-%d')}\n")

# ===== STEP 1: EXTRACT PR MODEL DATA =====
print("[STEP 1] Extracting PR Model Data...")

pr_file = 'Info/input/pr_model.xlsx'
df_pr = pd.read_excel(pr_file, sheet_name="TX Line Item (After 21-Apr 26)", header=None)

# Extract TSS models (starting from row 7 = index 7)
# Columns: 0=SOW, 1=PBOM Code, 2=Description, 3=Unit, 4=Quantity, 5=Rules
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
    print(f"  - {sow}: {len(sow_groups[sow])} items ({mandatory_count} mandatory)")

# ===== STEP 2: CONTRACT INFORMATION =====
print("\n[STEP 2] Extracting Contract Information...")

sample_file = 'Info/sample/Northern-GCI TX Mini Project TSS PR 20260515.xls'
df_contract = pd.read_excel(sample_file, sheet_name='contract infor', header=None)

# Parse contract info
contracts = {}
for idx in range(1, len(df_contract)):
    row = df_contract.iloc[idx, :]
    region = str(row[2]).strip() if pd.notna(row[2]) else None
    purch_area = str(row[3]).strip() if pd.notna(row[3]) else None
    subcon = str(row[5]).strip() if pd.notna(row[5]) else None
    contract_no = str(row[6]).strip() if pd.notna(row[6]) else None
    
    if subcon and subcon != 'nan' and subcon != '' and contract_no and contract_no != 'nan':
        contracts[subcon] = {
            'Region': region,
            'Purchasing_Area': purch_area,
            'Contract_No': contract_no
        }

print(f"✓ Extracted {len(contracts)} subcontractor mappings:")
for subcon, info in contracts.items():
    print(f"  - {subcon}: {info['Contract_No']} ({info['Purchasing_Area']})")

# ===== STEP 3: LOAD 5 DRY RUN CANDIDATES =====
print("\n[STEP 3] Loading 5 Dry Run Candidates...")

site_file = 'Info/input/site_pr_po_view.xlsx'
df_site = pd.read_excel(site_file, sheet_name='data', header=3)

# Filter TSS candidates
tss_candidates = df_site[
    (df_site['SubCon - TSS Team'].notna()) & 
    (df_site['SubCon - TSS Team'].astype(str).str.strip() != '')
].copy().reset_index(drop=True)

candidates_5 = tss_candidates.head(5).copy()
print(f"✓ Selected 5 candidates")

# ===== STEP 4: BUILD ECC OUTPUT ROWS =====
print("\n[STEP 4] Building ECC Output Rows...")

output_rows = []
sn = 1

for idx, (row_num, site_row) in enumerate(candidates_5.iterrows(), 1):
    site_id = site_row.get('customer site code', 'N/A')
    site_name = site_row.get('customer site name', 'N/A')
    region = site_row.get('region', 'N/A')
    du_code = site_row.get('du code', 'N/A')
    tx_sow = str(site_row.get('Tx SOW', '')).strip()
    subcon_tss = str(site_row.get('SubCon - TSS Team', '')).strip()
    
    print(f"\n  Candidate {idx}: {site_id} - {tx_sow}")
    
    # Find matching SOW in model
    matched_sow = None
    for model_sow in sow_groups.keys():
        if model_sow.upper() in tx_sow.upper():
            matched_sow = model_sow
            break
    
    if not matched_sow:
        print(f"    ⚠ SOW not matched, using closest match")
        # Fuzzy match
        for model_sow in sow_groups.keys():
            if any(word in tx_sow.upper() for word in model_sow.upper().split()):
                matched_sow = model_sow
                break
    
    if not matched_sow:
        # Use first available
        matched_sow = list(sow_groups.keys())[0] if sow_groups else None
    
    if not matched_sow:
        print(f"    ✗ No SOW match found")
        continue
    
    print(f"    ✓ Matched to SOW: {matched_sow}")
    
    # Get mandatory items for this SOW
    mandatory_items = [x for x in sow_groups[matched_sow] if x['Is_Mandatory']]
    print(f"    ✓ Found {len(mandatory_items)} mandatory line items")
    
    # Get contract info
    if subcon_tss in contracts:
        contract_info = contracts[subcon_tss]
        purch_area = contract_info['Purchasing_Area']
        contract_no = contract_info['Contract_No']
    else:
        purch_area = "REVIEW_REQUIRED"
        contract_no = "REVIEW_REQUIRED"
    
    # Create ECC row for each mandatory item
    for item in mandatory_items:
        output_rows.append({
            'SN': sn,
            'Purchasing Area*': purch_area,
            'Region*': region,
            'Site ID*': site_id,
            'Site Name*': site_name,
            'Delivery Unit Code*': du_code,
            'Logical Site Name': '',
            'Contract Number *': contract_no,
            'Subcontractor*': subcon_tss,
            'PBOM Code*': item['PBOM_Code'],
            'SOW*': item['Description'],
            'Unit*': item['Unit'],
            'Quantity*': item['Quantity'],
            'Remarks': ''
        })
        sn += 1

print(f"\n✓ Generated {len(output_rows)} ECC output rows")

# ===== STEP 5: GROUP BY REGION + SUBCON AND CREATE FILES =====
print("\n[STEP 5] Grouping and Creating Output Files...")

# Group output rows
grouped = {}
for row in output_rows:
    key = (row['Region*'], row['Subcontractor*'])
    if key not in grouped:
        grouped[key] = []
    grouped[key].append(row)

print(f"✓ Grouped into {len(grouped)} output files:")

output_files = []

for (region, subcon), rows in grouped.items():
    file_name = f"{region}-{subcon} TX Mini Project TSS PR 20260515.xls"
    print(f"\n  Creating: {file_name}")
    print(f"    - Records: {len(rows)}")
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'details'
    
    # Write headers
    headers = ['SN.', 'Purchasing Area*', 'Region*', 'Site ID*', 'Site Name*', 
               'Delivery Unit Code*', 'Logical Site Name', 'Contract Number *', 
               'Subcontractor*', 'PBOM Code*', 'SOW*', 'Unit*', 'Quantity*', 'Remarks']
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
        cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    # Write data rows
    for row_idx, row_data in enumerate(rows, 2):
        ws.cell(row=row_idx, column=1, value=row_data['SN'])
        ws.cell(row=row_idx, column=2, value=row_data['Purchasing Area*'])
        ws.cell(row=row_idx, column=3, value=row_data['Region*'])
        ws.cell(row=row_idx, column=4, value=row_data['Site ID*'])
        ws.cell(row=row_idx, column=5, value=row_data['Site Name*'])
        ws.cell(row=row_idx, column=6, value=row_data['Delivery Unit Code*'])
        ws.cell(row=row_idx, column=7, value=row_data['Logical Site Name'])
        ws.cell(row=row_idx, column=8, value=row_data['Contract Number *'])
        ws.cell(row=row_idx, column=9, value=row_data['Subcontractor*'])
        ws.cell(row=row_idx, column=10, value=row_data['PBOM Code*'])
        ws.cell(row=row_idx, column=11, value=row_data['SOW*'])
        ws.cell(row=row_idx, column=12, value=row_data['Unit*'])
        ws.cell(row=row_idx, column=13, value=row_data['Quantity*'])
        ws.cell(row=row_idx, column=14, value=row_data['Remarks'])
    
    # Add contract infor sheet
    ws_contract = wb.create_sheet('contract infor')
    ws_contract.cell(row=1, column=2, value='Region*')
    ws_contract.cell(row=1, column=3, value='Purchasing Area*')
    ws_contract.cell(row=1, column=5, value='Subcontractor*')
    ws_contract.cell(row=1, column=6, value='Contract Number *')
    
    # Add contract data
    for r_idx, row_data in enumerate(rows, 2):
        ws_contract.cell(row=r_idx, column=2, value=row_data['Region*'])
        ws_contract.cell(row=r_idx, column=3, value=row_data['Purchasing Area*'])
        ws_contract.cell(row=r_idx, column=5, value=row_data['Subcontractor*'])
        ws_contract.cell(row=r_idx, column=6, value=row_data['Contract Number *'])
    
    # Set column widths
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 18
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 15
    ws.column_dimensions['K'].width = 40
    ws.column_dimensions['L'].width = 8
    ws.column_dimensions['M'].width = 10
    ws.column_dimensions['N'].width = 20
    
    # Save file
    wb.save(file_name)
    output_files.append({
        'File': file_name,
        'Region': region,
        'Subcon': subcon,
        'Records': len(rows),
        'Sites': len(set([r['Site ID*'] for r in rows]))
    })
    print(f"    ✓ Saved")

# ===== STEP 6: GENERATE SUMMARY =====
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

print(f"\n✓ Generated {len(output_files)} TSS PR ECC files:\n")
for file_info in output_files:
    print(f"  {file_info['File']}")
    print(f"    - Region: {file_info['Region']}")
    print(f"    - Subcontractor: {file_info['Subcon']}")
    print(f"    - PR Records: {file_info['Records']}")
    print(f"    - Unique Sites: {file_info['Sites']}")
    print()

# Total summary
total_records = sum([f['Records'] for f in output_files])
total_sites = len(set([r['Site ID*'] for r in output_rows]))

print(f"\nTOTAL:")
print(f"  - Output Files: {len(output_files)}")
print(f"  - Total PR Records: {total_records}")
print(f"  - Total Sites: {total_sites}")

print("\n" + "=" * 100)
print("✓ FILE GENERATION COMPLETE")
print("=" * 100)
