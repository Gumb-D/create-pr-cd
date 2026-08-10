#!/usr/bin/env python3
"""Official create-pr-cd entrypoint for raw iEPMS export to ECC output."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from openpyxl import Workbook

from canonical_input_pipeline import build_canonical_records
from canonical_site_validator import PR_INPUT_READY
from du_export_adapter import PR_STATUS_EXISTS, PR_STATUS_NOT_REQUIRED
from du_profile_resolver import DuProfileResolutionError, resolve_du_profile
from pr_safety_controls import (
    CONTRACT_MISSING_REASON_CODE,
    EXCLUDED_REASON_CODE,
    SafetyControlError,
    get_exclusion_rule,
    load_contract_reference,
    load_subcontractor_policy,
    reason_distribution,
    set_generation_decision,
    validate_candidate_contracts,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE_ROOT = ROOT / "config" / "du_profiles"
IDENTITY_REGISTRY = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
SOW_REGISTRY = ROOT / "config" / "registries" / "canonical_sow_registry.yaml"
RENDERER = ROOT / "scripts" / "generate_tss_pr_ecc.py"
PR_POLICY_PATH = ROOT / "config" / "subcontractor_pr_policy.json"

RUN_MODE_PRODUCTION = "PRODUCTION"
RUN_MODE_NON_PRODUCTION_UAT = "NON_PRODUCTION_UAT"
UAT_MARKER = RUN_MODE_NON_PRODUCTION_UAT
UAT_ELIGIBLE_PROFILE_STATUSES = {"PR_INPUT_READY", "PRODUCTION"}

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
    "DU Profile ID",
    "Migration Decision ID",
    "Migration Work Item",
    "Required PBOM Codes",
)

REVIEW_REPORT_FIELDS = (
    "Source_Row",
    "Site_Code",
    "Region",
    "Scope",
    "Subcontractor",
    "Tx_SOW",
    "Profile_ID",
    "Classification",
    "Reason_Code",
    "Reason",
    "Required_Action",
    "Blocking_Reasons",
)

CONTRACT_REVIEW_FIELDS = (
    "Site_Code",
    "Region",
    "Scope",
    "Subcontractor",
    "Tx_SOW",
    "Reason_Code",
    "Required_Action",
)


class CreatePrError(RuntimeError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _resolve_run_mode(profile_status: str, non_production_uat: bool) -> str:
    status = str(profile_status or "").strip().upper()
    if non_production_uat:
        if status not in UAT_ELIGIBLE_PROFILE_STATUSES:
            raise CreatePrError(
                "PROFILE_NOT_UAT_ELIGIBLE",
                f"DU Profile status {status or '(blank)'} is not eligible for explicit non-production UAT ECC generation.",
                {
                    "profile_status": status or None,
                    "eligible_statuses": sorted(UAT_ELIGIBLE_PROFILE_STATUSES),
                    "required_action": "Complete profile validation and promote the profile to PR_INPUT_READY before UAT.",
                },
            )
        return RUN_MODE_NON_PRODUCTION_UAT
    if status != RUN_MODE_PRODUCTION:
        raise CreatePrError(
            "PROFILE_NOT_PRODUCTION",
            f"DU Profile status {status or '(blank)'} is not PRODUCTION; formal ECC generation is blocked.",
            {
                "profile_status": status or None,
                "required_action": "Use --non-production-uat for approved UAT or promote the profile through the formal production gate.",
            },
        )
    return RUN_MODE_PRODUCTION


def _new_uat_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _windows_extended_path(path: Path) -> str:
    resolved = Path(path).resolve()
    path_str = str(resolved)
    if not os.name == "nt":
        return path_str
    if path_str.startswith("\\\\?\\"):
        return path_str
    if path_str.startswith("\\\\"):
        # UNC path: convert to extended UNC prefix
        return "\\\\?\\UNC\\" + path_str[2:]
    return "\\\\?\\" + path_str


def _rename_path(source: Path, target: Path) -> None:
    if os.name == "nt":
        os.rename(_windows_extended_path(source), _windows_extended_path(target))
    else:
        source.rename(target)


def _resolve_output_directory(
    requested_output: Path,
    run_mode: str,
    run_id: str | None = None,
) -> tuple[Path, str | None]:
    output = Path(requested_output)
    if run_mode == RUN_MODE_PRODUCTION:
        return output, None
    if run_mode != RUN_MODE_NON_PRODUCTION_UAT:
        raise CreatePrError(
            "INVALID_RUN_MODE",
            f"Unsupported PR generation run mode: {run_mode}",
            {"run_mode": run_mode},
        )
    resolved_run_id = str(run_id or _new_uat_run_id()).strip()
    if not resolved_run_id:
        raise CreatePrError("INVALID_UAT_RUN_ID", "Non-production UAT run ID must not be blank.")
    return output / UAT_MARKER / resolved_run_id, resolved_run_id


def _mark_uat_artifacts(paths: list[Path]) -> list[Path]:
    renamed: list[Path] = []
    for raw_path in paths:
        source = Path(raw_path)
        if UAT_MARKER in source.stem:
            renamed.append(source)
            continue
        target = source.with_name(f"{source.stem}_{UAT_MARKER}{source.suffix}")
        if target.exists():
            raise CreatePrError(
                "UAT_ARTIFACT_COLLISION",
                "A marker-bearing UAT artefact already exists.",
                {"source": str(source), "target": str(target)},
            )
        _rename_path(source, target)
        renamed.append(target)
    return renamed


def _new_output_artifacts(output: Path, before: set[Path]) -> list[Path]:
    return sorted(
        path.resolve()
        for path in output.glob("*")
        if path.is_file() and path.resolve() not in before
    )


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
    parser.add_argument(
        "--subcontractor-policy",
        type=Path,
        default=PR_POLICY_PATH,
        help="Approved fail-closed subcontractor PR policy JSON",
    )
    parser.add_argument(
        "--non-production-uat",
        action="store_true",
        help=(
            "Explicitly generate visibly isolated non-production UAT ECC output "
            "for PR_INPUT_READY or PRODUCTION profiles."
        ),
    )
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


def _scope_subcontractor(record: Mapping[str, Any], scope: str) -> str:
    field = "subcontractor_tss" if str(scope).upper() == "TSS" else "subcontractor_ti"
    return str(record.get("pr_context", {}).get(field, "") or "").strip()


def _partition_records(
    records: list[dict[str, Any]],
    scope: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    scope = scope.upper()
    effective_policy = dict(policy or load_subcontractor_policy(PR_POLICY_PATH))
    subcontractor_field = "subcontractor_tss" if scope == "TSS" else "subcontractor_ti"
    status_field = "existing_tss_pr_status" if scope == "TSS" else "existing_ti_pr_status"
    partitions = {"candidates": [], "duplicates": [], "ignored": [], "review_required": []}
    for record in records:
        context = record.get("pr_context", {})
        subcontractor = str(context.get(subcontractor_field, "") or "").strip()
        exclusion = get_exclusion_rule(effective_policy, subcontractor, scope)
        if exclusion:
            set_generation_decision(
                record,
                exclusion["classification"],
                exclusion["reason_code"],
                exclusion["reason"],
            )
            partitions["ignored"].append(record)
            continue
        if not subcontractor:
            set_generation_decision(
                record,
                "IGNORED",
                "MISSING_SUBCONTRACTOR",
                "No scope-specific subcontractor was provided.",
            )
            partitions["ignored"].append(record)
            continue
        status = context.get(status_field)
        # Preserve the approved renderer business behavior: TI blocks an
        # existing/waived PR before generation; TSS entitlement remains
        # available for downstream Final PO audit comparison.
        if scope == "TI":
            if status == PR_STATUS_EXISTS:
                set_generation_decision(
                    record,
                    "DUPLICATE_BLOCKED",
                    "EXISTING_PR_REFERENCE",
                    "An existing TI PR reference is already present.",
                )
                partitions["duplicates"].append(record)
                continue
            if status == PR_STATUS_NOT_REQUIRED:
                set_generation_decision(
                    record,
                    "IGNORED",
                    "PR_STATUS_NOT_REQUIRED",
                    "The approved TI PR status states that a PR is not required.",
                )
                partitions["ignored"].append(record)
                continue
        normalization = (
            record.get("source_evidence", {})
            .get("fields", {})
            .get("tx_sow_normalized", {})
            .get("normalization_status")
        )
        migration_decision = context.get("migration_decision", {})
jendela_ti_decision = (
    scope == "TI"
    and record.get("validation", {}).get("profile_id") == "jendela_tx_migration_pr_v1"
    and isinstance(migration_decision, Mapping)
)
if jendela_ti_decision and migration_decision.get("classification") == "APPROVED_NO_OUTPUT":
    set_generation_decision(
        record,
        "IGNORED",
        str(migration_decision.get("reason_code") or "JENDELA_TI_NO_WORK_REQUIRED"),
        "The approved Jendela TI work plan contains no PR work items.",
    )
    partitions["ignored"].append(record)
    continue
approved_jendela_ti_decision = (
    jendela_ti_decision
    and migration_decision.get("classification") == "APPROVED"
)
        # Business hard stop: the approved Cancel / Drop SOW (and every other
        # APPROVED_NO_OUTPUT value) outranks Jendela migration eligibility.
        if normalization == "APPROVED_NO_OUTPUT":
            set_generation_decision(
                record,
                "IGNORED",
                "APPROVED_NO_OUTPUT",
                "The approved SOW normalization intentionally produces no PR output.",
            )
            partitions["ignored"].append(record)
            continue
        if record.get("validation", {}).get("pr_input_classification") != PR_INPUT_READY:
            set_generation_decision(
                record,
                "REVIEW_REQUIRED",
                "CANONICAL_INPUT_NOT_READY",
                "The canonical record is not classified PR_INPUT_READY.",
                "Resolve canonical validation blockers before PR generation.",
            )
            partitions["review_required"].append(record)
            continue
        if normalization != "APPROVED" and not approved_jendela_ti_decision:
            set_generation_decision(
                record,
                "REVIEW_REQUIRED",
                "TX_SOW_NOT_APPROVED",
                "The Tx SOW normalization is not approved for PR output.",
                "Review and approve the Tx SOW normalization before PR generation.",
            )
            partitions["review_required"].append(record)
            continue
        set_generation_decision(record, "CANDIDATE", "ELIGIBLE", "All pre-contract eligibility checks passed.")
        partitions["candidates"].append(record)
    return partitions


def _renderer_row(record: Mapping[str, Any]) -> dict[str, Any]:
    site = record.get("site", {})
    context = record.get("pr_context", {})
    technical = record.get("technical_context", {})
    approved_contract = record.get("approved_contract", {})
    approved_scope = str(approved_contract.get("scope", "")).upper()
    canonical_subcontractor = approved_contract.get("subcontractor", "")
    tss_subcontractor = context.get("subcontractor_tss", "")
    ti_subcontractor = context.get("subcontractor_ti", "")
    if approved_scope == "TSS" and canonical_subcontractor:
        tss_subcontractor = canonical_subcontractor
    if approved_scope == "TI" and canonical_subcontractor:
        ti_subcontractor = canonical_subcontractor
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
        "SubCon - TSS Team": tss_subcontractor,
        "Subcon PR - TSS": "",
        "SubCon - TI Team": ti_subcontractor,
        "Subcon PR - TI": "",
        "BOQ Configuration": technical.get("boq_configuration", ""),
        "TX SOW Details": technical.get("tx_sow_details", ""),
        "NE SOW Details": technical.get("ne_sow_details", ""),
        "FE SOW Details": technical.get("fe_sow_details", ""),
        "DU Profile ID": record.get("validation", {}).get("profile_id", ""),
        "Migration Decision ID": "",
        "Migration Work Item": "",
        "Required PBOM Codes": "",
    }


def _renderer_rows(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Render the decision result; this function never re-evaluates its matrix."""
    base = _renderer_row(record)
    decision = record.get("pr_context", {}).get("migration_decision", {})
    if not isinstance(decision, Mapping) or decision.get("classification") != "APPROVED":
        return [base]
    work_items = decision.get("work_items", [])
    if not isinstance(work_items, list) or not work_items:
        return [base]
    profile_id = str(record.get("validation", {}).get("profile_id", ""))
    source_row = record.get("identity", {}).get("source_row_number")
    site_code = str(record.get("site", {}).get("site_code", ""))
    decision_id = f"{profile_id}:{source_row}:{site_code}"
    rendered = []
    for work_item in work_items:
        if not isinstance(work_item, Mapping):
            continue
        row = dict(base)
        row["Tx SOW"] = work_item.get("model_sow", "")
        row["Migration Decision ID"] = decision_id
        row["Migration Work Item"] = work_item.get("work_item", "")
        required_codes = work_item.get("required_pbom_codes", [])
        row["Required PBOM Codes"] = "|".join(str(code) for code in required_codes)
        rendered.append(row)
    return rendered


def _write_renderer_input(path: Path, records: list[dict[str, Any]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "data"
    worksheet.append(["CANONICAL CREATE-PR-CD INPUT"])
    worksheet.append(["Generated from an approved DU Profile."])
    worksheet.append(["Only validated scope candidates with approved contracts are included."])
    worksheet.append(list(CANONICAL_RENDERER_COLUMNS))
    for record in records:
        for row in _renderer_rows(record):
            worksheet.append([row.get(column) for column in CANONICAL_RENDERER_COLUMNS])
    workbook.save(path)


def _report_row(record: Mapping[str, Any], scope: str) -> dict[str, Any]:
    decision = record.get("pr_generation_decision", {})
    context = record.get("pr_context", {})
    validation = record.get("validation", {})
    classification = decision.get("classification") or validation.get("pr_input_classification", "")
    return {
        "Source_Row": record.get("identity", {}).get("source_row_number"),
        "Site_Code": record.get("site", {}).get("site_code", ""),
        "Region": context.get("region", ""),
        "Scope": str(scope).upper(),
        "Subcontractor": _scope_subcontractor(record, scope),
        "Tx_SOW": context.get("tx_sow_normalized") or context.get("tx_sow_raw", ""),
        "Profile_ID": validation.get("profile_id", ""),
        "Classification": classification,
        "Reason_Code": decision.get("reason_code", ""),
        "Reason": decision.get("reason", ""),
        "Required_Action": decision.get("required_action", ""),
        "Blocking_Reasons": " | ".join(validation.get("blocking_reasons", [])),
    }


def _write_review_report(
    output: Path,
    scope: str,
    records: list[dict[str, Any]],
    run_mode: str = RUN_MODE_PRODUCTION,
) -> Path | None:
    if not records:
        return None
    marker = f"_{UAT_MARKER}" if run_mode == RUN_MODE_NON_PRODUCTION_UAT else ""
    path = output / f"CANONICAL_REVIEW_REQUIRED_{scope}{marker}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_REPORT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_report_row(record, scope))
    return path


def _write_contract_review_report(
    output: Path,
    scope: str,
    records: list[dict[str, Any]],
    run_mode: str,
) -> Path | None:
    if not records:
        return None
    marker = f"_{UAT_MARKER}" if run_mode == RUN_MODE_NON_PRODUCTION_UAT else ""
    path = output / f"CONTRACT_MAPPING_REVIEW_{scope}{marker}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONTRACT_REVIEW_FIELDS)
        writer.writeheader()
        for record in records:
            row = _report_row(record, scope)
            writer.writerow({field: row[field] for field in CONTRACT_REVIEW_FIELDS})
    return path


def run(parsed: argparse.Namespace) -> dict[str, Any]:
    resolution = resolve_du_profile(
        parsed.site_data,
        profile_root=PROFILE_ROOT,
        identity_registry_path=IDENTITY_REGISTRY,
    )
    profile_status = str(resolution["profile"].get("status", "")).strip().upper()
    run_mode = _resolve_run_mode(
        profile_status,
        bool(getattr(parsed, "non_production_uat", False)),
    )
    requested_output = parsed.output.resolve()
    output, run_id = _resolve_output_directory(
        requested_output,
        run_mode,
        getattr(parsed, "uat_run_id", None),
    )
    output.mkdir(parents=True, exist_ok=True)

    policy_path = Path(getattr(parsed, "subcontractor_policy", PR_POLICY_PATH))
    policy = load_subcontractor_policy(policy_path)
    contract_mappings = load_contract_reference(Path(parsed.mapping))

    records, metadata = build_canonical_records(
        input_path=parsed.site_data,
        profile=resolution["profile"],
        inventory=resolution["inventory"],
        header_hash=resolution["header_hash"],
        scope=parsed.scope,
        sow_registry_path=SOW_REGISTRY,
    )
    selected = _select_records(records, _parse_site_codes(parsed.site_code), parsed.all_sites)
    partitions = _partition_records(selected, parsed.scope, policy)
    pre_contract_candidate_count = len(partitions["candidates"])
    contract_valid, contract_missing = validate_candidate_contracts(
        partitions["candidates"],
        parsed.scope,
        contract_mappings,
    )
    partitions["candidates"] = contract_valid
    partitions["review_required"].extend(contract_missing)

    review_path = _write_review_report(output, parsed.scope, partitions["review_required"], run_mode)
    contract_review_path = _write_contract_review_report(output, parsed.scope, contract_missing, run_mode)

    before_renderer = {path.resolve() for path in output.glob("*") if path.is_file()}
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
                partial_artifacts = _new_output_artifacts(output, before_renderer)
                if run_mode == RUN_MODE_NON_PRODUCTION_UAT:
                    partial_artifacts = _mark_uat_artifacts(partial_artifacts)
                raise CreatePrError(
                    "ECC_RENDERER_FAILED",
                    "Validated canonical records could not be rendered to ECC.",
                    {
                        "exit_code": result.returncode,
                        "partial_artifacts": [str(path.resolve()) for path in partial_artifacts],
                    },
                )

    renderer_created = _new_output_artifacts(output, before_renderer)
    if run_mode == RUN_MODE_NON_PRODUCTION_UAT:
        renderer_created = _mark_uat_artifacts(renderer_created)
    created = sorted(str(path.resolve()) for path in renderer_created)

    missing_subcontractors = sorted(
        {_scope_subcontractor(record, parsed.scope) for record in contract_missing if _scope_subcontractor(record, parsed.scope)},
        key=str.casefold,
    )
    ignored_distribution = reason_distribution(partitions["ignored"])
    review_distribution = reason_distribution(partitions["review_required"])
    sm_excluded_count = ignored_distribution.get(EXCLUDED_REASON_CODE, 0)

    summary = {
        "status": "SUCCESS",
        "entrypoint": "create_pr.py",
        "run_mode": run_mode,
        "profile_status": profile_status,
        "non_production_uat": run_mode == RUN_MODE_NON_PRODUCTION_UAT,
        "production_ecc_allowed": run_mode == RUN_MODE_PRODUCTION,
        "requested_output": str(requested_output),
        "output_root": str(output.resolve()),
        "run_id": run_id,
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
        "pre_contract_candidate_count": pre_contract_candidate_count,
        "candidate_count": len(partitions["candidates"]),
        "duplicate_count": len(partitions["duplicates"]),
        "ignored_count": len(partitions["ignored"]),
        "ignored_reason_distribution": ignored_distribution,
        "review_required_count": len(partitions["review_required"]),
        "review_required_reason_distribution": review_distribution,
        "sm_excluded_count": sm_excluded_count,
        "sm_excluded_by_scope": {parsed.scope: sm_excluded_count},
        "contract_mapping_missing_count": len(contract_missing),
        "contract_mapping_missing_subcontractors": missing_subcontractors,
        "contract_mapping_review_report": str(contract_review_path.resolve()) if contract_review_path else None,
        "subcontractor_policy": str(policy_path.resolve()),
        "contract_reference": str(Path(parsed.mapping).resolve()),
        "review_report": str(review_path.resolve()) if review_path else None,
        "created_files": created,
    }
    marker = f"_{UAT_MARKER}" if run_mode == RUN_MODE_NON_PRODUCTION_UAT else ""
    summary_path = output / f"CREATE_PR_SUMMARY_{parsed.scope}{marker}.json"
    summary["summary_path"] = str(summary_path.resolve())
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    try:
        result = run(parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except DuProfileResolutionError as error:
        payload = {"status": "ERROR", "code": error.code, "message": str(error), "details": error.details}
    except (CreatePrError, SafetyControlError) as error:
        payload = {"status": "ERROR", "code": error.code, "message": str(error), "details": error.details}
    except Exception as error:
        payload = {"status": "ERROR", "code": "CREATE_PR_FAILED", "message": str(error)}
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
