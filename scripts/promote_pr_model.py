#!/usr/bin/env python3
"""Promote a compatible PR Model candidate into the single current production baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from analyze_pr_model_change import analyze_pr_model_change
from pr_model_baseline import load_pr_model_baseline, validate_pr_model_baseline


class PrModelPromotionError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__(f"{code}: {message} | {json.dumps(self.details, sort_keys=True)}")


def _repo_root(root: Path | str | None = None) -> Path:
    return Path(root).resolve() if root is not None else Path(__file__).resolve().parent.parent


def promote_pr_model(candidate_path: Path | str, version: str, *, root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _repo_root(root)
    current = validate_pr_model_baseline(root=repo_root)
    baseline = load_pr_model_baseline(repo_root)
    candidate = Path(candidate_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    if not candidate.exists():
        raise PrModelPromotionError(
            "PR_MODEL_CANDIDATE_MISSING",
            "Candidate PR Model workbook does not exist.",
            {"candidate_path": str(candidate)},
        )

    report = analyze_pr_model_change(current["path"], candidate)
    if report["status"] != "COMPATIBLE":
        raise PrModelPromotionError(
            "PR_MODEL_PROMOTION_REVIEW_REQUIRED",
            "Candidate cannot replace production until compatibility review is cleared.",
            {"candidate_path": str(candidate), "candidate_version": version, "compatibility": report},
        )

    candidate_bytes = candidate.read_bytes()
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    production_path = current["expected_path"]
    config_path = repo_root / "config/pr_model_baseline.yaml"

    next_baseline = json.loads(json.dumps(baseline))
    next_baseline["model"]["version"] = str(version)
    next_baseline["workbook"]["path"] = str(baseline["workbook"]["path"])
    next_baseline["workbook"]["sha256"] = candidate_sha

    with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
        staging = Path(tmp)
        staged_workbook = staging / "pr_model.xlsx"
        staged_config = staging / "pr_model_baseline.yaml"
        staged_workbook.write_bytes(candidate_bytes)
        staged_config.write_text(json.dumps(next_baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        old_workbook = production_path.read_bytes()
        old_config = config_path.read_bytes()
        try:
            shutil.copy2(staged_workbook, production_path)
            os.replace(staged_config, config_path)
            validated = validate_pr_model_baseline(root=repo_root)
        except Exception as exc:
            production_path.write_bytes(old_workbook)
            config_path.write_bytes(old_config)
            raise PrModelPromotionError(
                "PR_MODEL_PROMOTION_ROLLED_BACK",
                "Promotion failed and the previous production baseline was restored.",
                {"exception": type(exc).__name__, "message": str(exc)},
            ) from exc

    return {
        "status": "PROMOTED",
        "baseline_id": validated["baseline_id"],
        "version": validated["version"],
        "sha256": validated["actual_sha256"],
        "path": str(validated["path"]),
        "compatibility": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a compatible PR Model candidate.")
    parser.add_argument("candidate")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        result = promote_pr_model(args.candidate, args.version)
    except PrModelPromotionError as exc:
        print(json.dumps({"status": "ERROR", "code": exc.code, "message": str(exc), "details": exc.details}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
