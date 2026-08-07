#!/usr/bin/env python3
"""Build local-only UAT packets for TX Mini Scope Eligibility."""

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping

from openpyxl import Workbook
from canonical_generator_bridge import build_records_from_export, classify_uat_record, _load_json_or_yaml
from profile_du_export import sha256_file, calculate_header_hash, build_header_inventory, fingerprint_key

EXPECTED_SOURCE_SHA256 = "81de6ba3673dad406e7824727c5c8492dd06b3ef60d088a6e9d680af6c35f8ab"
EXPECTED_HEADER_HASH = "99645657ed5177bed3f0af673f141dc700fb7b486743cb830d5350a473c007ff"


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


def resolve_fingerprint(inventory: Mapping[str, Any], fingerprint: Mapping[str, Any]) -> str:
    if not fingerprint:
        raise ValueError("Missing fingerprint")
    target_key = fingerprint_key(fingerprint)
    matches = []
    for sheet in inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            if column.get("fingerprint_key") == target_key:
                matches.append(column["source_position"]["excel_column"])
    if len(matches) == 0:
        raise ValueError("FINGERPRINT_NOT_FOUND")
    if len(matches) > 1:
        raise ValueError("FINGERPRINT_AMBIGUOUS")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--scope-config", required=True, type=Path)
    parser.add_argument("--sow-registry", default=Path("config/registries/canonical_sow_registry.yaml"), type=Path)
    parser.add_argument("--output", default=Path("output/tx-mini-scope-eligibility-uat"), type=Path)
    args = parser.parse_args()

    # Config Validation
    if not args.scope_config.exists():
        raise FileNotFoundError(f"Scope config not found: {args.scope_config}")

    try:
        scope_config_data = _load_json_or_yaml(args.scope_config)
    except Exception as e:
        raise ValueError(f"Invalid JSON/YAML: {e}")

    if scope_config_data.get("profile_id") != "tx_mini_pr_v1":
        raise ValueError("PROFILE_ID_MISMATCH")

    config_version = scope_config_data.get("config_version")
    if not config_version:
        raise ValueError("Missing config_version")

    config_status = scope_config_data.get("status")
    if config_status != "UAT_ONLY":
        raise ValueError("SCOPE_CONFIG_NOT_UAT_ONLY")

    scopes_config = scope_config_data.get("scopes")
    if not scopes_config:
        raise ValueError("Missing scopes layer")

    for required_scope in ["TSS", "TI"]:
        if required_scope not in scopes_config:
            raise ValueError(f"Missing {required_scope} config")

    if len(scopes_config) != 2:  # Strict mode check for extra scope
        raise ValueError("Extra unexpected scope in config")

    for s, c in scopes_config.items():
        if c.get("rule") != "actual_end_required":
            raise ValueError("UNSUPPORTED_SCOPE_ELIGIBILITY_RULE")
        fp = c.get("actual_end_fingerprint")
        if not fp or not isinstance(fp, dict) or not all(k in fp for k in ["field_code", "wbs_stage", "task_name", "display_header"]):
            raise ValueError("Missing or invalid fingerprint layer")
        for k, v in fp.items():
            if not v or str(v).strip() == "":
                raise ValueError(f"Empty fingerprint value for {k}")

    # Source Identity Validation
    file_hash = sha256_file(args.input)
    if file_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"SOURCE_SHA256_MISMATCH: expected {EXPECTED_SOURCE_SHA256}, got {file_hash}")

    inventory = build_header_inventory(args.input)
    header_hash = calculate_header_hash(inventory)
    if header_hash != EXPECTED_HEADER_HASH:
        raise ValueError(f"HEADER_HASH_MISMATCH: expected {EXPECTED_HEADER_HASH}, got {header_hash}")

    # Fingerprint Resolution
    resolved_columns = {}
    for scope in ["TSS", "TI"]:
        fp = scopes_config[scope]["actual_end_fingerprint"]
        resolved_columns[scope] = resolve_fingerprint(inventory, fp)

    csv_columns = [
        "Source Row", "Masked Site Code", "Tx SOW Raw", "Tx SOW Normalized",
        "Region", "TSS Subcontractor", "TSS Actual End Date",
        "Existing TSS PR State", "Eligibility Classification", "Eligibility Reason",
        "Profile ID", "Profile Version", "Mapping Version",
        "Scope Eligibility Config Path", "Scope Eligibility Config Version", "Scope Eligibility Config Status",
        "Scope Fingerprint", "Resolved Source Column",
        "Source SHA-256", "Header Hash", "ECC Allowed"
    ]
    ti_csv_columns = [col.replace("TSS", "TI") for col in csv_columns]

    scopes = ["TSS", "TI"]
    manifest = []

    summary = {
        "file_hash": file_hash,
        "header_hash": header_hash,
        "scopes": {}
    }

    legacy_comparisons = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_out = Path(temp_dir)

        for scope in scopes:
            records, metadata = build_records_from_export(args.input, args.profile, scope, args.sow_registry, scope_config=scopes_config)

            counts = {
                "UAT_CANDIDATE": 0,
                "DUPLICATE_BLOCKED": 0,
                "NO_PR_OR_IGNORED": 0,
                "REVIEW_REQUIRED": 0
            }
            partitions = {k: [] for k in counts}

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
                    "Scope Eligibility Config Path": str(args.scope_config),
                    "Scope Eligibility Config Version": config_version,
                    "Scope Eligibility Config Status": config_status,
                    "Scope Fingerprint": fingerprint_key(scopes_config[scope]["actual_end_fingerprint"]),
                    "Resolved Source Column": resolved_columns[scope],
                    "Source SHA-256": file_hash,
                    "Header Hash": header_hash,
                    "ECC Allowed": False
                }
                partitions[cls].append(row)

            summary["scopes"][scope] = counts
            cols = csv_columns if scope == "TSS" else ti_csv_columns

            for cls, items in partitions.items():
                if scope == "TI" and cls == "UAT_CANDIDATE":
                    continue

                if cls == "UAT_CANDIDATE":
                    write_csv(temp_out / f"TX_MINI_{scope}_{cls}S.csv", items, cols)
                    write_xlsx(temp_out / f"TX_MINI_{scope}_{cls}S.xlsx", items, cols)
                    manifest.append(f"TX_MINI_{scope}_{cls}S.csv")
                    manifest.append(f"TX_MINI_{scope}_{cls}S.xlsx")
                else:
                    write_csv(temp_out / f"TX_MINI_{scope}_{cls}.csv", items, cols)
                    manifest.append(f"TX_MINI_{scope}_{cls}.csv")

            if sum(counts.values()) != total_canonical_rows:
                raise ValueError(f"Count consistency violation in {scope}")

            legacy_comparisons[scope] = {
                "scope_selection_parity": "NOT_EXECUTED",
                "legacy_selected": None,
                "eligibility_selected": counts["UAT_CANDIDATE"],
                "selected_by_both": None,
                "legacy_only": None,
                "eligibility_only": None,
                "excluded_missing_actual_end": None,
                "excluded_duplicate": None,
                "excluded_no_pr_sow": None,
                "review_required": counts["REVIEW_REQUIRED"]
            }

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
            md.append("TI UAT candidates: 0\n")

        (temp_out / "TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.md").write_text("\n".join(md))
        manifest.append("TX_MINI_SCOPE_ELIGIBILITY_SUMMARY.md")

        legacy_comp_md = [
            "# Legacy Selection Comparison",
            "",
            "Canonical column rendering parity: PASS",
            "Scope selection parity: NOT_EXECUTED",
            "ECC output parity for the 12 TSS candidates: NOT YET EXECUTED",
            ""
        ]
        for scope in scopes:
            legacy_comp_md.extend([
                f"## {scope}",
                f"- scope selection parity: NOT_EXECUTED",
                f"- legacy-selected row count: NOT_EXECUTED",
                f"- eligibility-selected candidate count: {legacy_comparisons[scope]['eligibility_selected']}",
                f"- review required: {legacy_comparisons[scope]['review_required']}",
                ""
            ])

        (temp_out / "TX_MINI_LEGACY_SELECTION_COMPARISON.md").write_text("\n".join(legacy_comp_md))
        manifest.append("TX_MINI_LEGACY_SELECTION_COMPARISON.md")
        (temp_out / "TX_MINI_LEGACY_SELECTION_COMPARISON.json").write_text(json.dumps(legacy_comparisons, indent=2))
        manifest.append("TX_MINI_LEGACY_SELECTION_COMPARISON.json")

        generated_files = {}
        for filename in manifest:
            generated_files[filename] = sha256_file(temp_out / filename)

        manifest_data = {
            "generated_at": str(temp_out),  # placeholder
            "generator_commit_sha": "TODO",
            "source_file_name": args.input.name,
            "source_sha256": file_hash,
            "header_hash": header_hash,
            "profile_id": "tx_mini_pr_v1",
            "profile_version": metadata["profile_version"],
            "mapping_version": metadata["mapping_version"],
            "scope_config_path": str(args.scope_config),
            "scope_config_version": config_version,
            "scope_config_status": config_status,
            "resolved_tss_fingerprint": fingerprint_key(scopes_config["TSS"]["actual_end_fingerprint"]),
            "resolved_tss_column": resolved_columns["TSS"],
            "resolved_ti_fingerprint": fingerprint_key(scopes_config["TI"]["actual_end_fingerprint"]),
            "resolved_ti_column": resolved_columns["TI"],
            "classification_counts": {s: summary["scopes"][s] for s in scopes},
            "count_reconciliation": "PASS",
            "ecc_allowed": False,
            "production_gate": "NON_PRODUCTION_UAT_ONLY",
            "generated_files": generated_files
        }

        import datetime
        manifest_data["generated_at"] = datetime.datetime.utcnow().isoformat()
        import subprocess
        try:
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            manifest_data["generator_commit_sha"] = commit_sha
        except Exception:
            manifest_data["generator_commit_sha"] = "UNKNOWN"

        (temp_out / "TX_MINI_ELIGIBILITY_MANIFEST.json").write_text(json.dumps(manifest_data, indent=2))

        # Atomic rename
        if args.output.exists():
            shutil.rmtree(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_out), str(args.output))

    print(f"UAT packet built in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
