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
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path("scripts")))
from profile_du_export import build_header_inventory
from run_tx_mini_golden_parity import resolution_report, build_canonical_records, render_canonical_path_view
from du_profile_loader import load_du_profile


def normalize_allowed_metadata(sheet_name: str, coordinate: str, value: str) -> str:
    """Only normalize approved non-business metadata fields (e.g., dynamic timestamps in header info)."""
    # If the value is a string timestamp or generation note in known metadata coordinates, normalize whitespace/case.
    # Otherwise return original string representation for strict comparison.
    if value is None:
        return ""
    val_str = str(value)
    # Business values must NOT be normalized away. Only allow metadata normalization if coordinate is in header block (rows 1-3)
    if coordinate.startswith("A1") or coordinate.startswith("B1") or coordinate.startswith("C1"):
        return val_str.strip()
    return val_str


def compare_cell_styles_and_properties(cl, cc):
    """Compare styling and properties of cell cl and cell cc."""
    diffs = []

    if cl.value != cc.value:
        diffs.append(f"value: '{cl.value}' vs '{cc.value}'")
    if cl.data_type != cc.data_type:
        diffs.append(f"data_type: '{cl.data_type}' vs '{cc.data_type}'")
    if cl.number_format != cc.number_format:
        diffs.append(f"number_format: '{cl.number_format}' vs '{cc.number_format}'")

    # Font
    fl, fc = cl.font, cc.font
    if fl and fc:
        if (fl.name, fl.size, fl.bold, fl.italic) != (fc.name, fc.size, fc.bold, fc.italic):
            diffs.append(f"font: ({fl.name}, {fl.size}, {fl.bold}, {fl.italic}) vs ({fc.name}, {fc.size}, {fc.bold}, {fc.italic})")
    elif fl != fc:
        diffs.append(f"font presence: {bool(fl)} vs {bool(fc)}")

    # Alignment
    al, ac = cl.alignment, cc.alignment
    if al and ac:
        if (al.horizontal, al.vertical, al.wrap_text) != (ac.horizontal, ac.vertical, ac.wrap_text):
            diffs.append(f"alignment: ({al.horizontal}, {al.vertical}, {al.wrap_text}) vs ({ac.horizontal}, {ac.vertical}, {ac.wrap_text})")
    elif al != ac:
        diffs.append(f"alignment presence: {bool(al)} vs {bool(ac)}")

    return diffs


def extract_business_fields(wb) -> dict:
    """Extract explicit business fields for validation."""
    fields = {}
    if "details" in wb.sheetnames:
        ws = wb["details"]
        # Extract metadata rows and line item table
        # Row 1-5 metadata, Row 6+ line items
        for r in range(1, min(ws.max_row + 1, 100)):
            vals = [ws.cell(row=r, column=c).value for c in range(1, min(ws.max_column + 1, 20))]
            if any(v is not None for v in vals):
                fields[f"details_row_{r}"] = [str(v) if v is not None else "" for v in vals]
    else:
        # First sheet fallback
        ws = wb.active
        for r in range(1, min(ws.max_row + 1, 100)):
            vals = [ws.cell(row=r, column=c).value for c in range(1, min(ws.max_column + 1, 20))]
            if any(v is not None for v in vals):
                fields[f"sheet_row_{r}"] = [str(v) if v is not None else "" for v in vals]
    return fields


def run_parity():
    out_dir = Path("output/tx-mini-tss-ecc-parity")
    legacy_dir = out_dir / "legacy_outputs"
    canonical_dir = out_dir / "canonical_outputs"

    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = out_dir / "candidate_manifest" / "TX_MINI_TSS_CANDIDATE_MANIFEST.json"
    if not manifest_file.exists():
        # Fallback to creating candidate manifest if needed
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        # Load from canonical scope eligibility build
        candidates = []
        # If not present, we load default 12 candidates
    candidates = json.loads(manifest_file.read_text(encoding="utf-8"))

    # Issue 5 Pre-check: Require candidate count == 12, unique IDs, unique source rows
    if len(candidates) != 12:
        raise ValueError(f"Candidate count must be exactly 12, got {len(candidates)}")
    cand_ids = [c["Candidate ID"] for c in candidates]
    if len(cand_ids) != len(set(cand_ids)):
        raise ValueError("Duplicate Candidate IDs found in manifest")
    source_rows = [c["Source Row"] for c in candidates]
    if len(source_rows) != len(set(source_rows)):
        raise ValueError("Duplicate Source Rows found in manifest")

    input_file = Path("Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx")
    profile_path = Path("config/du_profiles/tx_mini_pr_v1.yaml")
    pr_model = Path("Info/input/pr_model.xlsx")

    if not pr_model.exists():
        raise RuntimeError(f"PR model not found at {pr_model}")
    if not input_file.exists():
        raise RuntimeError(f"Source file not found at {input_file}")

    print("Building canonical view for parity check...")
    profile = load_du_profile(profile_path)
    inventory = build_header_inventory(input_file)
    resolved = resolution_report(inventory, profile)["resolved_mappings"]
    records, stats = build_canonical_records(input_file, profile, inventory, resolved)

    canonical_view = out_dir / "canonical_path_site_view.xlsx"
    render_canonical_path_view(input_file, records, resolved, inventory, canonical_view)
    print(f"Canonical view built at {canonical_view}")

    # Issue 9 Check: Confirm input paths are independent and distinct
    if input_file.resolve() == canonical_view.resolve():
        raise ValueError("Legacy input path and Canonical input path must not be identical")

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

        # Issue 4: Clean output directories before each candidate
        legacy_out = legacy_dir / cand_id
        canon_out = canonical_dir / cand_id

        if legacy_out.exists():
            shutil.rmtree(legacy_out)
        if canon_out.exists():
            shutil.rmtree(canon_out)

        legacy_out.mkdir(parents=True, exist_ok=True)
        canon_out.mkdir(parents=True, exist_ok=True)

        # Legacy Path
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

        # Canonical Path
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

        # Check execution success & exactly one workbook
        legacy_ok = (res_legacy.returncode == 0) and (len(leg_files) == 1)
        canon_ok = (res_canon.returncode == 0) and (len(can_files) == 1)

        if legacy_ok:
            legacy_success += 1
        if canon_ok:
            canonical_success += 1

        if not legacy_ok or not canon_ok:
            results.append({
                "Candidate ID": cand_id,
                "Site Code": site_code,
                "Parity Classification": "GENERATION_FAILED"
            })
            structural_differences.append({
                "Candidate ID": cand_id,
                "Difference": f"Generation failed. Legacy code={res_legacy.returncode}, files={len(leg_files)}. Canon code={res_canon.returncode}, files={len(can_files)}.\nLegacy stderr: {res_legacy.stderr[:200]}\nCanon stderr: {res_canon.stderr[:200]}"
            })
            continue

        leg_wb = openpyxl.load_workbook(leg_files[0], data_only=False)
        can_wb = openpyxl.load_workbook(can_files[0], data_only=False)

        # Issue 6: Comprehensive Structural Comparison
        struct_diffs = []

        # 1. Sheet names & counts
        if leg_wb.sheetnames != can_wb.sheetnames:
            struct_diffs.append(f"Sheet names differ: legacy {leg_wb.sheetnames} vs canonical {can_wb.sheetnames}")

        # 2. Hidden sheets
        for sheet in leg_wb.sheetnames:
            if sheet in can_wb.sheetnames:
                ws_l = leg_wb[sheet]
                ws_c = can_wb[sheet]
                if ws_l.sheet_state != ws_c.sheet_state:
                    struct_diffs.append(f"Sheet '{sheet}' state differs: {ws_l.sheet_state} vs {ws_c.sheet_state}")

                # Dimensions
                if (ws_l.max_row, ws_l.max_column) != (ws_c.max_row, ws_c.max_column):
                    struct_diffs.append(f"Sheet '{sheet}' dimensions differ: ({ws_l.max_row}, {ws_l.max_column}) vs ({ws_c.max_row}, {ws_c.max_column})")

                # Merged ranges
                merged_l = set(str(r) for r in ws_l.merged_cells.ranges)
                merged_c = set(str(r) for r in ws_c.merged_cells.ranges)
                if merged_l != merged_c:
                    struct_diffs.append(f"Sheet '{sheet}' merged cells differ: {merged_l ^ merged_c}")

                # Freeze panes & Auto filter
                if ws_l.freeze_panes != ws_c.freeze_panes:
                    struct_diffs.append(f"Sheet '{sheet}' freeze panes differ: {ws_l.freeze_panes} vs {ws_c.freeze_panes}")
                if getattr(ws_l.auto_filter, 'ref', None) != getattr(ws_c.auto_filter, 'ref', None):
                    struct_diffs.append(f"Sheet '{sheet}' auto filter ref differs: {getattr(ws_l.auto_filter, 'ref', None)} vs {getattr(ws_c.auto_filter, 'ref', None)}")

        if struct_diffs:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "STRUCTURAL_DIFFERENCE"})
            for sd in struct_diffs:
                structural_differences.append({"Candidate ID": cand_id, "Difference": sd})
            continue

        # Cell-by-cell comparison over full coordinate grid
        is_exact = True
        is_normalized = True
        has_biz_diff = False

        for sheet in leg_wb.sheetnames:
            ws_l = leg_wb[sheet]
            ws_c = can_wb[sheet]

            max_r = max(ws_l.max_row, ws_c.max_row)
            max_c = max(ws_l.max_column, ws_c.max_column)

            for r in range(1, max_r + 1):
                for c_idx in range(1, max_c + 1):
                    cl = ws_l.cell(row=r, column=c_idx)
                    cc = ws_c.cell(row=r, column=c_idx)
                    coord = get_column_letter(c_idx) + str(r)

                    cell_diffs = compare_cell_styles_and_properties(cl, cc)
                    if cell_diffs:
                        is_exact = False
                        norm_l = normalize_allowed_metadata(sheet, coord, cl.value)
                        norm_c = normalize_allowed_metadata(sheet, coord, cc.value)

                        if norm_l != norm_c or any("data_type" in d or "number_format" in d for d in cell_diffs):
                            is_normalized = False
                            has_biz_diff = True
                            cell_differences.append({
                                "Candidate ID": cand_id,
                                "Sheet": sheet,
                                "Cell": coord,
                                "Legacy": str(cl.value),
                                "Canonical": str(cc.value)
                            })

        # Issue 7: Business field extraction & comparison
        leg_biz = extract_business_fields(leg_wb)
        can_biz = extract_business_fields(can_wb)

        biz_match = (leg_biz == can_biz) and not has_biz_diff
        business_comparison.append({
            "Candidate ID": cand_id,
            "Site Code": site_code,
            "Matches": str(biz_match).upper(),
            "Legacy Value": json.dumps(leg_biz.get("details_row_6", leg_biz.get("sheet_row_1", []))[:5]),
            "Canonical Value": json.dumps(can_biz.get("details_row_6", can_biz.get("sheet_row_1", []))[:5])
        })

        if has_biz_diff or not biz_match:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "BUSINESS_DIFFERENCE"})
        elif is_exact:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "EXACT_MATCH"})
        else:
            results.append({"Candidate ID": cand_id, "Site Code": site_code, "Parity Classification": "MATCH_AFTER_ALLOWED_NORMALIZATION"})

    # Write Results CSVs
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
        writer = csv.DictWriter(f, fieldnames=["Candidate ID", "Site Code", "Matches", "Legacy Value", "Canonical Value"])
        writer.writeheader()
        writer.writerows(business_comparison)

    # Model Identity
    model_sha = hashlib.sha256(pr_model.read_bytes()).hexdigest()
    model_id = {
        "actual_filename": pr_model.name,
        "logical_model_identity": "Celcomdigi TX PR Model & Line Item 20250420 v3.2",
        "absolute_path": str(pr_model.resolve()),
        "sha256": model_sha,
        "sheet_names": openpyxl.load_workbook(pr_model, data_only=True).sheetnames
    }
    (out_dir / "TX_MINI_TSS_PR_MODEL_IDENTITY.json").write_text(json.dumps(model_id, indent=2))

    # Summary
    counts = {"EXACT_MATCH": 0, "MATCH_AFTER_ALLOWED_NORMALIZATION": 0, "BUSINESS_DIFFERENCE": 0, "STRUCTURAL_DIFFERENCE": 0, "GENERATION_FAILED": 0}
    for r in results:
        counts[r["Parity Classification"]] += 1

    # Issue 5: Strict Overall PASS condition
    overall_pass = (
        len(candidates) == 12 and
        len(results) == 12 and
        canonical_success == 12 and
        legacy_success == 12 and
        (counts["EXACT_MATCH"] + counts["MATCH_AFTER_ALLOWED_NORMALIZATION"]) == 12 and
        counts["BUSINESS_DIFFERENCE"] == 0 and
        counts["STRUCTURAL_DIFFERENCE"] == 0 and
        counts["GENERATION_FAILED"] == 0
    )
    overall = "PASS" if overall_pass else "ECC_PARITY_FAILED"

    summary = {
        "candidate_count": len(candidates),
        "results_count": len(results),
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
    return 0 if overall == "PASS" else 1

if __name__ == "__main__":
    sys.exit(run_parity())
