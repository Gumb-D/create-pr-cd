#!/usr/bin/env python3
"""AI Worker Platform contract entrypoint for the standalone create-pr-cd skill."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import create_pr  # noqa: E402


CONTRACT_VERSION = "1.0"
SKILL_ID = "create-pr-cd"
SKILL_VERSION = "4.0.0"


class ContractError(Exception):
    def __init__(self, code: str, message: str, category: str = "domain_input", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.category = category
        self.details = details or {}


class CancelledError(ContractError):
    def __init__(self, message: str = "Cancellation was requested."):
        super().__init__("SKILL_CANCELLED", message, "cancelled")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def emit(event_type: str, phase: str, message: str, percent: int | None = None) -> None:
    event: dict[str, Any] = {
        "type": event_type,
        "timestamp": utc_now(),
        "phase": phase,
        "message": message,
    }
    if percent is not None:
        event["percent"] = percent
    print(json.dumps(event, ensure_ascii=False), flush=True)


def start_progress_heartbeat(phase: str, message: str, seconds: int = 30):
    stopped = threading.Event()
    def heartbeat() -> None:
        while not stopped.wait(seconds):
            emit("progress", phase, message)
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    return stopped


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run create-pr-cd using the AI Worker Platform skill contract.")
    parser.add_argument("--input-manifest", required=True, type=Path)
    return parser.parse_args()


def resolve_inside(workspace: Path, value: Any, label: str) -> Path:
    raw = str(value or "").strip()
    if not raw or Path(raw).is_absolute():
        raise ContractError("CONTRACT_PATH_INVALID", f"{label} must be a workspace-relative path.")
    resolved = (workspace / raw).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ContractError("CONTRACT_PATH_INVALID", f"{label} escapes the workspace.") from exc
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_envelope(path: Path) -> tuple[dict[str, Any], Path, Path, Path, Path]:
    manifest_path = path.resolve()
    if not manifest_path.is_file():
        raise ContractError("INPUT_MANIFEST_NOT_FOUND", "The input manifest was not found.")
    try:
        envelope = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("INPUT_MANIFEST_INVALID", "The input manifest is not valid JSON.") from exc
    if envelope.get("schemaVersion") != CONTRACT_VERSION:
        raise ContractError("CONTRACT_VERSION_UNSUPPORTED", "Unsupported input contract version.")
    skill = envelope.get("skill") or {}
    if skill.get("skillId") != SKILL_ID or skill.get("version") != SKILL_VERSION:
        raise ContractError("SKILL_IDENTITY_MISMATCH", "Input manifest skill identity does not match this package.")
    if not str(envelope.get("jobId") or "").strip():
        raise ContractError("JOB_ID_REQUIRED", "jobId is required.")

    paths = envelope.get("paths") or {}
    workspace = resolve_inside(manifest_path.parent, paths.get("workspace", "."), "paths.workspace")
    output = resolve_inside(workspace, paths.get("output", "output"), "paths.output")
    result = resolve_inside(workspace, paths.get("result", "result.json"), "paths.result")
    cancellation = resolve_inside(workspace, paths.get("cancellation", "control/cancel.requested"), "paths.cancellation")
    output.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    return envelope, workspace, output, result, cancellation


def declared_file(envelope: dict[str, Any], workspace: Path, name: str) -> Path:
    matches = [item for item in envelope.get("files", []) if item.get("name") == name]
    if len(matches) != 1:
        raise ContractError("INPUT_FILE_INVALID", f"Exactly one {name} file is required.")
    item = matches[0]
    path = resolve_inside(workspace, item.get("path"), f"files.{name}.path")
    if not path.is_file() or path.suffix.lower() != ".xlsx":
        raise ContractError("INPUT_FILE_INVALID", f"{name} must be an existing .xlsx file.")
    if item.get("size") is not None and int(item["size"]) != path.stat().st_size:
        raise ContractError("INPUT_FILE_SIZE_MISMATCH", f"{name} size does not match its declaration.")
    if item.get("sha256") and str(item["sha256"]).lower() != sha256(path):
        raise ContractError("INPUT_FILE_CHECKSUM_MISMATCH", f"{name} checksum does not match its declaration.")
    return path


def check_cancel(cancellation: Path) -> None:
    if cancellation.exists():
        raise CancelledError()


def output_item(path: Path, workspace: Path) -> dict[str, Any]:
    return {
        "name": path.stem,
        "path": path.resolve().relative_to(workspace).as_posix(),
        "mediaType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "displayName": path.name,
        "size": path.stat().st_size,
        "sha256": sha256(path),
    }


def reconciliation(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "requestedCount": int(summary.get("requested_count", 0) or 0),
        "generatedCount": int(summary.get("generated_count", 0) or 0),
        "reviewRequiredCount": int(summary.get("review_required_count", 0) or 0),
        "approvedIgnoredCount": int(summary.get("approved_ignored_count", 0) or 0),
        "duplicateBlockedCount": int(summary.get("duplicate_blocked_count", 0) or 0),
        "failedCount": int(summary.get("failed_count", 0) or 0),
        "unaccountedCount": int(summary.get("unaccounted_count", 0) or 0),
    }


def safe_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "run_mode", "profile_status", "scope", "profile_id", "profile_version",
        "mapping_version", "project_key", "du_model_name", "du_model_id", "view_id",
        "source_record_count", "selected_record_count", "candidate_count", "duplicate_count",
        "ignored_count", "ignored_reason_distribution", "review_required_count",
        "review_required_reason_distribution", "contract_mapping_missing_count",
        "sm_excluded_count", "pr_model_baseline",
    )
    return {field: summary[field] for field in fields if field in summary}


def run_domain(parsed: argparse.Namespace, cancellation: Path) -> dict[str, Any]:
    command = [
        sys.executable, str(SKILL_ROOT / "scripts" / "create_pr.py"),
        "--site-data", str(parsed.site_data), "--output", str(parsed.output),
        "--scope", parsed.scope,
    ]
    if parsed.all_sites:
        command.append("--all-sites")
    else:
        command.extend(["--site-code", parsed.site_code])
    if parsed.non_production_uat:
        command.append("--non-production-uat")
    workspace = cancellation.parent.parent
    log_dir = workspace / "temp"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / "create-pr.stdout.log"
    stderr_path = log_dir / "create-pr.stderr.log"
    with stdout_path.open("wb") as stdout_log, stderr_path.open("wb") as stderr_log:
        process = subprocess.Popen(
            command,
            cwd=SKILL_ROOT,
            stdout=stdout_log,
            stderr=stderr_log,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        while process.poll() is None:
            if cancellation.exists():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise CancelledError()
            time.sleep(0.2)
    if process.returncode != 0:
        raise ContractError(
            "CREATE_PR_FAILED",
            "create-pr-cd rejected the input or failed during domain processing.",
            "domain_processing",
            {"exitCode": process.returncode},
        )
    summaries = sorted(parsed.output.rglob("CREATE_PR_SUMMARY_*.json"), key=lambda item: item.stat().st_mtime_ns)
    if not summaries:
        raise ContractError("CREATE_PR_RESULT_MISSING", "create-pr-cd did not write its domain summary.", "domain_processing")
    return json.loads(summaries[-1].read_text(encoding="utf-8"))


def write_result(result_path: Path, payload: dict[str, Any]) -> None:
    temp = result_path.with_suffix(result_path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, result_path)


def run(input_manifest: Path) -> int:
    envelope: dict[str, Any] = {}
    result_path = input_manifest.resolve().parent / "result.json"
    cancellation = input_manifest.resolve().parent / "control" / "cancel.requested"
    try:
        envelope, workspace, output, result_path, cancellation = load_envelope(input_manifest)
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(CancelledError()))
        check_cancel(cancellation)
        emit("progress", "contract_validation", "Validated the skill request.", 5)
        site_data = declared_file(envelope, workspace, "site_data")
        parameters = envelope.get("parameters") or {}
        allowed = {"scope", "allSites", "siteCodes", "nonProductionUat"}
        unknown = sorted(set(parameters) - allowed)
        if unknown:
            raise ContractError("PARAMETERS_INVALID", "Unsupported parameters were supplied.", details={"fields": unknown})
        scope = str(parameters.get("scope") or "").upper()
        if scope not in {"TSS", "TI"}:
            raise ContractError("PARAMETERS_INVALID", "scope must be TSS or TI.")
        site_codes = [str(value).strip() for value in parameters.get("siteCodes", []) if str(value).strip()]
        all_sites = bool(parameters.get("allSites", False))
        if all_sites == bool(site_codes):
            raise ContractError("PARAMETERS_INVALID", "Use exactly one of allSites or siteCodes.")

        parsed = argparse.Namespace(
            site_data=site_data,
            output=output,
            scope=scope,
            site_code=",".join(site_codes) if site_codes else None,
            all_sites=all_sites,
            pr_model=SKILL_ROOT / "Info" / "input" / "pr_model.xlsx",
            template=SKILL_ROOT / "Info" / "input" / "ecc_template.xls",
            mapping=SKILL_ROOT / "Info" / "input" / "contract_info_reference.md",
            subcontractor_policy=SKILL_ROOT / "config" / "subcontractor_pr_policy.json",
            non_production_uat=bool(parameters.get("nonProductionUat", False)),
        )
        emit("progress", "domain_processing", "Creating PR deliverables.", 15)
        progress_heartbeat = start_progress_heartbeat("domain_processing", "PR processing is still running.")
        try:
            summary = run_domain(parsed, cancellation)
        finally:
            progress_heartbeat.set()
        check_cancel(cancellation)
        emit("progress", "result_packaging", "Packaging declared outputs.", 95)
        candidates = []
        for raw in list(summary.get("created_files", [])) + [
            summary.get("summary_path"), summary.get("review_report"),
            summary.get("contract_mapping_review_report"), summary.get("ignored_report"),
        ]:
            if raw:
                path = Path(raw).resolve()
                if path.is_file() and path not in candidates:
                    path.relative_to(output.resolve())
                    candidates.append(path)
        rec = reconciliation(summary)
        warning_count = rec["reviewRequiredCount"] + rec["approvedIgnoredCount"] + rec["duplicateBlockedCount"]
        status = "succeeded_with_warning" if warning_count else "succeeded"
        payload = {
            "schemaVersion": CONTRACT_VERSION,
            "jobId": envelope["jobId"],
            "skillId": SKILL_ID,
            "skillVersion": SKILL_VERSION,
            "status": status,
            "summary": {"message": "PR processing completed.", "metrics": safe_metrics(summary)},
            "reconciliation": rec,
            "outputs": [output_item(path, workspace) for path in candidates],
            "warnings": ([{"code": "DOMAIN_REVIEW_REQUIRED", "message": "Some requested sites require review or were not generated.", "details": rec}] if warning_count else []),
            "error": None,
        }
        write_result(result_path, payload)
        emit("progress", "completed", "PR processing completed.", 100)
        return 0
    except CancelledError as exc:
        status, exit_code = "cancelled", 130
        error = exc
    except ContractError as exc:
        status, exit_code = "failed", 2
        error = exc
    except Exception as exc:
        status, exit_code = "failed", 4
        code = getattr(exc, "code", "CREATE_PR_FAILED")
        details = getattr(exc, "details", {})
        error = ContractError(code, str(exc), "domain_processing", details)

    payload = {
        "schemaVersion": CONTRACT_VERSION,
        "jobId": str(envelope.get("jobId") or "unknown"),
        "skillId": SKILL_ID,
        "skillVersion": SKILL_VERSION,
        "status": status,
        "summary": {"message": str(error), "metrics": {}},
        "outputs": [],
        "warnings": [],
        "error": {"code": error.code, "category": error.category, "message": str(error), "retryable": False, "details": error.details},
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    write_result(result_path, payload)
    emit("warning", status, str(error))
    return exit_code


def main() -> int:
    args = parse_cli()
    return run(args.input_manifest)


if __name__ == "__main__":
    raise SystemExit(main())
