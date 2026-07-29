#!/usr/bin/env python3
"""Official create-pr entrypoint with audit-complete reporting."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import create_pr_impl as _impl


for _name in dir(_impl):
    if not _name.startswith("__"):
        globals().setdefault(_name, getattr(_impl, _name))

_ORIGINAL_PARTITION = _impl._partition_records
_LAST_PARTITIONS = None


def _partition_records(records, scope, policy=None):
    """Delegate partitioning while retaining the auditable decision sets."""

    global _LAST_PARTITIONS
    _LAST_PARTITIONS = _ORIGINAL_PARTITION(records, scope, policy)
    return _LAST_PARTITIONS


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
    """Propagate public test seams and the audit partition wrapper."""

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


def run(parsed):
    """Run the implementation and persist the ignored-record audit reference."""

    global _LAST_PARTITIONS
    _LAST_PARTITIONS = None
    _sync_dependencies()
    summary = _impl.run(parsed)
    ignored_records = (_LAST_PARTITIONS or {}).get("ignored", [])
    ignored_path = _write_ignored_report(
        Path(summary["output_root"]),
        parsed.scope,
        ignored_records,
        summary["run_mode"],
    )
    summary["ignored_report"] = str(ignored_path.resolve()) if ignored_path else None
    Path(summary["summary_path"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
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
