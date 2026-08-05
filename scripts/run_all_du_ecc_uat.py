#!/usr/bin/env python3
"""Public wrapper for the consolidated all-DU UAT implementation."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import all_du_uat_impl as _impl
from all_du_uat_impl import *  # noqa: F401,F403 - preserve the tested public module surface
from iepms_export_source_resolver import (
    LATEST_FILENAME_TIMESTAMP,
    discover_latest_source_exports,
    load_identity_registry,
)


_TESTABLE_DEPENDENCIES = (
    "load_input_manifest",
    "load_structured_profiles",
    "resolve_du_profile",
    "run_scope_pack",
    "deterministic_review_site_codes",
    "write_empty_review_summary",
    "write_master_manifest",
    "write_blocked_profiles",
    "materialize_scope_artifacts",
)

SOURCE_RESOLUTION_COLUMNS = (
    "Status",
    "Project Code",
    "Project Key",
    "Project Name",
    "DU Model",
    "Profile ID",
    "Profile Status",
    "View Name",
    "Export Timestamp",
    "Source Path",
    "Error Code",
    "Message",
)


def _is_windows() -> bool:
    return os.name == "nt"


def _absolute_path_string(path: Path | str) -> str:
    return os.path.abspath(os.fspath(path))


def _windows_extended_path(path: Path | str) -> str:
    raw_path = os.fspath(path)
    if not _is_windows():
        return _absolute_path_string(raw_path)
    if raw_path.startswith("\\\\?\\"):
        return raw_path
    path_str = _absolute_path_string(raw_path)
    if path_str.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path_str[2:]
    return "\\\\?\\" + path_str


def _strip_windows_extended_path(path: Path | str) -> str:
    path_str = os.fspath(path)
    if path_str.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path_str[len("\\\\?\\UNC\\") :]
    if path_str.startswith("\\\\?\\"):
        return path_str[len("\\\\?\\") :]
    return path_str


def _path_exists(path: Path | str) -> bool:
    candidate = _windows_extended_path(path) if _is_windows() else os.fspath(path)
    return os.path.exists(candidate)


def _path_is_file(path: Path | str) -> bool:
    candidate = _windows_extended_path(path) if _is_windows() else os.fspath(path)
    return os.path.isfile(candidate)


def _iter_materialization_files(engine_root: Path | str) -> list[Path]:
    root = _windows_extended_path(engine_root) if _is_windows() else os.fspath(engine_root)
    discovered: list[Path] = []
    for current, directories, filenames in os.walk(root):
        directories.sort(key=str.casefold)
        filenames.sort(key=str.casefold)
        logical_current = _strip_windows_extended_path(current) if _is_windows() else current
        discovered.extend(Path(logical_current) / filename for filename in filenames)
    return sorted(discovered, key=lambda path: _absolute_path_string(path).casefold())


def _path_safe_move(source: Path | str, target: Path | str) -> str:
    source_path = Path(source)
    target_path = Path(target)
    if _is_windows():
        os.makedirs(_windows_extended_path(target_path.parent), exist_ok=True)
        os.rename(_windows_extended_path(source_path), _windows_extended_path(target_path))
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(target_path)
    return str(target_path)


def _path_safe_rmtree(path: Path | str) -> None:
    candidate = _windows_extended_path(path) if _is_windows() else os.fspath(path)
    shutil.rmtree(candidate)


def materialize_scope_artifacts(engine_root, scope_dir, summary, pack_type, batch_run_id):
    """Materialize child files without normal-path Windows MAX_PATH operations."""

    engine_root = Path(engine_root)
    scope_dir = Path(scope_dir)
    if _is_windows():
        os.makedirs(_windows_extended_path(scope_dir), exist_ok=True)
    else:
        scope_dir.mkdir(parents=True, exist_ok=True)

    old_summary = summary.get("summary_path")
    old_summary_key = _absolute_path_string(old_summary) if old_summary else None
    path_map: dict[str, str] = {}
    generated_xlsx: list[Path] = []

    for source in _iter_materialization_files(engine_root):
        source_key = _absolute_path_string(source)
        if old_summary_key and source_key == old_summary_key:
            continue

        target = scope_dir / _impl._artifact_name(source, pack_type, batch_run_id)
        if _path_exists(target):
            raise _impl.BatchUatError(
                "UAT_ARTIFACT_COLLISION",
                "Batch UAT artefact target already exists.",
                {"source": str(source), "target": str(target)},
            )
        if not _path_is_file(source):
            raise _impl.BatchUatError(
                "UAT_ARTIFACT_SOURCE_MISSING",
                "Batch UAT artefact source is missing before materialisation.",
                {"source": str(source), "target": str(target)},
            )

        _path_safe_move(source, target)
        target_absolute = Path(_absolute_path_string(target))
        path_map[source_key] = str(target_absolute)
        if target.suffix.lower() == ".xlsx":
            generated_xlsx.append(target_absolute)

    if _path_exists(engine_root):
        _path_safe_rmtree(engine_root)

    adjusted = dict(summary)
    adjusted["pack_type"] = pack_type
    adjusted["batch_run_id"] = batch_run_id
    adjusted["output_root"] = _absolute_path_string(scope_dir)
    adjusted["created_files"] = [
        path_map[key]
        for path in summary.get("created_files", [])
        if (key := _absolute_path_string(path)) in path_map
    ]
    for key in ("review_report", "contract_mapping_review_report", "ignored_report"):
        old_value = summary.get(key)
        adjusted[key] = path_map.get(_absolute_path_string(old_value)) if old_value else None

    summary_path = scope_dir / (
        f"CREATE_PR_SUMMARY_{adjusted['scope']}_{pack_type}_"
        f"{_impl.UAT_MARKER}_{batch_run_id}.json"
    )
    adjusted["summary_path"] = _absolute_path_string(summary_path)
    summary_path.write_text(json.dumps(adjusted, ensure_ascii=False, indent=2), encoding="utf-8")
    return adjusted, sorted(generated_xlsx, key=lambda path: str(path).casefold())


def run_scope_pack(
    source_export,
    scope_dir,
    scope,
    pack_type,
    site_codes,
    profile_id,
    batch_run_id,
    args,
):
    """Render in a short temporary directory, then materialize into the final UAT evidence path."""

    scope_dir = Path(scope_dir)
    child_run_id = f"{batch_run_id}_{pack_type}_{scope}"
    with tempfile.TemporaryDirectory(prefix="create-pr-uat-") as temp_dir:
        engine_root = Path(temp_dir)
        parsed = _impl._create_pr_namespace(
            Path(source_export),
            engine_root,
            scope,
            site_codes,
            args,
            child_run_id,
        )
        summary = _impl.create_pr.run(parsed)
        return materialize_scope_artifacts(
            engine_root,
            scope_dir,
            summary,
            pack_type,
            batch_run_id,
        )


def _sync_testable_dependencies() -> None:
    """Propagate public test seams into the implementation module."""

    module_globals = globals()
    for name in _TESTABLE_DEPENDENCIES:
        public_value = module_globals.get(name)
        if public_value is not None and getattr(_impl, name, None) is not public_value:
            setattr(_impl, name, public_value)


def _load_manifest_payload(manifest_path: Path) -> dict:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _impl.BatchUatError(
            "UAT_INPUT_MANIFEST_INVALID",
            f"UAT input manifest is invalid: {manifest_path}",
            {"path": str(manifest_path), "error": str(error)},
        ) from error
    if not isinstance(payload, dict):
        raise _impl.BatchUatError(
            "UAT_INPUT_MANIFEST_INVALID",
            "UAT input manifest must contain a JSON object.",
            {"path": str(manifest_path)},
        )
    return payload


def resolve_v2_manifest_sources(
    manifest_path: Path,
    *,
    identity_registry_path: Path = _impl.IDENTITY_REGISTRY,
) -> tuple[dict, dict]:
    """Resolve schema 2.0 source roots into the existing schema 1.0 batch input."""

    manifest_path = Path(manifest_path).resolve()
    payload = _load_manifest_payload(manifest_path)
    if str(payload.get("schema_version", "")).strip() != "2.0":
        raise _impl.BatchUatError(
            "UAT_INPUT_MANIFEST_INVALID",
            "Source-root discovery requires UAT manifest schema_version 2.0.",
            {"path": str(manifest_path)},
        )
    if str(payload.get("selection_policy", "")).strip() != LATEST_FILENAME_TIMESTAMP:
        raise _impl.BatchUatError(
            "UAT_INPUT_MANIFEST_INVALID",
            f"schema 2.0 selection_policy must be {LATEST_FILENAME_TIMESTAMP}.",
            {"path": str(manifest_path)},
        )
    raw_roots = payload.get("source_roots")
    if not isinstance(raw_roots, list) or not raw_roots:
        raise _impl.BatchUatError(
            "UAT_INPUT_MANIFEST_INVALID",
            "schema 2.0 source_roots must be a non-empty list.",
            {"path": str(manifest_path)},
        )

    source_roots: list[Path] = []
    for raw_root in raw_roots:
        value = os.path.expandvars(str(raw_root or "").strip())
        if not value:
            raise _impl.BatchUatError(
                "UAT_INPUT_MANIFEST_INVALID",
                "schema 2.0 source root values must not be blank.",
                {"path": str(manifest_path)},
            )
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = manifest_path.parent / candidate
        source_roots.append(candidate.resolve())

    registry = load_identity_registry(identity_registry_path)
    discovery = discover_latest_source_exports(source_roots, registry)
    internal_manifest = {
        "schema_version": "1.0",
        "profiles": [
            {
                "profile_id": profile_id,
                "source_export": selection["source_path"],
            }
            for profile_id, selection in sorted(discovery["selections"].items())
        ],
    }
    return internal_manifest, discovery


def _write_source_resolution_csv(path: Path, discovery: dict) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_RESOLUTION_COLUMNS)
        writer.writeheader()
        for row in discovery.get("rows", []):
            source_path = row.get("source_path", "")
            if not source_path and row.get("source_paths"):
                source_path = json.dumps(row.get("source_paths"), ensure_ascii=False)
            writer.writerow(
                {
                    "Status": row.get("status", ""),
                    "Project Code": row.get("project_code", ""),
                    "Project Key": row.get("project_key", ""),
                    "Project Name": row.get("project_name", ""),
                    "DU Model": row.get("du_model_name", ""),
                    "Profile ID": row.get("profile_id", ""),
                    "Profile Status": row.get("profile_status", ""),
                    "View Name": row.get("view_name", ""),
                    "Export Timestamp": row.get("export_timestamp", ""),
                    "Source Path": source_path,
                    "Error Code": row.get("code", ""),
                    "Message": row.get("message", ""),
                }
            )


def _run_v2_batch(args, manifest_path: Path) -> dict:
    internal_manifest, discovery = resolve_v2_manifest_sources(manifest_path)
    with tempfile.TemporaryDirectory(prefix="create-pr-uat-manifest-") as temp_dir:
        internal_path = Path(temp_dir) / "resolved_manifest_v1.json"
        internal_path.write_text(
            json.dumps(internal_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        child_args = argparse.Namespace(**vars(args))
        child_args.manifest = internal_path
        summary = _impl.run_batch(child_args)

    output_root = Path(summary["output_root"])
    report_path = output_root / "UAT_SOURCE_RESOLUTION.csv"
    _write_source_resolution_csv(report_path, discovery)
    summary["input_manifest"] = str(manifest_path)
    summary["source_selection_policy"] = discovery["selection_policy"]
    summary["source_resolution_report"] = str(report_path.resolve())
    summary["source_resolution"] = discovery
    summary_path = output_root / "UAT_MASTER_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def run_batch(args):
    """Run schema 1.0 explicit paths or schema 2.0 automatic source discovery."""

    _sync_testable_dependencies()
    manifest_path = Path(args.manifest).resolve()
    payload = _load_manifest_payload(manifest_path)
    if str(payload.get("schema_version", "")).strip() == "2.0":
        summary = _run_v2_batch(args, manifest_path)
    else:
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
