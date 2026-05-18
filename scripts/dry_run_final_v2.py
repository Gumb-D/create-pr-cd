import pandas as pd
from datetime import datetime

print("=" * 100)
print("DRY RUN: 5 TSS PR GENERATION")
print("=" * 100)
print(f"Execution Date: {datetime.now().strftime('%Y-%m-%d')}")

# Load site data with row 3 as headers
site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'
df_site = pd.read_excel(site_file, sheet_name='data', header=3)

print(f"\n[STEP 1] Loaded {len(df_site)} site records")
print(f"  Columns: {len(df_site.columns)}")

# Identify TSS candidates
print(f"\n[STEP 2] Identifying TSS PR Candidates...")
print("  Criteria: SubCon - TSS Team is not blank")

tss_candidates = df_site[
    (df_site['SubCon - TSS Team'].notna()) & 
    (df_site['SubCon - TSS Team'].astype(str).str.strip() != '')
].copy().reset_index(drop=True)

print(f"  ✓ Found {len(tss_candidates)} candidates")

# Load PR Model
print(f"\n[STEP 3] Loading PR Model Reference...")
pr_file = 'Info/Celcomdigi TX PR Model & Line Item 20250416 Rev 2.0.xlsx'
pr_df = pd.read_excel(pr_file, sheet_name='TX Line Item (After 21-Apr 26)', header=None, nrows=50)
print(f"  ✓ PR model loaded")

# Load sample for reference
print(f"\n[STEP 4] Loading Sample TSS PR Output...")
sample_file = 'Info/Northern-GCI TX Mini Project TSS PR 20260515.xls'
sample_df = pd.read_excel(sample_file, sheet_name='details')
print(f"  ✓ Sample has {len(sample_df)} PR lines")

# Extract first 5 TSS candidates
print(f"\n" + "=" * 100)
print(f"5 TSS PR CANDIDATES FOR DRY RUN")
print(f"=" * 100)

candidates_5 = tss_candidates.head(5).copy()
output_rows = []

for idx, (row_num, row_data) in enumerate(candidates_5.iterrows(), 1):
    site_id = row_data.get('customer site code', 'N/A')
    site_name = row_data.get('customer site name', 'N/A')
    region = row_data.get('region', 'N/A')
    du_code = row_data.get('du code', 'N/A')
    tx_sow = row_data.get('Tx SOW', 'N/A')
    subcon_tss = row_data.get('SubCon - TSS Team', 'N/A')
    
    print(f"\n[{idx}] TSS PR Candidate")
    print(f"  Site ID: {site_id}")
    print(f"  Site Name: {site_name}")
    print(f"  Region: {region}")
    print(f"  DU Code: {du_code}")
    print(f"  TX SOW: {tx_sow}")
    print(f"  SubCon - TSS Team: {subcon_tss}")
    
    # Prepare output row
    out_row = {
        'Candidate #': idx,
        'Site ID': site_id,
        'Site Name': site_name,
        'Region': region,
        'DU Code': du_code,
        'Tx SOW': tx_sow,
        'SubCon - TSS Team': subcon_tss,
        'Status': 'Ready for PR generation'
    }
    output_rows.append(out_row)

# Generate summary table
print(f"\n\n" + "=" * 100)
print(f"SUMMARY TABLE: 5 TSS PR CANDIDATES")
print(f"=" * 100)

summary_df = pd.DataFrame(output_rows)
print("\n" + summary_df.to_string(index=False))

# Expected output structure
print(f"\n\n" + "=" * 100)
print(f"EXPECTED OUTPUT (ECC Format)")
print(f"=" * 100)

print(f"""
For each of the 5 candidates, generate ECC output:

ECC Output Columns Required:
  1. SN. (serial number)
  2. Purchasing Area* (from contract infor sheet by subcontractor)
  3. Region* (from site data)
  4. Site ID* (from site data)
  5. Site Name* (from site data)
  6. Delivery Unit Code* (from site data)
  7. Logical Site Name
  8. Contract Number * (from contract infor sheet by subcontractor)
  9. Subcontractor* (TSS Team name)
  10. PBOM Code* (from PR model by matching Tx SOW)
  11. SOW* (from PR model)
  12. Unit* (from PR model)
  13. Quantity* (always 1 for TSS)
  14. Remarks (empty if normal, else "REVIEW_REQUIRED: reason")

Sample Output Structure (from Northern-GCI file):
""")

print(sample_df[['Region*', 'Site ID*', 'Subcontractor*', 'PBOM Code*', 'SOW*', 'Unit*', 'Quantity*']].head(3).to_string())

# Processing steps
print(f"\n\n" + "=" * 100)
print(f"PROCESSING STEPS FOR 5 TSS PR GENERATION")
print(f"=" * 100)

steps = """
Step 1: For each of 5 candidates
  - Extract: Site ID, Site Name, Region, DU Code, Tx SOW, SubCon - TSS Team ✓

Step 2: Match SOW to TSS PR Model
  - Read PR Model sheet "TX Line Item (After 21-Apr 26)"
  - Find TSS section (antenna size NOT required)
  - Match Tx SOW against TSS model rows
  - Retrieve PBOM Code and SOW description

Step 3: Get Contract Information
  - Read contract infor sheet from PR Model file OR sample file
  - Match by Subcontractor name (normalize spaces)
  - Retrieve: Contract Number, Purchasing Area

Step 4: Extract Mandatory Line Items
  - For matched TSS model, select ONLY mandatory line items
  - Quantity = 1 per site per line item
  - If multiple line items: create multiple ECC rows for same site

Step 5: Build ECC Row
  - Populate all 14 mandatory columns per row
  - Add "REVIEW_REQUIRED" remarks if unable to match or missing data
  - Keep remarks blank for normal cases

Step 6: Group and Save
  - Group output rows by: Region + Subcontractor
  - Create file: <Region>-<Subcon> TX Mini Project TSS PR 20260515.xls
  - Add 'details' sheet with PR lines
  - Add 'contract infor' sheet with reference data

Step 7: Generate Processing Summary
  - Output file name
  - Total lines generated
  - Regions and subcontractors included
  - Any REVIEW_REQUIRED issues
"""

print(steps)

# Next actions
print(f"\n" + "=" * 100)
print(f"NEXT STEP REQUIRED")
print(f"=" * 100)

print("""
To complete the dry run, need:

1. PR Model Data Mapping
   - TSS SOW values and their corresponding PBOM codes
   - Which line items are "mandatory" for each SOW
   
2. Contract Information
   - Mapping of Subcontractor → Contract Number, Purchasing Area
   - Current sample shows: GCI, GTSB, CCSMY, Datasco, others
   
3. Confirmation on Output Format
   - File naming: <Region>-<Subcon> TX Mini Project TSS PR 20260515.xls
   - Group all 5 candidates or separate by Region/Subcon?

Ready to proceed with full implementation once clarified.
""")

print("=" * 100)
