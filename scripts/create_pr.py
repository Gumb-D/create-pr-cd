#!/usr/bin/env python3
"""Official create-pr entrypoint with audit-complete reporting."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import create_pr_impl as _impl
from renderer_reconciliation import collect_renderer_reconciliation


for _name in dir(_impl):
    if not _name.startswith("__"):
        globals().setdefault(_name, getattr(_impl, _name))

_ORIGINAL_PARTITION = _impl._partition_records
_ORIGINAL_RENDERER_ROW = _impl._renderer_row
_LAST_PARTITIONS = None


def _canonical_relocate_site_id(value):
    """Render the approved Decom - Relo Site ID without changing source identity."""
    text = str(value or "").strip()
    match = re.match(r"^(.*?)[_-]RELOCATE(?:_?\d+)?$", text, flags=re.IGNORECASE)
    if not match:
        return text
    base = match.group(1).rstrip("_-")
    return f"{base}_Relocate" if base else text


def _renderer_row(record):
    row = _ORIGINAL_RENDERER_ROW(record)
    sow = str(record.get("pr_context", {}).get("tx_sow_normalized", "") or "").strip().upper()
    if sow == "DECOM - RELO":
        row["customer site code"] = _canonical_relocate_site_id(row.get("customer site code", ""))
    return row


def _partition_records(records, scope, policy=None):
    """Delegate partitioning while retaining the auditable decision sets."""
    global _LAST_PARTITIONS
    _LAST_PARTITIONS = _ORIGINAL_PARTITION(records, scope, policy)
    return _LAST_PARTITIONS


def _record_site_code(record):
    return str(record.get("site", {}).get("site_code", "") or "").strip()


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
    _impl._partition_records = _partition_records
    _impl._renderer_row = _renderer_row


def _reconcile_summary(summary, scope):
    partitions = _LAST_PARTITIONS or {
        "candidates": [], "duplicates": [], "ignored": [], "review_required": []
    }
    selected = []
    for bucket in ("candidates", "duplicates", "ignored", "review_required"):
        selected.extend(partitions.get(bucket, []))

    renderer = collect_renderer_reconciliation(
        Path(summary["output_root"]),
        partitions.get("candidates", []),
        scope,
        lambda record: _renderer_row(record).get("customer site code", ""),
        created_paths=summary.get("created_files", []),
    )
    return _build_site_reconciliation(selected, partitions, renderer)


def run(parsed):
    """Run the implementation and persist ignored/reconciliation audit data."""
    global _LAST_PARTITIONS
    _LAST_PARTITIONS = None
    _sync_dependencies()
    summary = _impl.run(parsed)
    ignored_records = (_LAST_PARTITIONS or {}).get("ignored", [])
    ignored_path = _write_ignored_report(
        Path(summary["output_root"]), parsed.scope, ignored_records, summary["run_mode"]
    )
    summary["ignored_report"] = str(ignored_path.resolve()) if ignored_path else None
    summary.update(_reconcile_summary(summary, parsed.scope))
    Path(summary["summary_path"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
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
