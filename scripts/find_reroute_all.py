import pandas as pd
import os

df_pr = # Auto-detect project root (support running from scripts/ or project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) == 'scripts':
    project_root = os.path.dirname(script_dir)
else:
    project_root = script_dir
pr_model_path = os.path.join(project_root, 'Info', 'input', 'pr_model.xlsx')
df_pr = pd.read_excel(pr_model_path, sheet_name="TX Line Item (After 21-Apr 26)", header=None)

# Search entire sheet for any cell containing "REROUTE" or "Reroute" (case insensitive)
print("Searching for any MW Reroute items in the entire PR model sheet:")
print()
for idx in range(len(df_pr)):
    for col in range(len(df_pr.columns)):
        cell = df_pr.iloc[idx, col]
        if isinstance(cell, str) and ('REROUTE' in cell.upper() or 'REROUTE' in cell.upper()):
            sow = df_pr.iloc[idx, 0]
            pbom = df_pr.iloc[idx, 1] if 1 < len(df_pr.columns) else ''
            desc = df_pr.iloc[idx, 2] if 2 < len(df_pr.columns) else ''
            qty = df_pr.iloc[idx, 4] if 4 < len(df_pr.columns) else ''
            print(f"Row {idx+1}: SOW='{sow}' | PBOM='{pbom}' | Qty={qty}")
            print()
