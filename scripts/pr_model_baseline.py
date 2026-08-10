#!/usr/bin/env python3
"""Single-source PR Model production baseline governance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PR_MODEL_BASELINE_MISMATCH = "PR_MODEL_BASELINE_MISMATCH"
DEFAULT_CONFIG = Path("config/pr_model_baseline.yaml")
LEGACY_DEFAULT_ALIAS = Path("pr_model.xlsx")


class PrModelBaselineError(ValueError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__(f"{code}: {message} | {json.dumps(self.details, sort_keys=True)}")


def _repo_root(root: Path | str | None = None) -> Path:
    if root is not None:
        return Path(root).resolve()
    return Path(__file__).resolve().parent.parent


def load_pr_model_baseline(root: Path | str | None = None, config_path: Path | str | None = None) -> dict[str, Any]:
    repo_root = _repo_root(root)
    path = Path(config_path) if config_path is not None else repo_root / DEFAULT_CONFIG
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Current PR Model baseline configuration is missing.",
            {"config_path": str(path)},
        )
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Current PR Model baseline configuration is invalid.",
            {"config_path": str(path), "exception": type(exc).__name__},
        ) from exc

    required = {
        "baseline_id": baseline.get("baseline_id"),
        "status": baseline.get("status"),
        "version": baseline.get("model", {}).get("version"),
        "path": baseline.get("workbook", {}).get("path"),
        "sha256": baseline.get("workbook", {}).get("sha256"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Current PR Model baseline configuration is incomplete.",
            {"config_path": str(path), "missing": missing},
        )
    if baseline.get("status") != "PRODUCTION":
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Current PR Model baseline is not PRODUCTION.",
            {"status": baseline.get("status")},
        )
    expected_sha = str(baseline["workbook"]["sha256"]).lower()
    if len(expected_sha) != 64 or any(ch not in "0123456789abcdef" for ch in expected_sha):
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Current PR Model baseline SHA-256 is invalid.",
            {"sha256": baseline["workbook"]["sha256"]},
        )
    return baseline


def validate_pr_model_baseline(
    workbook_path: Path | str | None = None,
    *,
    root: Path | str | None = None,
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    repo_root = _repo_root(root)
    baseline = load_pr_model_baseline(repo_root, config_path)
    declared_path = Path(str(baseline["workbook"]["path"]))
    expected_path = declared_path if declared_path.is_absolute() else repo_root / declared_path

    requested_path = Path(workbook_path) if workbook_path is not None else None
    if requested_path == LEGACY_DEFAULT_ALIAS and not (repo_root / requested_path).exists():
        # Backward-compatible alias only: old internal callers that still pass
        # bare `pr_model.xlsx` resolve to the one authoritative current baseline.
        # Any other explicit path remains subject to exact SHA validation.
        actual_path = expected_path
    else:
        actual_path = requested_path if requested_path is not None else expected_path
        if not actual_path.is_absolute():
            actual_path = repo_root / actual_path

    if not actual_path.exists():
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Approved PR Model workbook is missing.",
            {
                "baseline_id": baseline["baseline_id"],
                "version": baseline["model"]["version"],
                "expected_path": str(expected_path),
                "actual_path": str(actual_path),
            },
        )

    expected_sha = str(baseline["workbook"]["sha256"]).lower()
    actual_sha = hashlib.sha256(actual_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise PrModelBaselineError(
            PR_MODEL_BASELINE_MISMATCH,
            "Workbook bytes do not match the single approved production PR Model baseline.",
            {
                "baseline_id": baseline["baseline_id"],
                "version": baseline["model"]["version"],
                "expected_path": str(expected_path),
                "actual_path": str(actual_path),
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "policy": "FAIL_CLOSED",
            },
        )

    return {
        "baseline_id": baseline["baseline_id"],
        "version": str(baseline["model"]["version"]),
        "path": actual_path,
        "expected_path": expected_path,
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
    }
