import pandas as pd
import json
from datetime import datetime

print("=" * 100)
print("DRY RUN: 5 TSS PR GENERATION ANALYSIS")
print("=" * 100)
print(f"\nExecution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Load site data with proper multi-level headers
site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'

print("\n[STEP 1] Loading Site Data...")
df_raw = pd.read_excel(site_file, sheet_name='data', header=[1, 2], nrows=5)  # Use rows 1-2 as headers
print(f"✓ Column structure detected: {len(df_raw.columns)} columns")

# Read again with row 2 as reference for mapping
df_all = pd.read_excel(site_file, sheet_name='data', header=None)
row_labels = df_all.iloc[2, :].tolist()  # Row 2 = field names like 'customer site code', 'Tx SOW', etc.

print(f"\nField names identified from Row 2:")
for i, label in enumerate(row_labels[:40]):
    if label and label not in ['nan', 'NaN', None]:
        print(f"  Col {i}: {label}")

# Find columns we need
col_mapping = {}
for i, label in enumerate(row_labels):
    if label is None or str(label).lower() == 'nan':
        continue
    label_str = str(label).lower()
    
    # Map to standard field names
    if 'customer site code' in label_str or 'site id' in label_str:
        col_mapping['Site ID'] = i
    elif 'site name' in label_str:
        col_mapping['Site Name'] = i
    elif 'region' in label_str:
        col_mapping['Region'] = i
    elif 'tx sow' in label_str:
        col_mapping['Tx SOW'] = i
    elif 'du code' in label_str or 'delivery unit' in label_str:
        col_mapping['DU Code'] = i
    elif 'tss team' in label_str or 'subcon - tss' in label_str:
        col_mapping['SubCon - TSS Team'] = i
    elif 'ti team' in label_str or 'subcon - ti' in label_str:
        col_mapping['SubCon - TI Team'] = i
    elif 'planning' in label_str and 'subcon' in label_str:
        col_mapping['SubCon - Planning'] = i
    elif 'antenna size ne' in label_str:
        col_mapping['MW Config Antenna Size NE'] = i
    elif 'antenna size fe' in label_str:
        col_mapping['MW Config Antenna Size FE'] = i
    elif 'actual end date' in label_str:
        col_mapping['TX Integrated actual end date'] = i

print(f"\n✓ Identified {len(col_mapping)} key columns:")
for key, col_idx in sorted(col_mapping.items()):
    print(f"  {key}: Column {col_idx}")

# Extract the data rows (skip header rows 0-2)
print("\n[STEP 2] Extracting Site Data Rows...")
data_rows = df_all.iloc[3:, :].copy()
print(f"✓ Total data rows: {len(data_rows)}")

# Build a cleaner dataframe
extracted_data = {}
for field_name, col_idx in col_mapping.items():
    extracted_data[field_name] = data_rows.iloc[:, col_idx].tolist()

df_sites = pd.DataFrame(extracted_data)

# Filter for TSS candidates
print("\n[STEP 3] Identifying TSS PR Candidates...")
print("Filter criteria:")
print("  - SubCon - TSS Team is not blank")
print("  - No existing TSS PR (would check PR status column if available)")

# Find non-empty SubCon - TSS Team rows
tss_candidates = df_sites[
    (df_sites['SubCon - TSS Team'].notna()) & 
    (df_sites['SubCon - TSS Team'].astype(str).str.strip() != '') &
    (df_sites['SubCon - TSS Team'].astype(str).str.lower() != 'nan')
].copy()

print(f"\n✓ Found {len(tss_candidates)} TSS PR candidates")

# Show first 5
print("\n[STEP 4] First 5 TSS PR Candidates:")
print("=" * 100)

for idx, (i, row) in enumerate(tss_candidates.head(5).iterrows(), 1):
    site_id = row.get('Site ID', 'N/A')
    site_name = row.get('Site Name', 'N/A')
    region = row.get('Region', 'N/A')
    tx_sow = row.get('Tx SOW', 'N/A')
    subcon = row.get('SubCon - TSS Team', 'N/A')
    
    print(f"\n[CANDIDATE {idx}]")
    print(f"  Site ID: {site_id}")
    print(f"  Site Name: {site_name}")
    print(f"  Region: {region}")
    print(f"  Tx SOW: {tx_sow}")
    print(f"  SubCon - TSS Team: {subcon}")
    print(f"  DU Code: {row.get('DU Code', 'N/A')}")

# Load PR Model for TSS matching
print("\n\n[STEP 5] Loading PR Model Reference...")
pr_file = 'Info/Celcomdigi TX PR Model & Line Item 20250416 Rev 2.0.xlsx'
try:
    pr_df = pd.read_excel(pr_file, sheet_name='TX Line Item (After 21-Apr 26)', header=None)
    print(f"✓ PR model loaded: {len(pr_df)} rows")
    
    # Find data start (first non-empty row)
    for idx in range(len(pr_df)):
        if pr_df.iloc[idx].notna().sum() > 5:
            print(f"\nData starts at row {idx}")
            print(f"Headers: {pr_df.iloc[idx, :10].tolist()}")
            break
except Exception as e:
    print(f"✗ Error loading PR model: {e}")

# Load sample output for reference
print("\n\n[STEP 6] Sample TSS PR Output Structure...")
sample_file = 'Info/Northern-GCI TX Mini Project TSS PR 20260515.xls'
sample_df = pd.read_excel(sample_file, sheet_name='details')
sample_contract = pd.read_excel(sample_file, sheet_name='contract infor', header=None)

print(f"✓ Sample output structure:")
print(f"  - Details sheet: {sample_df.shape[0]} rows, {len(sample_df.columns)} columns")
print(f"  - Columns: {list(sample_df.columns)}")
print(f"\nSample TSS PR lines:")
print(sample_df[['Purchasing Area*', 'Region*', 'Site ID*', 'Subcontractor*', 'PBOM Code*', 'SOW*']].to_string())

print(f"\n\n  - Contract infor sheet:")
print(sample_contract.iloc[1:6, :].to_string())

# Summary
print("\n\n" + "=" * 100)
print("DRY RUN SUMMARY")
print("=" * 100)

summary = f"""
Input Data Analysis:
  Total sites in database: 2,556
  TSS PR candidates identified: {len(tss_candidates)}
  Sample candidates to process: 5

Processing Steps for 5 TSS PR:
  1. Extract Site IDs, Names, Regions, SOW, SubCon for 5 candidates ✓
  2. Match each SOW against PR Model (TSS section)
  3. Retrieve mandatory line items for matched model
  4. Get contract number from 'contract infor' sheet
  5. Build ECC output rows with mandatory fields:
     - Purchasing Area (from contract info)
     - Region (from site data)
     - Site ID, Site Name (from site data)
     - DU Code (from site data)
     - Contract Number (from contract info)
     - Subcontractor: TSS team name (from site data)
     - PBOM Code (from PR model)
     - SOW (from PR model)
     - Unit (from PR model)
     - Quantity: 1 (per TSS rule)
  6. Group by Region + Subcontractor
  7. Generate output file: <Region>-<Subcon> TX Mini Project TSS PR 20260515.xls

Expected Output Format:
  - File: Northern-XXX TX Mini Project TSS PR 20260515.xls
  - Details sheet: 5+ rows (PR lines)
  - Contract infor sheet: Reference data
  
Next Steps:
  1. Request full PR Model Reference mapping (TSS SOW → PBOM codes)
  2. Implement SOW matching logic
  3. Extract mandatory line items
  4. Generate 5 PR lines in ECC format
"""

print(summary)

# Export candidate data for next step
print("\nCandidate export:")
export_cols = ['Site ID', 'Site Name', 'Region', 'DU Code', 'Tx SOW', 'SubCon - TSS Team']
print(tss_candidates[export_cols].head(5).to_string())

print("\n" + "=" * 100)
