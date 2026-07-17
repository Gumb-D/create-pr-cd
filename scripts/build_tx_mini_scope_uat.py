#!/usr/bin/env python3
"""Build local-only UAT packets for TX Mini Scope Eligibility."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping

from openpyxl import Workbook
from canonical_generator_bridge import build_records_from_export, classify_uat_record, GENERATOR_COLUMNS, canonical_record_to_generator_row
from profile_du_export import sha256_file, calculate_header_hash, build_header_inventory

def write_csv(path: Path, rows: list[Mapping[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def write_xlsx(path: Path, rows: list[Mapping[str, Any]], fieldnames: list[str]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(fieldnames)
    for row in rows:
        ws.append([row.get(col, "") for col in fieldnames])
    wb.save(path)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--sow-registry", default=Path("config/registries/canonical_sow_registry.yaml"), type=Path)
    parser.add_argument("--output", default=Path("output/tx-mini-scope-eligibility-uat"), type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    
    file_hash = sha256_file(args.input)
    inventory = build_header_inventory(args.input)
    header_hash = calculate_header_hash(inventory)

    summary = {
        "file_hash": file_hash,
        "header_hash": header_hash,
        "scopes": {}
    }

    manifest = []
    
    scopes = ["TSS", "TI"]
    total_canonical_rows = 0
    
    # We will use the canonical_generator_bridge's build_records_from_export
    # However, to meet the strict reporting requirements for the UAT candidates we need a specific set of columns for the CSVs.
    
    csv_columns = [
        "Source Row",
        "Masked Site Code",
        "Tx SOW Raw",
        "Tx SOW Normalized",
        "Region",
        "TSS Subcontractor",
        "TSS Actual End Date",
        "Existing TSS PR State",
        "Eligibility Classification",
        "Eligibility Reason",
        "Profile ID",
        "Profile Version",
        "Mapping Version",
        "Scope Eligibility Config Version",
        "Source SHA-256",
        "Header Hash",
        "ECC Allowed"
    ]
    
    ti_csv_columns = [col.replace("TSS", "TI") for col in csv_columns]
    
    for scope in scopes:
        records, metadata = build_records_from_export(args.input, args.profile, scope, args.sow_registry)
        
        counts = {
            "UAT_CANDIDATE": 0,
            "DUPLICATE_BLOCKED": 0,
            "NO_PR_OR_IGNORED": 0,
            "REVIEW_REQUIRED": 0
        }
        
        partitions = {
            "UAT_CANDIDATE": [],
            "DUPLICATE_BLOCKED": [],
            "NO_PR_OR_IGNORED": [],
            "REVIEW_REQUIRED": []
        }
        
        total_canonical_rows = len(records)
        
        for record in records:
            cls, reasons = classify_uat_record(record, scope)
            counts[cls] += 1
            
            site_code = record["site"].get("site_code", "")
            masked = site_code[:3] + "***" + site_code[-3:] if len(site_code) > 6 else "***"
            
            end_date_val = record.get("source_evidence", {}).get("fields", {}).get(f"{scope.lower()}_actual_end_date", {}).get("source_value", "")
            existing_pr = record.get("pr_context", {}).get(f"existing_{scope.lower()}_pr_status", "")
            
            row = {
                "Source Row": record["identity"]["source_row_number"],
                "Masked Site Code": masked,
                "Tx SOW Raw": record["pr_context"].get("tx_sow_raw", ""),
                "Tx SOW Normalized": record["pr_context"].get("tx_sow_normalized", ""),
                "Region": record["pr_context"].get("region", ""),
                f"{scope} Subcontractor": record["pr_context"].get(f"subcontractor_{scope.lower()}", ""),
                f"{scope} Actual End Date": str(end_date_val) if end_date_val else "",
                f"Existing {scope} PR State": str(existing_pr) if existing_pr else "",
                "Eligibility Classification": cls,
                "Eligibility Reason": " | ".join(reasons),
                "Profile ID": record["validation"]["profile_id"],
                "Profile Version": record["validation"]["profile_version"],
                "Mapping Version": record["validation"]["mapping_version"],
                "Scope Eligibility Config Version": "0.1.0", # hardcoded for this version
                "Source SHA-256": file_hash,
                "Header Hash": header_hash,
                "ECC Allowed": False
            }
            partitions[cls].append(row)
        
        summary["scopes"][scope] = counts
        cols = csv_columns if scope == "TSS" else ti_csv_columns
        
        for cls, items in partitions.items():
            if scope == "TI" and cls == "UAT_CANDIDATE":
                continue # Do not generate a misleading empty production candidate workbook for TI
                
            if cls == "UAT_CANDIDATE":
                write_csv(args.output / f"TX_MINI_{scope}_{cls}S.csv", items, cols)
                write_xlsx(args.output / f"TX_MINI_{scope}_{cls}S.xlsx", items, cols)
                manifest.append(f"TX_MINI_{scope}_{cls}S.csv")
                manifest.append(f"TX_MINI_{scope}_{cls}S.xlsx")
            else:
                write_csv(args.output / f"TX_MINI_{scope}_{cls}.csv", items, cols)
                manifest.append(f"TX_MINI_{scope}_{cls}.csv")
                
        # Count consistency guard
        total_classified = sum(counts.values())
        if total_classified != total_canonical_rows:
            raise ValueError(f"Count consistency violation in {scope}: canonical rows {total_canonical_rows} != classified {total_classified}")
    
    (args.output / "TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    manifest.append("TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.json")
    
    md = [
        "# TX Mini Scope Eligibility Summary",
        "",
        f"- Source SHA-256: `{file_hash}`",
        f"- Header Hash: `{header_hash}`",
        ""
    ]
    for scope in scopes:
        md.extend([
            f"## {scope}",
            f"- UAT_CANDIDATE: {summary['scopes'][scope]['UAT_CANDIDATE']}",
            f"- DUPLICATE_BLOCKED: {summary['scopes'][scope]['DUPLICATE_BLOCKED']}",
            f"- NO_PR_OR_IGNORED: {summary['scopes'][scope]['NO_PR_OR_IGNORED']}",
            f"- REVIEW_REQUIRED: {summary['scopes'][scope]['REVIEW_REQUIRED']}",
            ""
        ])
    if summary['scopes']['TI']['UAT_CANDIDATE'] == 0:
        md.append("TI UAT candidates: 0")
        
    (args.output / "TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.md").write_text("\n".join(md))
    manifest.append("TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.md")
    
    (args.output / "TX_MINI_ELIGIBILITY_MANIFEST.json").write_text(json.dumps({"manifest": manifest}, indent=2))
    print(f"UAT packet built in {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
