import pandas as pd

site_file = 'Info/input/site_pr_po_view.xlsx'
df = pd.read_excel(site_file, sheet_name='data', header=None, nrows=6)

print("Row 3 (field names - index 3):")
for i, val in enumerate(df.iloc[3, :50]):
    print(f"  Col {i}: {val}")
