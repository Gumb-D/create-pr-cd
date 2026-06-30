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

print("=== TSS: MW Reroute items ===")
tss_found = False
for idx in range(7, len(df_pr)):
    sow = df_pr.iloc[idx, 0]
    if pd.isna(sow) or str(sow).strip() == '':
        if tss_found:
            break
        continue
    if 'MW REROUTE' in str(sow).upper() or str(sow).strip() == 'MW Reroute':
        tss_found = True
        pbom = df_pr.iloc[idx, 1]
        desc = df_pr.iloc[idx, 2]
        qty = df_pr.iloc[idx, 4]
        rules = df_pr.iloc[idx, 5]
        print(f"SOW: {sow}")
        print(f"  PBOM: {pbom}")
        print(f"  Desc: {desc}")
        print(f"  Qty: {qty}")
        print(f"  Rules: {rules}")
        print()

print("\n=== TI: MW Reroute items ===")
ti_started = False
ti_found = False
for idx in range(len(df_pr)):
    cell = df_pr.iloc[idx, 0]
    if isinstance(cell, str) and 'TI Model' in cell:
        ti_started = True
        continue
    if ti_started:
        sow = df_pr.iloc[idx, 0]
        if pd.isna(sow) or str(sow).strip() == '':
            if ti_found:
                break
            continue
        if 'REROUTE' in str(sow).upper():
            ti_found = True
            pbom = df_pr.iloc[idx, 1]
            desc = df_pr.iloc[idx, 2]
            qty = df_pr.iloc[idx, 4]
            rules = df_pr.iloc[idx, 5]
            print(f"SOW: {sow}")
            print(f"  PBOM: {pbom}")
            print(f"  Desc: {desc}")
            print(f"  Qty: {qty}")
            print(f"  Rules: {rules}")
            print()
