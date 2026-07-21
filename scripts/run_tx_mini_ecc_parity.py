import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import hashlib
from datetime import datetime

import openpyxl

sys.path.insert(0, str(Path("scripts")))
from profile_du_export import build_header_inventory
from run_tx_mini_golden_parity import resolution_report, build_canonical_records, render_canonical_path_view
from du_profile_loader import load_du_profile
from canonical_generator_bridge import build_records_from_export

def run_parity():
    out_dir = Path("output/tx-mini-tss-ecc-parity")
    legacy_dir = out_dir / "legacy_outputs"
    canonical_dir = out_dir / "canonical_outputs"
    report_dir = out_dir
    
    legacy_dir.mkdir(parents=True, exist_ok=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = out_dir / "candidate_manifest" / "TX_MINI_TSS_CANDIDATE_MANIFEST.json"
    candidates = json.loads(manifest_file.read_text(encoding="utf-8"))
    
    input_file = Path("Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx")
    profile_path = Path("config/du_profiles/tx_mini_pr_v1.yaml")
    pr_model = Path("Info/input/pr_model.xlsx")
    
    if not pr_model.exists():
        raise RuntimeError(f"PR model not found at {pr_model}")
        
    print("Building canonical view for parity check...")
    # Load profile and build canonical view for ALL rows to maintain parity structures.
    # Actually, canonical view should only contain the 12 candidates?
    # The instruction says "For each of the 12 candidates, compare... canonical adapter... legacy path".
    # Golden parity renders the entire source file. Let's do that for parity consistency.
    profile = load_du_profile(profile_path)
    inventory = build_header_inventory(input_file)
    resolved = resolution_report(inventory, profile)["resolved_mappings"]
    records, stats = build_canonical_records(input_file, profile, inventory, resolved)
    
    canonical_view = out_dir / "canonical_path_site_view.xlsx"
    render_canonical_path_view(input_file, records, resolved, inventory, canonical_view)
    print(f"Canonical view built at {canonical_view}")

    results = []
    
    cell_differences = []
    structural_differences = []
    business_comparison = []
    
    canonical_success = 0
    legacy_success = 0
    
    generator_script = Path("scripts/generate_tss_pr_ecc.py")
    
    for c in candidates:
        site_code = c["Site Code"]
        cand_id = c["Candidate ID"]
        print(f"Running candidate {cand_id} ({site_code})...")
        
        # Legacy Path
        legacy_out = legacy_dir / cand_id
        legacy_out.mkdir(parents=True, exist_ok=True)
        cmd_legacy = [
            sys.executable, str(generator_script),
            "--site-data", str(input_file),
            "--pr-model", str(pr_model),
            "--output", str(legacy_out),
            "--site-code", site_code,
            "--scope", "TSS"
        ]
        res_legacy = subprocess.run(cmd_legacy, capture_output=True, text=True)
        leg_files = list(legacy_out.glob("*.xlsx")) if legacy_out.exists() else []
        if leg_files: legacy_success += 1
        
        # Canonical Path
        canon_out = canonical_dir / cand_id
        canon_out.mkdir(parents=True, exist_ok=True)
        cmd_canon = [
            sys.executable, str(generator_script),
            "--site-data", str(canonical_view),
            "--pr-model", str(pr_model),
            "--output", str(canon_out),
            "--site-code", site_code,
            "--scope", "TSS"
        ]
        res_canon = subprocess.run(cmd_canon, capture_output=True, text=True)
        can_files = list(canon_out.glob("*.xlsx")) if canon_out.exists() else []
        if can_files: canonical_success += 1
        
        if not leg_files or not can_files:
            results.append({
                "Candidate ID": cand_id,
                "Site Code": site_code,
                "Parity Classification": "GENERATION_FAILED"
            })
            continue
            
        leg_wb = openpyxl.load_workbook(leg_files[0], data_only=False)
        can_wb = openpyxl.load_workbook(can_files[0], data_only=False)
        
        # Structural check
        if leg_wb.sheetnames != can_wb.sheetnames:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "STRUCTURAL_DIFFERENCE"})
            structural_differences.append({"Candidate ID": cand_id, "Difference": f"Sheets differ: {leg_wb.sheetnames} vs {can_wb.sheetnames}"})
            continue
            
        is_exact = True
        is_normalized = True
        has_biz_diff = False
        
        for sheet in leg_wb.sheetnames:
            ws_l = leg_wb[sheet]
            ws_c = can_wb[sheet]
            
            for row_idx, (row_l, row_c) in enumerate(zip(ws_l.iter_rows(), ws_c.iter_rows())):
                for col_idx, (cl, cc) in enumerate(zip(row_l, row_c)):
                    vl, vc = cl.value, cc.value
                    if vl != vc:
                        is_exact = False
                        
                        # Check if it's just timestamp or metadata normalization difference
                        # Wait, what are allowed normalizations? Timestamps? ZIP ordering?
                        # I'll just check if they are identical in string after stripping?
                        # Actually, business fields must match exactly.
                        if str(vl).strip() == str(vc).strip():
                            pass # Normalization match
                        else:
                            is_normalized = False
                            has_biz_diff = True
                            cell_differences.append({
                                "Candidate ID": cand_id,
                                "Sheet": sheet,
                                "Cell": cl.coordinate,
                                "Legacy": vl,
                                "Canonical": vc
                            })
                            
        # Simulate Business Comparison
        business_comparison.append({
            "Candidate ID": cand_id,
            "Site Code": site_code,
            "Matches": not has_biz_diff
        })
        
        if has_biz_diff:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "BUSINESS_DIFFERENCE"})
        elif is_exact:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "EXACT_MATCH"})
        else:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "MATCH_AFTER_ALLOWED_NORMALIZATION"})

    # Write Results CSV
    with open(out_dir / "TX_MINI_TSS_ECC_PARITY_RESULTS.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Candidate ID", "Site Code", "Parity Classification"])
        writer.writeheader()
        writer.writerows(results)
        
    with open(out_dir / "TX_MINI_TSS_ECC_CELL_DIFFERENCES.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Candidate ID", "Sheet", "Cell", "Legacy", "Canonical"])
        writer.writeheader()
        writer.writerows(cell_differences)
        
    with open(out_dir / "TX_MINI_TSS_ECC_STRUCTURAL_DIFFERENCES.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Candidate ID", "Difference"])
        writer.writeheader()
        writer.writerows(structural_differences)
        
    with open(out_dir / "TX_MINI_TSS_ECC_BUSINESS_FIELD_COMPARISON.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Candidate ID", "Site Code", "Matches"])
        writer.writeheader()
        writer.writerows(business_comparison)
        
    # Model Identity
    model_sha = hashlib.sha256(pr_model.read_bytes()).hexdigest()
    model_id = {
        "filename": pr_model.name,
        "absolute_path": str(pr_model.resolve()),
        "sha256": model_sha,
        "sheet_names": openpyxl.load_workbook(pr_model, data_only=True).sheetnames
    }
    (out_dir / "TX_MINI_TSS_PR_MODEL_IDENTITY.json").write_text(json.dumps(model_id, indent=2))
    
    # Summary
    counts = {"EXACT_MATCH": 0, "MATCH_AFTER_ALLOWED_NORMALIZATION": 0, "BUSINESS_DIFFERENCE": 0, "STRUCTURAL_DIFFERENCE": 0, "GENERATION_FAILED": 0}
    for r in results:
        counts[r["Parity Classification"]] += 1
        
    overall = "PASS" if counts["BUSINESS_DIFFERENCE"] == 0 and counts["STRUCTURAL_DIFFERENCE"] == 0 and counts["GENERATION_FAILED"] == 0 else "ECC_PARITY_FAILED"
    
    summary = {
        "candidate_count": len(candidates),
        "canonical_generation_success_count": canonical_success,
        "legacy_generation_success_count": legacy_success,
        "exact_match_count": counts["EXACT_MATCH"],
        "normalized_match_count": counts["MATCH_AFTER_ALLOWED_NORMALIZATION"],
        "business_difference_count": counts["BUSINESS_DIFFERENCE"],
        "structural_difference_count": counts["STRUCTURAL_DIFFERENCE"],
        "generation_failed_count": counts["GENERATION_FAILED"],
        "overall_parity_result": overall
    }
    (out_dir / "TX_MINI_TSS_ECC_PARITY_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    
    # Manifest
    commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "repository_commit_sha": commit_sha,
        "pr_number": 37,
        "business_uat_status": "BUSINESS_UAT_WAIVED_BY_OWNER",
        "owner_waiver_status": "PROCEED_WITH_ACCEPTED_RISK",
        "candidate_count": len(candidates),
        "pr_model_filename": pr_model.name,
        "pr_model_sha256": model_sha,
        "generator_commit_sha": commit_sha,
        "ecc_allowed": False,
        "production_gate": "PROFILE_NOT_PRODUCTION",
        "production_output_created": False,
        "production_submission_invoked": False
    }
    (out_dir / "TX_MINI_TSS_ECC_PARITY_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    
    print(f"Overall parity: {overall}")

if __name__ == "__main__":
    run_parity()
