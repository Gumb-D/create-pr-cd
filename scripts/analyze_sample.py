import pandas as pd

# Check the sample PR file using pandas
sample_file = "Info/Northern-GCI TX Mini Project TSS PR 20260515.xls"

print("=" * 80)
print("ANALYZING SAMPLE TSS PR OUTPUT FILE")
print("=" * 80)

try:
    # Read with pandas - it will auto-detect format
    xls = pd.ExcelFile(sample_file)
    print(f"\nAvailable sheets: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(sample_file, sheet_name=sheet_name)
        print(f"\n\nSheet: {sheet_name}")
        print(f"  Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Get headers
        print(f"\n  Column Headers:")
        for i, col in enumerate(df.columns, 1):
            print(f"    {i}. {col}")
        
        # Show first 5 rows
        print(f"\n  First 5 data rows:")
        print(df.head(5).to_string())
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
