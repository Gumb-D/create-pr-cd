import pandas as pd
import os

# 自动定位项目根目录（支持从 scripts/ 或根目录运行）
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) == 'scripts':
    project_root = os.path.dirname(script_dir)
else:
    project_root = script_dir
pr_model_path = os.path.join(project_root, 'Info', 'input', 'pr_model.xlsx')

df_pr = pd.read_excel(pr_model_path, sheet_name="TX Line Item (After 21-Apr 26)", header=None)

print("Checking MW Swap TSS items:\n")
for idx in range(7, len(df_pr)):
    sow = df_pr.iloc[idx, 0]
    if pd.isna(sow) or str(sow).strip() == '':
        break
    if 'MW Swap' in str(sow):
        pbom = df_pr.iloc[idx, 1]
        desc = df_pr.iloc[idx, 2]
        unit = df_pr.iloc[idx, 3]
        qty = df_pr.iloc[idx, 4]
        rules = df_pr.iloc[idx, 5]
        print(f"SOW: {sow}")
        print(f"  PBOM: {pbom}")
        print(f"  Desc: {desc}")
        print(f"  Unit: {unit}")
        print(f"  Quantity: {qty}")
        print(f"  Rules: {rules}")
        print()
