import pandas as pd
import os

files = [
    'output/outputs/Central-GTSB TX Mini Project TSS PR 20260518.xls',
    'output/outputs/Northern-GCI TX Mini Project TSS PR 20260518.xls',
    'output/outputs/Northern-GTSB TX Mini Project TSS PR 20260518.xls',
    'output/outputs/Sabah-Seri Pancar TX Mini Project TSS PR 20260518.xls'
]

print('\n' + '=' * 100)
print('VALIDATION CHECKS FOR AMENDMENTS 1-3')
print('=' * 100)

# Check 1-2
print('\n[CHECK 1-2] Single Sheet Named "details":')
for fname in files:
    book = load_workbook(fname)
    sheets = book.sheetnames
    ok = len(sheets) == 1 and sheets[0] == 'details'
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} {sheets}')

# Check 3
print('\n[CHECK 3] Sequential SN (1-based):')
for fname in files:
    book = load_workbook(fname)
    sheet = book.active
    sns = [int(sheet.cell(i, 1).value) for i in range(2, sheet.max_row + 1)]
    expected = list(range(1, len(sns) + 1))
    ok = sns == expected
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} {sns}')

# Check 4
print('\n[CHECK 4] Purchasing Area from Region:')
region_map = {'Northern': 'Malaysia_South North Region', 'Central': 'Malaysia_Central Region', 'Sabah': 'Malaysia_East Malaysia'}
for fname in files:
    book = load_workbook(fname)
    sheet = book.active
    bad = 0
    for i in range(2, sheet.max_row + 1):
        region = sheet.cell(i, 3).value
        purch = sheet.cell(i, 2).value
        if purch != region_map.get(region):
            bad += 1
    ok = bad == 0
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} Issues: {bad}')

# Check 5-6
print('\n[CHECK 5-6] Column 8 = Column 16 (Contract Numbers):')
for fname in files:
    book = load_workbook(fname)
    sheet = book.active
    bad = 0
    for i in range(2, sheet.max_row + 1):
        c8 = sheet.cell(i, 8).value
        c16 = sheet.cell(i, 16).value
        if c8 != c16:
            bad += 1
    ok = bad == 0
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} Mismatches: {bad}')

# Check 7
print('\n[CHECK 7] Max 30 Unique Sites:')
for fname in files:
    book = load_workbook(fname)
    sheet = book.active
    sites = set([sheet.cell(i, 4).value for i in range(2, sheet.max_row + 1)])
    ok = len(sites) <= 30
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} Count: {len(sites)}')

# Check 8
print('\n[CHECK 8] File Naming (<Region>-<Subcon> ... TSS PR YYYYMMDD):')
for fname in files:
    basename = fname.split("/")[-1]
    ok = 'TSS PR 20260518' in basename and 'Part' not in basename
    print(f'  {basename:<55} {"✓" if ok else "✗"}')

# Check 9
print('\n[CHECK 9] Contract from Subcontractor Mapping:')
subcon_map = {'GTSB': 'S1MY2024071003WBF1', 'GCI': 'S1MY2024071002WBF1', 'Seri Pancar': 'S1MY2024071011WBF1'}
for fname in files:
    book = load_workbook(fname)
    sheet = book.active
    bad = 0
    for i in range(2, sheet.max_row + 1):
        subcon = sheet.cell(i, 9).value
        cn = sheet.cell(i, 8).value
        expected = subcon_map.get(subcon, 'UNKNOWN')
        if cn != expected:
            bad += 1
    ok = bad == 0
    print(f'  {fname.split("/")[-1]:<55} {"✓" if ok else "✗"} Issues: {bad}')

print('\n' + '=' * 100)
