#!/usr/bin/env python3
"""Official create-pr-cd entrypoint for raw iEPMS export to ECC output."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from openpyxl import Workbook

from canonical_input_pipeline import build_canonical_records
from canonical_site_validator import PR_INPUT_READY
from du_export_adapter import PR_STATUS_EXISTS, PR_STATUS_NOT_REQUIRED
from du_profile_resolver import DuProfileResolutionError, resolve_du_profile


ROOT = Path(__file__).resolve().parent.parent
PROFILE_ROOT = ROOT / "config" / "du_profiles"
IDENTITY_REGISTRY = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
SOW_REGISTRY = ROOT / "config" / "registries" / "canonical_sow_registry.yaml"
RENDERER = ROOT / "scripts" / "generate_tss_pr_ecc.py"

CANONICAL_RENDERER_COLUMNS = (
    "customer site code",
    "customer site name",
    "du code",
    "region",
    "Province/State",
    "Latitude (North Plus South Minus)",
    "Longitude (East Plus West Minus)",
    "TX Upgrade Scope",
    "Tx SOW",
    "MW Config Antenna Size NE",
    "MW Config Antenna Size FE",
    "SubCon - TSS Team",
    "Subcon PR - TSS",
    "SubCon - TI Team",
    "Subcon PR - TI",
    "BOQ Configuration",
    "TX SOW Details",
    "NE SOW Details",
    "FE SOW Details",
)


class CreatePrError(RuntimeError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Identify DU Profile, canonicalize iEPMS data, and generate ECC.")
    parser.add_argument("--site-data", required=True, type=Path, help="Original four-header iEPMS export")
    parser.add_argument("--output", required=True, type=Path, help="ECC output directory")
    parser.add_argument("--scope", required=True, choices=["TSS", "TI"], type=str.upper)
    parser.add_argument("--site-code", help="Comma-separated site codes")
    parser.add_argument("--all-sites", action="store_true")
    parser.add_argument("--pr-model", type=Path, default=ROOT / "Info" / "input" / "pr_model.xlsx")
    parser.add_argument("--template", type=Path, default=ROOT / "Info" / "input" / "ecc_template.xls")
    parser.add_argument("--mapping", type=Path, default=ROOT / "Info" / "input" / "contract_info_reference.md")
    return parser.parse_args()


def _parse_site_codes(raw: str | None) -> list[str]:
    return list(dict.fromkeys(value.strip().upper() for value in str(raw or "").split(",") if value.strip()))


def _select_records(records: list[dict[str, Any]], site_codes: list[str], all_sites: bool) -> list[dict[str, Any]]:
    if all_sites == bool(site_codes):
        raise CreatePrError("INVALID_SITE_SELECTION", "Use exactly one of --all-sites or --site-code.")
    if all_sites:
        return records
    available = {
        str(record.get("site", {}).get("site_code", "")).strip().upper()
        for record in records
    }
    missing = [code for code in site_codes if code not in available]
    if missing:
        raise CreatePrError(
            "SITE_CODES_NOT_FOUND",
            "Requested site codes were not found in the canonical input.",
            {"missing_site_codes": missing},
        )
    requested = set(site_codes)
    return [
        record
        for record in records
        if str(record.get("site", {}).get("site_code", "")).strip().upper() in requested
    ]


def _partition_records(records: list[dict[str, Any]], scope: str) -> dict[str, list[dict[str, Any]]]:
    scope = scope.upper()
    subcontractor_field = "subcontractor_tss" if scope == "TSS" else "subcontractor_ti"
    status_field = "existing_tss_pr_status" if scope == "TSS" else "existing_ti_pr_status"
    partitions = {"candidates": [], "duplicates": [], "ignored": [], "review_required": []}
    for record in records:
        context = record.get("pr_context", {})
        subcontractor = str(context.get(subcontractor_field, "") or "").strip()
        if not subcontractor:
            partitions["ignored"].append(record)
            continue
        status = context.get(status_field)
        # Preserve the approved renderer business behavior: TI blocks an
        # existing/waived PR before generation; TSS entitlement remains
        # available for downstream Final PO audit comparison.
        if scope == "TI":
            if status == PR_STATUS_EXISTS:
                partitions["duplicates"].append(record)
                continue
            if status == PR_STATUS_NOT_REQUIRED:
                partitions["ignored"].append(record)
                continue
        normalization = (
            record.get("source_evidence", {})
            .get("fields", {})
            .get("tx_sow_normalized", {})
            .get("normalization_status")
        )
        if normalization == "APPROVED_NO_OUTPUT":
            partitions["ignored"].append(record)
            continue
        if record.get("validation", {}).get("pr_input_classification") != PR_INPUT_READY:
            partitions["review_required"].append(record)
            continue
        if normalization != "APPROVED":
            partitions["review_required"].append(record)
            continue
        partitions["candidates"].append(record)
    return partitions


def _renderer_row(record: Mapping[str, Any]) -> dict[str, Any]:
    site = record.get("site", {})
    context = record.get("pr_context", {})
    technical = record.get("technical_context", {})
    return {
        "customer site code": site.get("site_code", ""),
        "customer site name": site.get("site_name", ""),
        "du code": site.get("du_key", ""),
        "region": context.get("region", ""),
        "Province/State": context.get("state", ""),
        "Latitude (North Plus South Minus)": technical.get("latitude"),
        "Longitude (East Plus West Minus)": technical.get("longitude"),
        "TX Upgrade Scope": context.get("tx_upgrade_scope_raw", ""),
        "Tx SOW": context.get("tx_sow_normalized") or context.get("tx_sow_raw", ""),
        "MW Config Antenna Size NE": technical.get("antenna_size_ne", ""),
        "MW Config Antenna Size FE": technical.get("antenna_size_fe", ""),
        "SubCon - TSS Team": context.get("subcontractor_tss", ""),
        "Subcon PR - TSS": "",
        "SubCon - TI Team": context.get("subcontractor_ti", ""),
        "Subcon PR - TI": "",
        "BOQ Configuration": technical.get("boq_configuration", ""),
        "TX SOW Details": technical.get("tx_sow_details", ""),
        "NE SOW Details": technical.get("ne_sow_details", ""),
        "FE SOW Details": technical.get("fe_sow_details", ""),
    }


def _write_renderer_input(path: Path, records: list[dict[str, Any]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "data"
    worksheet.append(["CANONICAL CREATE-PR-CD INPUT"])
    worksheet.append(["Generated from an approved DU Profile."])
    worksheet.append(["Only validated scope candidates are included."])
    worksheet.append(list(CANONICAL_RENDERER_COLUMNS))
    for record in records:
        row = _renderer_row(record)
        worksheet.append([row.get(column) for column in CANONICAL_RENDERER_COLUMNS])
    workbook.save(path)


def _write_review_report(output: Path, scope: str, records: list[dict[str, Any]]) -> Path | None:
    if not records:
        return None
    path = output / f"CANONICAL_REVIEW_REQUIRED_{scope}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Source_Row", "Site_Code", "Profile_ID", "Classification", "Blocking_Reasons"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Source_Row": record.get("identity", {}).get("source_row_number"),
                    "Site_Code": record.get("site", {}).get("site_code", ""),
                    "Profile_ID": record.get("validation", {}).get("profile_id", ""),
                    "Classification": record.get("validation", {}).get("pr_input_classification", ""),
                    "Blocking_Reasons": " | ".join(record.get("validation", {}).get("blocking_reasons", [])),
                }
            )
    return path


def run(parsed: argparse.Namespace) -> dict[str, Any]:
    output = parsed.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    resolution = resolve_du_profile(
        parsed.site_data,
        profile_root=PROFILE_ROOT,
        identity_registry_path=IDENTITY_REGISTRY,
    )
    records, metadata = build_canonical_records(
        input_path=parsed.site_data,
        profile=resolution["profile"],
        inventory=resolution["inventory"],
        header_hash=resolution["header_hash"],
        scope=parsed.scope,
        sow_registry_path=SOW_REGISTRY,
    )
    selected = _select_records(records, _parse_site_codes(parsed.site_code), parsed.all_sites)
    partitions = _partition_records(selected, parsed.scope)
    review_path = _write_review_report(output, parsed.scope, partitions["review_required"])

    before = {path.resolve() for path in output.glob("*") if path.is_file()}
    if partitions["candidates"]:
        with tempfile.TemporaryDirectory(prefix="create-pr-canonical-") as temp_dir:
            canonical_input = Path(temp_dir) / "canonical_input.xlsx"
            _write_renderer_input(canonical_input, partitions["candidates"])
            command = [
                sys.executable,
                str(RENDERER),
                "--site-data", str(canonical_input),
                "--pr-model", str(parsed.pr_model),
                "--template", str(parsed.template),
                "--mapping", str(parsed.mapping),
                "--output", str(output),
                "--scope", parsed.scope,
                "--all-sites",
                "--du-model-name", metadata["du_model_name"],
            ]
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")
            if result.returncode != 0:
                raise CreatePrError(
                    "ECC_RENDERER_FAILED",
                    "Validated canonical records could not be rendered to ECC.",
                    {"exit_code": result.returncode},
                )

    created = sorted(
        str(path.resolve())
        for path in output.glob("*")
        if path.is_file() and path.resolve() not in before
    )
    summary = {
        "status": "SUCCESS",
        "entrypoint": "create_pr.py",
        "scope": parsed.scope,
        "profile_id": metadata["profile_id"],
        "profile_version": metadata["profile_version"],
        "mapping_version": metadata["mapping_version"],
        "project_key": metadata["project_key"],
        "du_model_name": metadata["du_model_name"],
        "du_model_id": metadata["du_model_id"],
        "view_id": metadata["view_id"],
        "header_hash": metadata["header_hash"],
        "source_record_count": len(records),
        "selected_record_count": len(selected),
        "candidate_count": len(partitions["candidates"]),
        "duplicate_count": len(partitions["duplicates"]),
        "ignored_count": len(partitions["ignored"]),
        "review_required_count": len(partitions["review_required"]),
        "review_report": str(review_path.resolve()) if review_path else None,
        "created_files": created,
    }
    summary_path = output / f"CREATE_PR_SUMMARY_{parsed.scope}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path.resolve())
    return summary


def main() -> int:
    try:
        result = run(parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except DuProfileResolutionError as error:
        payload = {"status": "ERROR", "code": error.code, "message": str(error), "details": error.details}
    except CreatePrError as error:
        payload = {"status": "ERROR", "code": error.code, "message": str(error), "details": error.details}
    except Exception as error:
        payload = {"status": "ERROR", "code": "CREATE_PR_FAILED", "message": str(error)}
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
