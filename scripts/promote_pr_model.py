#!/usr/bin/env python3
"""Promote a compatible or explicitly reviewed PR Model into the single current production baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
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


def _sync_legacy_hash_mirrors(root: Path, sha256_value: str) -> list[Path]:
    """Synchronize transitional hard-coded mirrors until legacy consumers are removed."""
    targets = (
        (root / "scripts/generate_tss_pr_ecc.py", "APPROVED_PR_MODEL_SHA256"),
        (root / "scripts/run_tx_mini_ecc_parity.py", "APPROVED_PR_MODEL_SHA256"),
        (root / "tests/test_jendela_approved_pr_model.py", "APPROVED_V4_SHA256"),
    )
    changed: list[Path] = []
    for path, constant in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(rf'({re.escape(constant)}\s*=\s*["\'])[0-9a-f]{{64}}(["\'])')
        updated, count = pattern.subn(rf"\g<1>{sha256_value}\g<2>", text, count=1)
        if count:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def _run_regression_gate(root: Path) -> dict[str, Any]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise PrModelPromotionError(
            "PR_MODEL_REGRESSION_FAILED",
            "Candidate baseline failed the broad regression gate.",
            {
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-4000:],
                "stderr_tail": result.stderr[-4000:],
            },
        )
    return {"status": "PASS", "command": command}


def _load_review_approval(
    approval_path: Path | str,
    *,
    root: Path,
    candidate_sha: str,
    version: str,
    reason_codes: list[str],
) -> dict[str, Any]:
    path = Path(approval_path)
    if not path.is_absolute():
        path = root / path
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PrModelPromotionError(
            "PR_MODEL_PROMOTION_APPROVAL_INVALID",
            "Reviewed-change approval evidence is missing or invalid.",
            {"approval_path": str(path), "exception": type(exc).__name__},
        ) from exc

    approved_codes = {str(code) for code in approval.get("approved_reason_codes", [])}
    required_codes = {str(code) for code in reason_codes}
    unapproved = sorted(required_codes - approved_codes)
    references = approval.get("business_change_references", [])
    errors = []
    if approval.get("status") != "APPROVED":
        errors.append("status")
    if str(approval.get("candidate_version")) != str(version):
        errors.append("candidate_version")
    if str(approval.get("candidate_sha256", "")).lower() != candidate_sha.lower():
        errors.append("candidate_sha256")
    if not isinstance(references, list) or not [item for item in references if str(item).strip()]:
        errors.append("business_change_references")
    if unapproved:
        errors.append("approved_reason_codes")

    if errors:
        raise PrModelPromotionError(
            "PR_MODEL_PROMOTION_APPROVAL_INVALID",
            "Approval evidence does not authorize all reviewed changes for this exact candidate.",
            {
                "approval_path": str(path),
                "invalid_fields": errors,
                "unapproved_reason_codes": unapproved,
                "candidate_version": version,
                "candidate_sha256": candidate_sha,
            },
        )
    return approval


def promote_pr_model(
    candidate_path: Path | str,
    version: str,
    *,
    root: Path | str | None = None,
    approval_path: Path | str | None = None,
) -> dict[str, Any]:
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

    candidate_bytes = candidate.read_bytes()
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    report = analyze_pr_model_change(current["path"], candidate)
    approval = None
    if report["status"] != "COMPATIBLE":
        if approval_path is None:
            raise PrModelPromotionError(
                "PR_MODEL_PROMOTION_REVIEW_REQUIRED",
                "Candidate cannot replace production until compatibility review is cleared.",
                {"candidate_path": str(candidate), "candidate_version": version, "compatibility": report},
            )
        approval = _load_review_approval(
            approval_path,
            root=repo_root,
            candidate_sha=candidate_sha,
            version=version,
            reason_codes=report.get("reason_codes", []),
        )

    production_path = current["expected_path"]
    config_path = repo_root / "config/pr_model_baseline.yaml"

    next_baseline = json.loads(json.dumps(baseline))
    next_baseline["model"]["version"] = str(version)
    next_baseline["workbook"]["path"] = str(baseline["workbook"]["path"])
    next_baseline["workbook"]["sha256"] = candidate_sha

    tracked_paths = [
        production_path,
        config_path,
        repo_root / "scripts/generate_tss_pr_ecc.py",
        repo_root / "scripts/run_tx_mini_ecc_parity.py",
        repo_root / "tests/test_jendela_approved_pr_model.py",
    ]
    snapshots = {path: path.read_bytes() for path in tracked_paths if path.exists()}

    try:
        production_path.write_bytes(candidate_bytes)
        config_path.write_text(json.dumps(next_baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        mirror_paths = _sync_legacy_hash_mirrors(repo_root, candidate_sha)
        validated = validate_pr_model_baseline(root=repo_root)
        regression = _run_regression_gate(repo_root)
    except Exception as exc:
        for path, payload in snapshots.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        if isinstance(exc, PrModelPromotionError):
            raise
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
        "approval": approval,
        "regression": regression,
        "legacy_hash_mirrors_updated": [str(path.relative_to(repo_root)) for path in mirror_paths],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a compatible or reviewed PR Model candidate.")
    parser.add_argument("candidate")
    parser.add_argument("--version", required=True)
    parser.add_argument("--approval", help="JSON approval evidence for reviewed compatibility changes")
    args = parser.parse_args()
    try:
        result = promote_pr_model(args.candidate, args.version, approval_path=args.approval)
    except PrModelPromotionError as exc:
        print(json.dumps({"status": "ERROR", "code": exc.code, "message": str(exc), "details": exc.details}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
