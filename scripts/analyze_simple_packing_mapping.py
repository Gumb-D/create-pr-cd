import os
import json
import csv
import pandas as pd
import sys

def main():
    pr_model_path = os.path.join("Info", "input", "pr_model.xlsx")
    mapping_path = os.path.join("Info", "reference", "geography_mapping.json")
    output_dir = "output_ti_test"
    csv_output_path = os.path.join(output_dir, "simple_packing_pr_model_extract.csv")

    print("=" * 80)
    print("SIMPLE PACKING PR MODEL RESOLUTION ANALYSIS")
    print("=" * 80)

    # Validate file existences
    if not os.path.exists(pr_model_path):
        print(f"FAIL: PR Model not found at {pr_model_path}")
        sys.exit(1)
    if not os.path.exists(mapping_path):
        print(f"FAIL: Geography Mapping reference not found at {mapping_path}")
        sys.exit(1)

    # 1. Load geography mapping reference
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
        sp_ref = mapping_data.get("simple_packing", {})
        sp_mappings = sp_ref.get("mappings", {})
        missing_sp_list = sp_ref.get("missing_simple_packing_data", [])
        print("✓ Loaded Info/reference/geography_mapping.json successfully.")
    except Exception as e:
        print(f"FAIL: Error reading geography_mapping.json: {e}")
        sys.exit(1)

    # 2. Load PR model
    try:
        df_pr = pd.read_excel(pr_model_path, sheet_name="TX Line Item (After 21-Apr 26)", header=None)
        print("✓ Loaded Info/input/pr_model.xlsx successfully.")
    except Exception as e:
        print(f"FAIL: Error reading PR model Excel workbook: {e}")
        sys.exit(1)

    # Find TI Model header
    ti_header_idx = None
    for idx in range(len(df_pr)):
        cell_value = df_pr.iloc[idx, 0]
        if isinstance(cell_value, str) and 'TI Model' in cell_value:
            ti_header_idx = idx
            break

    if ti_header_idx is None:
        print("FAIL: TI Model section header not found in the Excel sheet.")
        sys.exit(1)

    # Extract all Simple Packing rows from TI Model
    extracted_rows = []
    keywords = [
        "Kota Kinabalu", "Sandakan", "Tawau",
        "Kuching", "Sibu", "Bintulu", "Miri", "Limbang", "Lawas", "Sri Aman",
        "Perlis", "Kedah", "Penang", "Perak", "Selangor", "Kuala Lumpur", 
        "Negeri Sembilan", "Malacca", "Melaka", "Johor", "Pahang", "Terengganu", "Kelantan"
    ]

    for idx in range(ti_header_idx + 1, len(df_pr)):
        sow = df_pr.iloc[idx, 0]
        pbom = df_pr.iloc[idx, 1]
        desc = df_pr.iloc[idx, 2]
        unit = df_pr.iloc[idx, 3]
        qty = df_pr.iloc[idx, 4]
        rules = df_pr.iloc[idx, 5]

        if pd.isna(sow) or str(sow).strip() == '':
            break

        sow_str = str(sow).strip() if pd.notna(sow) else ""
        pbom_str = str(pbom).strip() if pd.notna(pbom) else ""
        desc_str = str(desc).strip() if pd.notna(desc) else ""
        rules_str = str(rules).strip() if pd.notna(rules) else ""

        full_text = f"{sow_str} {desc_str} {rules_str}".lower()
        if "simple packing" in full_text:
            # Find all matched keywords
            matched_kws = []
            for kw in keywords:
                if kw.lower() in full_text:
                    matched_kws.append(kw)

            # Normalize keywords to avoid treating Melaka/Malacca as distinct
            normalized_kws = list(set([("Melaka" if k.lower() in ["melaka", "malacca"] else k) for k in matched_kws]))

            inferred_bucket = "Unknown"
            is_suspicious = False
            suspicious_reason = ""

            if len(normalized_kws) == 1:
                inferred_bucket = normalized_kws[0]
            elif len(normalized_kws) > 1:
                # Prioritize Lawas if present
                if "Lawas" in normalized_kws:
                    inferred_bucket = "Lawas"
                # Else prioritize Penang for Penang vs Perak Row 81 case
                elif "Penang" in normalized_kws:
                    inferred_bucket = "Penang"
                else:
                    inferred_bucket = normalized_kws[0]
                
                is_suspicious = True
                suspicious_reason = f"Multiple bucket keywords matched: {normalized_kws}"

            excel_row_num = idx + 1
            extracted_rows.append({
                'excel_row': excel_row_num,
                'inferred_bucket': inferred_bucket,
                'sow': sow_str,
                'pbom_code': pbom_str,
                'description': desc_str,
                'unit': str(unit).strip() if pd.notna(unit) else 'Hop',
                'quantity': float(qty) if pd.notna(qty) else 1.0,
                'rules': rules_str,
                'is_suspicious': is_suspicious,
                'suspicious_reason': suspicious_reason
            })

    print(f"✓ Extracted {len(extracted_rows)} Simple Packing TI PR model rows.")

    # 3. Classify and analyze mapping coverage & duplicates/gaps
    mapped_buckets = set(sp_mappings.keys())
    
    # Group extracted rows by bucket
    extracted_by_bucket = {}
    for r in extracted_rows:
        bucket = r['inferred_bucket']
        extracted_by_bucket.setdefault(bucket, []).append(r)

    # Classification Lists
    repeated_same_pbom = []
    conflicting_bucket_pbom = []
    unknown_bucket = []
    suspicious_bucket_text = []
    lawas_special_cases = []
    missing_from_mapping = []
    mismatches = []
    missing_from_pr = []

    # Track distinct PBOMs per bucket for conflicts & Lawas
    for bucket, rows in extracted_by_bucket.items():
        if bucket == "Unknown":
            unknown_bucket.extend(rows)
            for r in rows:
                r['mapping_status'] = "UNKNOWN_BUCKET"
                r['mapping_material_code'] = "N/A"
                r['issue'] = "GAP: Unable to infer destination bucket."
            continue

        if bucket == "Lawas":
            lawas_special_cases.extend(rows)
            # Find all distinct PBOM codes for Lawas
            distinct_lawas_pboms = set([r['pbom_code'] for r in rows])
            for r in rows:
                r['mapping_status'] = "LAWAS_SPECIAL_HANDLING"
                r['issue'] = f"LAWAS_SPECIAL_HANDLING_REQUIRED: Multiple Lawas PBOMs found in sheet: {list(distinct_lawas_pboms)}"
            continue

        distinct_pboms = set([r['pbom_code'] for r in rows])
        
        if len(distinct_pboms) == 1:
            # Safe repeated or single row
            pbom = list(distinct_pboms)[0]
            if len(rows) > 1:
                repeated_same_pbom.extend(rows)
                for r in rows:
                    r['mapping_status'] = "INFO_REPEATED"
                    r['issue'] = "Harmless repeated row with same PBOM code."
            else:
                for r in rows:
                    r['mapping_status'] = "OK"
                    r['issue'] = "OK"
        elif len(distinct_pboms) > 1:
            # Conflicting PBOM codes for the same bucket!
            conflicting_bucket_pbom.extend(rows)
            for r in rows:
                r['mapping_status'] = "GAP_CONFLICT"
                r['issue'] = f"GAP: Conflicting PBOM codes for bucket '{bucket}': {list(distinct_pboms)}"

    # Check for suspicious bucket texts, missing mappings, and mismatches
    for r in extracted_rows:
        bucket = r['inferred_bucket']
        pbom = r['pbom_code']

        if r['is_suspicious']:
            suspicious_bucket_text.append(r)
            r['mapping_status'] = "WARNING_SUSPICIOUS"
            r['issue'] = f"WARNING: {r['suspicious_reason']}"

        if bucket != "Unknown" and bucket != "Lawas":
            if bucket not in sp_mappings:
                missing_from_mapping.append(r)
                if r['mapping_status'] not in ["GAP_CONFLICT", "WARNING_SUSPICIOUS"]:
                    r['mapping_status'] = "NOT_MAPPED"
                    r['issue'] = "GAP: Inferred bucket is not mapped in geography_mapping.json."
            else:
                ref_material_code = str(sp_mappings[bucket].get("material_code"))
                if ref_material_code != pbom:
                    mismatches.append(r)
                    if r['mapping_status'] not in ["GAP_CONFLICT", "WARNING_SUSPICIOUS"]:
                        r['mapping_status'] = "MISMATCH"
                        r['issue'] = f"Material code mismatch! Excel PBOM={pbom}, Mapping ref={ref_material_code}"

    # Identify mapped buckets not found in PR model
    found_buckets = set(extracted_by_bucket.keys())
    for bucket in mapped_buckets:
        if bucket not in found_buckets:
            missing_from_pr.append({
                'bucket': bucket,
                'mapping_material_code': sp_mappings[bucket].get("material_code"),
                'issue': "Mapped in JSON but no matching row found in PR model."
            })

    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    with open(csv_output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "excel_row", "inferred_bucket", "sow", "pbom_code", "description", 
            "unit", "quantity", "rules", "mapping_status", "mapping_material_code", "issue"
        ])
        for r in extracted_rows:
            ref_material_code = sp_mappings.get(r['inferred_bucket'], {}).get("material_code", "N/A") if r['inferred_bucket'] in sp_mappings else "N/A"
            writer.writerow([
                r['excel_row'], r['inferred_bucket'], r['sow'], r['pbom_code'], r['description'],
                r['unit'], r['quantity'], r['rules'], r['mapping_status'], ref_material_code, r['issue']
            ])
    print(f"✓ Saved extracted CSV report to: {csv_output_path}")

    # Print Text Report
    print("\n" + "=" * 80)
    print("## Simple Packing PR Model Rows")
    print("=" * 80)
    if not extracted_rows:
        print("No Simple Packing rows found in the TI model.")
    else:
        for r in extracted_rows[:25]:  # Print first 25 for brevity
            print(f"Excel Row {r['excel_row']:<3} | Bucket: {r['inferred_bucket']:<15} | PBOM: {r['pbom_code']:<12} | Status: {r['mapping_status']:<18} | SOW: {r['sow']}")
        if len(extracted_rows) > 25:
            print(f"  ... ({len(extracted_rows) - 25} more rows shown in CSV report) ...")

    print("\n" + "=" * 80)
    print("## Current Mapping Coverage")
    print("=" * 80)
    print(f"Total mapped buckets in JSON: {len(mapped_buckets)}")
    for bucket in sorted(mapped_buckets):
        status = "FOUND" if bucket in found_buckets else "NOT_FOUND_IN_PR_MODEL"
        print(f"  - {bucket:<15} : PBOM={sp_mappings[bucket].get('material_code'):<12} ({status})")

    print("\n" + "=" * 80)
    print("## Missing From Mapping")
    print("=" * 80)
    if not missing_from_mapping:
        print("None. All extracted non-Lawas PR model rows are correctly mapped in JSON.")
    else:
        # Group by bucket to avoid duplicates
        missing_buckets = {}
        for r in missing_from_mapping:
            missing_buckets.setdefault(r['inferred_bucket'], set()).add(r['pbom_code'])
        for b, pboms in sorted(missing_buckets.items()):
            print(f"  - Bucket '{b}' is missing from JSON. Discovered PBOM codes: {list(pboms)}")

    print("\n" + "=" * 80)
    print("## Missing From PR Model")
    print("=" * 80)
    if not missing_from_pr:
        print("None. All mapped buckets in JSON are present in the PR model.")
    else:
        for r in missing_from_pr:
            print(f"  - Bucket '{r['bucket']}' (Mapped PBOM: {r['mapping_material_code']}) not found in PR model SOW rows.")

    print("\n" + "=" * 80)
    print("## Material Code Mismatches")
    print("=" * 80)
    if not mismatches:
        print("None. All mapped material codes match the PR model perfectly.")
    else:
        for r in mismatches:
            print(f"  - Bucket '{r['inferred_bucket']}' (Excel Row {r['excel_row']}): Excel PBOM={r['pbom_code']}, Mapping ref={sp_mappings[r['inferred_bucket']]['material_code']}")

    print("\n" + "=" * 80)
    print("## Repeated Same-PBOM Rows")
    print("=" * 80)
    if not repeated_same_pbom:
        print("None. All buckets have exactly one row in the PR model.")
    else:
        # Group by bucket for cleaner summary
        repeated_groups = {}
        for r in repeated_same_pbom:
            repeated_groups.setdefault(r['inferred_bucket'], []).append(r['excel_row'])
        print(f"INFO: Harmless duplicates detected. The following buckets repeat the same PBOM code across multiple SOW groups:")
        for b, rows in sorted(repeated_groups.items()):
            pbom = extracted_by_bucket[b][0]['pbom_code']
            print(f"  - Bucket '{b}' (PBOM: {pbom}) is repeated in {len(rows)} rows: {rows}")

    print("\n" + "=" * 80)
    print("## Conflicting Bucket PBOMs")
    print("=" * 80)
    if not conflicting_bucket_pbom:
        print("None. No conflicting material codes found for non-Lawas buckets.")
    else:
        conflict_groups = {}
        for r in conflicting_bucket_pbom:
            conflict_groups.setdefault(r['inferred_bucket'], {}).setdefault(r['pbom_code'], []).append(r['excel_row'])
        print("GAP: Genuine conflicts detected! The same bucket is associated with multiple distinct PBOM codes:")
        for b, pboms in sorted(conflict_groups.items()):
            print(f"  - Bucket '{b}':")
            for code, rows in pboms.items():
                print(f"    * PBOM {code} is used in rows: {rows}")

    print("\n" + "=" * 80)
    print("## Suspicious Bucket Text")
    print("=" * 80)
    if not suspicious_bucket_text:
        print("None. All rows contain descriptions that align with the inferred bucket.")
    else:
        print("WARNING: Descriptions mention multiple bucket/state names, indicating possible manual errors or special rules:")
        for r in suspicious_bucket_text:
            print(f"  - Excel Row {r['excel_row']}: Inferred '{r['inferred_bucket']}' | PBOM: {r['pbom_code']} | SOW: '{r['sow']}' | Desc: '{r['description']}'")
            print(f"    Reason: {r['suspicious_reason']}")

    print("\n" + "=" * 80)
    print("## Lawas Special Handling")
    print("=" * 80)
    if not lawas_special_cases:
        print("No Lawas rows found in the PR model.")
    else:
        lawas_groups = {}
        for r in lawas_special_cases:
            lawas_groups.setdefault(r['pbom_code'], []).append(r)
        print("LAWAS_SPECIAL_HANDLING_REQUIRED: Lawas has multiple distinct PBOM codes depending on the target warehouse destination:")
        for code, rows in sorted(lawas_groups.items()):
            print(f"  - PBOM: {code} ({len(rows)} occurrences)")
            print(f"    Description: '{rows[0]['description']}'")
            print(f"    Excel Rows: {[r['excel_row'] for r in rows]}")

    print("\n" + "=" * 80)
    print("## Recommendation")
    print("=" * 80)
    gaps_exist = bool(missing_from_mapping or missing_from_pr or mismatches or conflicting_bucket_pbom or lawas_special_cases or unknown_bucket)
    
    if repeated_same_pbom and not gaps_exist:
        print("INFO: Only harmless repeated rows were found. The geography_mapping.json is fully consistent and supports geography-level mapping!")
    else:
        print("Discrepancies or special conditions require attention:")
        if missing_from_mapping:
            print("  [GAP] Missing Buckets: Update geography_mapping.json to include the newly discovered buckets.")
        if mismatches:
            print("  [GAP] Material Mismatch: Correct material codes in geography_mapping.json to match the PR model.")
        if conflicting_bucket_pbom:
            print("  [CRITICAL GAP] Conflicting PBOMs: SME validation is required to resolve how a single bucket maps to multiple codes.")
        if lawas_special_cases:
            print("  [LAWAS] Lawas Boundary Handling: A coordinate/manual boundary decision rule must be defined before production implementation.")
        if unknown_bucket:
            print("  [GAP] Unknown Buckets: Review Excel rows with unknown buckets to manually categorize their destinations.")
        print("\nDo NOT implement production resolver logic until all GAPs and LAWAS boundary rules are finalized.")

    sys.exit(0)

if __name__ == "__main__":
    main()
