#!/usr/bin/env python3
"""
DRY RUN: 5 TSS PR CANDIDATES
Generated: May 15, 2026

Display the 5 candidates identified for TSS PR generation with all relevant details.
"""

import pandas as pd

# Load site data
site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'
df_site = pd.read_excel(site_file, sheet_name='data', header=3)

# Filter TSS candidates
tss_candidates = df_site[
    (df_site['SubCon - TSS Team'].notna()) & 
    (df_site['SubCon - TSS Team'].astype(str).str.strip() != '')
].copy().reset_index(drop=True)

# Extract first 5
candidates_5 = tss_candidates.head(5)[
    ['customer site code', 'customer site name', 'region', 'du code', 
     'Tx SOW', 'SubCon - TSS Team']
].copy()

# Rename for clarity
candidates_5.columns = ['Site ID', 'Site Name', 'Region', 'DU Code', 'Tx SOW', 'SubCon - TSS Team']

print("\n" + "="*140)
print("DRY RUN: 5 TSS PR CANDIDATES")
print("="*140)

print("\nFull Details:\n")
for idx in range(len(candidates_5)):
    print(f"\n[CANDIDATE {idx+1}]")
    print("-" * 80)
    for col in candidates_5.columns:
        value = candidates_5.iloc[idx][col]
        print(f"  {col:.<30} {value}")

print("\n\n" + "="*140)
print("SUMMARY TABLE")
print("="*140 + "\n")

# Create display table
display_df = candidates_5.copy()
display_df.insert(0, '#', range(1, len(display_df)+1))

# Format for display
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

print(display_df.to_string(index=False))

print("\n\n" + "="*140)
print("GROUPING BY REGION + SUBCONTRACTOR")
print("="*140 + "\n")

# Group by Region and SubCon
grouped = candidates_5.groupby(['Region', 'SubCon - TSS Team'])

for (region, subcon), group in grouped:
    print(f"\n📁 {region} - {subcon}")
    print(f"   File: {region}-{subcon} TX Mini Project TSS PR 20260515.xls")
    print(f"   Candidates: {', '.join(group['Site ID'].tolist())}")
    print(f"   Count: {len(group)}")

print("\n\n" + "="*140)
print("EXPECTED OUTPUT FILES")
print("="*140 + "\n")

files_expected = []
for (region, subcon), group in grouped:
    file_name = f"{region}-{subcon} TX Mini Project TSS PR 20260515.xls"
    files_expected.append((file_name, len(group), group['Site ID'].tolist()))

for i, (file_name, count, sites) in enumerate(files_expected, 1):
    print(f"{i}. {file_name}")
    print(f"   Lines: ~{count} PR records (depending on mandatory items per SOW)")
    print(f"   Sites: {', '.join(sites)}")
    print()

print("="*140)
print(f"TOTAL: {len(files_expected)} files, {len(candidates_5)} candidates")
print("="*140 + "\n")
