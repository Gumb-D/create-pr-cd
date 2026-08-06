#!/usr/bin/env python3
"""Auto-routing entry point for canonical generator-compatible UAT packets.

The implementation remains in ``canonical_generator_bridge_impl``. This public
entry point resolves the authoritative DU Profile from Project + DU Model before
building any records. An optional ``--profile`` is an assertion only and cannot
override the automatically resolved profile.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping

import canonical_generator_bridge_impl as _impl
from canonical_generator_bridge_impl import *  # noqa: F401,F403 - preserve public API
from du_profile_loader import load_du_profile
from du_profile_resolver import resolve_du_profile
from profile_du_export import build_header_inventory, calculate_header_hash


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_ROOT = REPO_ROOT / "config" / "du_profiles"
DEFAULT_IDENTITY_REGISTRY = (
    REPO_ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
)


def __getattr__(name: str):
    """Preserve access to implementation helpers used by existing callers/tests."""
    return getattr(_impl, name)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build generator-compatible UAT packets and automatically resolve "
            "the DU Profile from Project + DU Model."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to DU export file")
    parser.add_argument(
        "--profile",
        type=Path,
        default=None,
        help="Optional expected DU Profile path; assertion only, never a routing override",
    )
    parser.add_argument(
        "--profile-root",
        type=Path,
        default=DEFAULT_PROFILE_ROOT,
        help="Directory containing registered DU Profile YAML files",
    )
    parser.add_argument(
        "--identity-registry",
        type=Path,
        default=DEFAULT_IDENTITY_REGISTRY,
        help="Project + DU Model identity registry",
    )
    parser.add_argument(
        "--scope",
        required=True,
        choices=["TSS", "TI", "tss", "ti"],
        help="Scope (TSS or TI)",
    )
    parser.add_argument(
        "--sow-registry",
        required=True,
        type=Path,
        help="Path to canonical SOW registry file",
    )
    parser.add_argument(
        "--scope-config",
        type=Path,
        default=None,
        help="Path to scope eligibility config JSON file",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    return parser.parse_args(args)


def _assert_expected_profile(
    expected_profile_path: Path | None,
    resolved_profile: Mapping[str, object],
) -> None:
    if expected_profile_path is None:
        return
    expected_profile_path = Path(expected_profile_path)
    if not expected_profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {expected_profile_path}")
    expected_profile = load_du_profile(expected_profile_path)
    expected_profile_id = str(expected_profile.get("profile_id", ""))
    resolved_profile_id = str(resolved_profile.get("profile_id", ""))
    if expected_profile_id != resolved_profile_id:
        raise ValueError("DU_PROFILE_IDENTITY_MISMATCH")


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    if not parsed.input.exists():
        raise FileNotFoundError(f"Input file not found: {parsed.input}")
    if not parsed.profile_root.is_dir():
        raise FileNotFoundError(f"DU Profile directory not found: {parsed.profile_root}")
    if not parsed.identity_registry.is_file():
        raise FileNotFoundError(
            f"DU Profile identity registry not found: {parsed.identity_registry}"
        )
    if not parsed.sow_registry.exists():
        raise FileNotFoundError(f"SOW registry file not found: {parsed.sow_registry}")

    resolution = resolve_du_profile(
        parsed.input,
        profile_root=parsed.profile_root,
        identity_registry_path=parsed.identity_registry,
    )
    resolved_profile = resolution["profile"]
    resolved_profile_path = Path(resolution["profile_path"])
    _assert_expected_profile(parsed.profile, resolved_profile)

    scope_config = None
    if parsed.scope_config:
        if not parsed.scope_config.exists():
            raise FileNotFoundError(f"Scope config file not found: {parsed.scope_config}")
        scope_config = _impl._load_json_or_yaml(parsed.scope_config)
        if isinstance(scope_config, Mapping) and "scopes" in scope_config:
            scope_config = scope_config["scopes"]

    records, metadata = _impl.build_records_from_export(
        input_path=parsed.input,
        profile_path=resolved_profile_path,
        scope=parsed.scope.upper(),
        sow_registry_path=parsed.sow_registry,
        scope_config=scope_config,
    )
    outputs = _impl.write_uat_packet(
        records=records,
        metadata=metadata,
        output_dir=parsed.output,
        scope=parsed.scope.upper(),
    )

    workbook_path = outputs["workbook"]
    summary_path = outputs["summary_json"]
    if not workbook_path.exists() or not summary_path.exists():
        raise RuntimeError("Expected UAT packet outputs were not generated successfully.")

    result_summary = {
        "status": "SUCCESS",
        "records": len(records),
        "scope": parsed.scope.upper(),
        "ecc_allowed": False,
        "resolved_profile_id": resolved_profile["profile_id"],
        "resolved_profile_path": str(resolved_profile_path.resolve()),
        "profile_selection_basis": resolution["profile_selection_basis"],
        "project_key": resolution.get("project_key", metadata.get("project_key", "")),
        "du_model_name": resolution.get("du_model_name", metadata.get("du_model_name", "")),
        "du_model_id": resolution.get("du_model_id", metadata.get("du_model_id", "")),
        "view_name": resolution.get("view_name", ""),
        "view_id": resolution.get("view_id", metadata.get("view_id", "")),
        "raw_header_hash": resolution.get("raw_header_hash", metadata.get("raw_header_hash", "")),
        "structural_header_hash": resolution.get(
            "structural_header_hash",
            metadata.get("structural_header_hash", ""),
        ),
        "approved_header_hash": resolution.get(
            "approved_header_hash",
            metadata.get("approved_header_hash", ""),
        ),
        "header_hash_approval_basis": resolution.get(
            "header_hash_approval_basis",
            metadata.get("header_hash_approval_basis", ""),
        ),
        "generated_output_paths": {
            "workbook": str(workbook_path.resolve()),
            "summary_json": str(summary_path.resolve()),
        },
    }
    print(json.dumps(result_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(
            json.dumps(
                {"status": "ERROR", "error": str(error)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        sys.exit(1)
