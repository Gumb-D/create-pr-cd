#!/usr/bin/env python3
"""Public wrapper for the consolidated all-DU UAT implementation."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import all_du_uat_impl as _impl
from all_du_uat_impl import *  # noqa: F401,F403 - preserve the tested public module surface


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


def _sync_testable_dependencies() -> None:
    """Propagate public test seams into the implementation module."""

    module_globals = globals()
    for name in _TESTABLE_DEPENDENCIES:
        public_value = module_globals.get(name)
        if public_value is not None and getattr(_impl, name, None) is not public_value:
            setattr(_impl, name, public_value)


def run_batch(args):
    """Run the batch and classify any blocked profile as a controlled block."""

    _sync_testable_dependencies()
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
