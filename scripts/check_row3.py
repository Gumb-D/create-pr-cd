import pandas as pd

site_file = 'Info/A-P202202168750_D002-TX Mini Project-Mira\'s PR_PO View-20260511141147.xlsx'
df = pd.read_excel(site_file, sheet_name='data', header=None, nrows=6)

print("Row 3 (field names - index 3):")
for i, val in enumerate(df.iloc[3, :50]):
    print(f"  Col {i}: {val}")
