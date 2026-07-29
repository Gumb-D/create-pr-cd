#!/usr/bin/env python3
"""Public wrapper for the consolidated all-DU UAT implementation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import all_du_uat_impl as _impl
from all_du_uat_impl import *  # noqa: F401,F403 - preserve the tested public module surface


def run_batch(args):
    """Run the batch and classify any blocked profile as a controlled block."""

    summary = _impl.run_batch(args)
    has_blocks = bool(summary.get("blocked_profile_count", 0))
    has_failures = bool(summary.get("failed_scope_runs", 0))
    reconciled = bool(summary.get("manifest_reconciliation_ok", False))
    summary["status"] = (
        "SUCCESS"
        if not has_blocks and not has_failures and reconciled
        else "COMPLETED_WITH_BLOCKS"
    )
    summary_path = Path(summary["output_root"]) / "UAT_MASTER_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    try:
        summary = run_batch(_impl.parse_args())
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["status"] == "SUCCESS" else 2
    except (
        _impl.BatchUatError,
        _impl.SafetyControlError,
        _impl.create_pr.CreatePrError,
        _impl.DuProfileResolutionError,
    ) as error:
        payload = {
            "status": "ERROR",
            "code": getattr(error, "code", "ALL_DU_UAT_FAILED"),
            "message": str(error),
            "details": getattr(error, "details", {}),
        }
    except Exception as error:
        payload = {"status": "ERROR", "code": "ALL_DU_UAT_FAILED", "message": str(error)}
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
