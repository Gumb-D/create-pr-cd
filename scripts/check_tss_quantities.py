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

print("=== TSS Items with Quantity 1.5 ===")
for idx in range(7, len(df_pr)):
    sow = df_pr.iloc[idx, 0]
    if pd.isna(sow) or str(sow).strip() == '':
        break
    qty = df_pr.iloc[idx, 4]
    if qty == 1.5:
        pbom = df_pr.iloc[idx, 1]
        desc = df_pr.iloc[idx, 2]
        print(f"Row {idx+1}: SOW='{sow}' | PBOM='{pbom}' | Qty={qty}")
        print(f"  Desc: {desc}")
        print()

print("\n=== TSS Items with other quantities (for comparison) ===")
for idx in range(7, len(df_pr)):
    sow = df_pr.iloc[idx, 0]
    if pd.isna(sow) or str(sow).strip() == '':
        break
    qty = df_pr.iloc[idx, 4]
    if qty != 1.5 and qty != '' and not pd.isna(qty):
        pbom = df_pr.iloc[idx, 1]
        print(f"Row {idx+1}: SOW='{sow}' | PBOM='{pbom}' | Qty={qty}")
