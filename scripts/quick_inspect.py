import pandas as pd

# Inspect site data
site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'

# Read without header to see raw structure
df = pd.read_excel(site_file, sheet_name='data', header=None, nrows=5)

print("SITE DATA RAW STRUCTURE (first 5 rows):")
print("\nColumn count:", len(df.columns))
print("\nFirst 20 columns, all 5 rows:")
print(df.iloc[:, :20])

print("\n\nColumn labels (Row 0 and Row 1):")
for i in range(min(30, len(df.columns))):
    print(f"Col {i}: Row0='{df.iloc[0, i]}' | Row1='{df.iloc[1, i]}'")
