#!/usr/bin/env python3
"""Official create-pr entrypoint with audit-complete reporting."""
from __future__ import annotations

import csv
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

import create_pr_impl as _impl
from pr_model_baseline import PrModelBaselineError, validate_pr_model_baseline
from renderer_reconciliation import (
    collect_renderer_reconciliation,
    snapshot_renderer_artifacts,
    touched_renderer_artifacts,
)


for _name in dir(_impl):
    if not _name.startswith("__"):
        globals().setdefault(_name, getattr(_impl, _name))

_ORIGINAL_PARTITION = _impl._partition_records
_ORIGINAL_RENDERER_ROW = _impl._renderer_row
_LAST_PARTITIONS = None

_ANTENNA_EVIDENCE_RENDERER_COLUMNS = (
    "Antenna Evidence Governance",
    "Antenna Size NE Mapping Status",
    "Antenna Size FE Mapping Status",
    "TX SOW Details Mapping Status",
    "NE SOW Details Mapping Status",
    "FE SOW Details Mapping Status",
)
CANONICAL_RENDERER_COLUMNS = tuple(_impl.CANONICAL_RENDERER_COLUMNS) + tuple(
    column
    for column in _ANTENNA_EVIDENCE_RENDERER_COLUMNS
    if column not in _impl.CANONICAL_RENDERER_COLUMNS
)


def _canonical_relocate_site_id(value):
    """Render the approved Decom - Relo Site ID without changing source identity."""
    text = str(value or "").strip()
    match = re.match(r"^(.*?)[_-]RELOCATE(?:_?\d+)?$", text, flags=re.IGNORECASE)
    if not match:
        return text
    base = match.group(1).rstrip("_-")
    return f"{base}_Relocate" if base else text


def _canonical_source_fields(record):
    """Return canonical source evidence only when the record carries that contract."""
    source_evidence = record.get("source_evidence")
    if not isinstance(source_evidence, Mapping):
        return None
    fields = source_evidence.get("fields")
    return fields if isinstance(fields, Mapping) else None


def _source_mapping_status(record, canonical_field):
    """Return canonical mapping approval state for renderer-side evidence gates."""
    fields = _canonical_source_fields(record)
    if fields is None:
        return ""
    evidence = fields.get(canonical_field, {})
    if not isinstance(evidence, Mapping):
        return ""
    return str(evidence.get("mapping_status", "") or "").strip().upper()


def _renderer_row(record):
    row = _ORIGINAL_RENDERER_ROW(record)
    canonical_fields = _canonical_source_fields(record)
    row.update(
        {
            "Antenna Evidence Governance": (
                "CANONICAL_MAPPING_STATUS" if canonical_fields is not None else ""
            ),
            "Antenna Size NE Mapping Status": _source_mapping_status(record, "antenna_size_ne"),
            "Antenna Size FE Mapping Status": _source_mapping_status(record, "antenna_size_fe"),
            "TX SOW Details Mapping Status": _source_mapping_status(record, "tx_sow_details"),
            "NE SOW Details Mapping Status": _source_mapping_status(record, "ne_sow_details"),
            "FE SOW Details Mapping Status": _source_mapping_status(record, "fe_sow_details"),
        }
    )
    sow = str(record.get("pr_context", {}).get("tx_sow_normalized", "") or "").strip().upper()
    if sow == "DECOM - RELO":
        row["customer site code"] = _canonical_relocate_site_id(row.get("customer site code", ""))
    return row


def _record_site_code(record):
    return str(record.get("site", {}).get("site_code", "") or "").strip()


def _record_project_key(record):
    return str(record.get("identity", {}).get("project_key", "") or "").strip()


def _assert_unique_project_site_codes(records):
    """Fail closed if the Project + Site Code business identity is duplicated."""
    seen = {}
    duplicates = {}
    for record in records:
        project_key = _record_project_key(record)
        site_code = _record_site_code(record)
        if not site_code:
            continue
        key = (project_key.casefold(), site_code.upper())
        source_row = record.get("identity", {}).get("source_row_number")
        if key not in seen:
            seen[key] = {
                "project_key": project_key,
                "site_code": site_code.upper(),
                "source_rows": [source_row] if source_row is not None else [],
            }
            continue
        duplicate = duplicates.setdefault(key, dict(seen[key]))
        if source_row is not None:
            duplicate.setdefault("source_rows", []).append(source_row)

    if duplicates:
        details = sorted(
            duplicates.values(),
            key=lambda item: (str(item.get("project_key", "")).casefold(), str(item.get("site_code", ""))),
        )
        raise CreatePrError(
            "DUPLICATE_SITE_CODE_IN_PROJECT",
            "Site Code must be unique within a Project before PR generation.",
            {
                "duplicates": details,
                "required_action": "Correct the duplicate Project + Site Code records in the source export before rerunning create-pr.",
            },
        )


def _partition_records(records, scope, policy=None):
    """Validate business identity, then delegate partitioning and retain audit sets."""
    global _LAST_PARTITIONS
    _assert_unique_project_site_codes(records)
    _LAST_PARTITIONS = _ORIGINAL_PARTITION(records, scope, policy)
    return _LAST_PARTITIONS


def _build_site_reconciliation(selected, partitions, renderer_reconciliation=None):
    """Assign exactly one terminal engine disposition to every selected site."""
    renderer_by_site = {
        str(item.get("site_code", "")).strip().upper(): dict(item)
        for item in (renderer_reconciliation or {}).get("site_dispositions", [])
        if str(item.get("site_code", "")).strip()
    }
    direct = {}
    for bucket, disposition in (
        ("review_required", "REVIEW_REQUIRED"),
        ("ignored", "IGNORED_WITH_APPROVED_REASON"),
        ("duplicates", "DUPLICATE_BLOCKED"),
    ):
        for record in partitions.get(bucket, []):
            code = _record_site_code(record)
            decision = record.get("pr_generation_decision", {})
            direct[code.upper()] = {
                "site_code": code,
                "disposition": disposition,
                "reason_code": decision.get("reason_code", ""),
                "reason": decision.get("reason", ""),
            }

    candidate_codes = {_record_site_code(record).upper() for record in partitions.get("candidates", [])}
    site_dispositions = []
    for record in selected:
        source_code = _record_site_code(record)
        key = source_code.upper()
        terminal = direct.get(key)
        if terminal is None and key in candidate_codes:
            terminal = renderer_by_site.get(key)
            if terminal is None:
                terminal = {
                    "site_code": source_code,
                    "disposition": "FAILED",
                    "reason_code": "RENDERER_SITE_UNACCOUNTED",
                    "reason": "The site entered the renderer candidate set but returned no terminal renderer disposition.",
                }
        if terminal is None:
            terminal = {
                "site_code": source_code,
                "disposition": "FAILED",
                "reason_code": "ENGINE_SITE_UNACCOUNTED",
                "reason": "The selected site did not enter any terminal engine partition.",
            }
        site_dispositions.append(terminal)

    counts = {name: 0 for name in (
        "GENERATED", "REVIEW_REQUIRED", "IGNORED_WITH_APPROVED_REASON", "DUPLICATE_BLOCKED", "FAILED"
    )}
    for item in site_dispositions:
        disposition = str(item.get("disposition", ""))
        if disposition in counts:
            counts[disposition] += 1
    accounted = sum(counts.values())
    return {
        "requested_count": len(selected),
        "generated_count": counts["GENERATED"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "approved_ignored_count": counts["IGNORED_WITH_APPROVED_REASON"],
        "duplicate_blocked_count": counts["DUPLICATE_BLOCKED"],
        "failed_count": counts["FAILED"],
        "unaccounted_count": max(0, len(selected) - accounted),
        "site_dispositions": site_dispositions,
    }


def _assert_reconciliation_success(reconciliation):
    """Fail closed only for engine-unaccounted outcomes, not valid review terminals."""
    failed_count = int(reconciliation.get("failed_count", 0) or 0)
    unaccounted_count = int(reconciliation.get("unaccounted_count", 0) or 0)
    if failed_count or unaccounted_count:
        failed_sites = [
            item
            for item in reconciliation.get("site_dispositions", [])
            if str(item.get("disposition", "")).upper() == "FAILED"
        ]
        raise CreatePrError(
            "PR_SITE_RECONCILIATION_FAILED",
            "PR generation did not produce a valid terminal engine outcome for every requested site.",
            {
                "failed_count": failed_count,
                "unaccounted_count": unaccounted_count,
                "failed_sites": failed_sites,
                "required_action": "Review renderer/engine failure evidence before rerunning create-pr.",
            },
        )


def _write_ignored_report(output, scope, records, run_mode=RUN_MODE_PRODUCTION):
    """Write one auditable row for every ignored record, including SM."""
    if not records:
        return None
    marker = f"_{UAT_MARKER}" if run_mode == RUN_MODE_NON_PRODUCTION_UAT else ""
    path = Path(output) / f"CANONICAL_IGNORED_{scope}{marker}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_REPORT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_impl._report_row(record, scope))
    return path


def _sync_dependencies() -> None:
    """Propagate public test seams and audit wrappers."""
    for name in (
        "resolve_du_profile",
        "build_canonical_records",
        "load_subcontractor_policy",
        "load_contract_reference",
        "validate_candidate_contracts",
    ):
        public_value = globals().get(name)
        if public_value is not None:
            setattr(_impl, name, public_value)
    _impl.CANONICAL_RENDERER_COLUMNS = CANONICAL_RENDERER_COLUMNS
    _impl._partition_records = _partition_records
    _impl._renderer_row = _renderer_row


def _reconcile_summary(summary, scope, before_renderer=None):
    partitions = _LAST_PARTITIONS or {
        "candidates": [], "duplicates": [], "ignored": [], "review_required": []
    }
    selected = []
    for bucket in ("candidates", "duplicates", "ignored", "review_required"):
        selected.extend(partitions.get(bucket, []))

    touched = touched_renderer_artifacts(
        Path(summary["output_root"]),
        before_renderer or {},
    )
    renderer = collect_renderer_reconciliation(
        Path(summary["output_root"]),
        partitions.get("candidates", []),
        scope,
        lambda record: _renderer_row(record).get("customer site code", ""),
        created_paths=touched,
    )
    return _build_site_reconciliation(selected, partitions, renderer)


def _persist_reconciliation_artifact_error(summary, error):
    """Replace a previously successful summary when reconciliation evidence cannot be read."""
    diagnostic = {
        "exception_type": type(error).__name__,
        "message": str(error),
    }
    summary["status"] = "ERROR"
    summary["code"] = "PR_RECONCILIATION_ARTIFACT_READ_FAILED"
    summary["reconciliation_error"] = diagnostic
    Path(summary["summary_path"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    raise CreatePrError(
        "PR_RECONCILIATION_ARTIFACT_READ_FAILED",
        "Renderer output could not be read for site reconciliation.",
        {
            "summary_path": summary.get("summary_path"),
            "reconciliation_error": diagnostic,
            "required_action": "Inspect the renderer output artifact for corruption or incomplete write, then rerun create-pr.",
        },
    ) from error


def run(parsed):
    """Run the implementation only after validating the single approved PR Model baseline."""
    global _LAST_PARTITIONS
    _LAST_PARTITIONS = None
    baseline = validate_pr_model_baseline(getattr(parsed, "pr_model", None))
    if not hasattr(parsed, "pr_model"):
        parsed.pr_model = baseline["path"]
    _sync_dependencies()
    before_renderer = snapshot_renderer_artifacts(Path(parsed.output))
    summary = _impl.run(parsed)
    summary["pr_model_baseline"] = {
        "baseline_id": baseline["baseline_id"],
        "version": baseline["version"],
        "sha256": baseline["actual_sha256"],
    }
    ignored_records = (_LAST_PARTITIONS or {}).get("ignored", [])
    ignored_path = _write_ignored_report(
        Path(summary["output_root"]), parsed.scope, ignored_records, summary["run_mode"]
    )
    summary["ignored_report"] = str(ignored_path.resolve()) if ignored_path else None
    try:
        reconciliation = _reconcile_summary(summary, parsed.scope, before_renderer)
    except Exception as error:
        _persist_reconciliation_artifact_error(summary, error)

    summary.update(reconciliation)

    if reconciliation.get("failed_count", 0) or reconciliation.get("unaccounted_count", 0):
        summary["status"] = "ERROR"
        summary["code"] = "PR_SITE_RECONCILIATION_FAILED"

    Path(summary["summary_path"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _assert_reconciliation_success(reconciliation)
    return summary


def main() -> int:
    try:
        result = run(parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except PrModelBaselineError as error:
        payload = {"status": "ERROR", "code": error.code, "message": str(error), "details": error.details}
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
