#!/usr/bin/env python3
"""Resolve an approved DU profile from an original four-header iEPMS export."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from du_profile_loader import load_du_profile
from iepms_export_source_resolver import (
    SourceResolutionError,
    load_identity_registry,
    parse_iepms_export_filename,
    resolve_profile_route,
)
from profile_du_export import build_header_inventory, calculate_header_hash


RUNNABLE_PROFILE_STATUSES = {"PR_INPUT_READY", "PRODUCTION"}


class DuProfileResolutionError(ValueError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _extract_du_identities(inventory: Mapping[str, Any]) -> list[dict[str, str]]:
    identities: dict[tuple[str, str], dict[str, str]] = {}
    for sheet in inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            fingerprint = column.get("fingerprint", {})
            parts = str(fingerprint.get("field_code", "")).split("|")
            if len(parts) < 4 or parts[0:2] != ["site", "fix00012"]:
                continue
            du_model_id, view_id = parts[-2], parts[-1]
            identities[(du_model_id, view_id)] = {
                "du_model_id": du_model_id,
                "view_id": view_id,
                "sheet_name": str(sheet.get("sheet_name", "")),
            }
    return list(identities.values())


def _legacy_model_view_route(
    registry: Mapping[str, Any],
    detected: Mapping[str, str],
) -> dict[str, Any]:
    model_entries = [
        entry
        for entry in registry.get("profiles", [])
        if str(entry.get("du_model_id", "")) == detected["du_model_id"]
    ]
    matches = [
        entry
        for entry in model_entries
        if detected["view_id"] in {str(value) for value in entry.get("accepted_view_ids", [])}
    ]
    if not matches:
        code = "DU_PROFILE_VIEW_NOT_APPROVED" if model_entries else "DU_PROFILE_NOT_FOUND"
        raise DuProfileResolutionError(
            code,
            (
                f"No approved DU Profile matches model {detected['du_model_id']} "
                f"and view {detected['view_id']}."
            ),
            {
                **detected,
                "registered_view_ids": sorted(
                    {
                        str(view_id)
                        for entry in model_entries
                        for view_id in entry.get("accepted_view_ids", [])
                    }
                ),
            },
        )
    if len(matches) != 1:
        raise DuProfileResolutionError(
            "DU_PROFILE_AMBIGUOUS",
            "More than one DU Profile matches the detected model/view identity.",
            {"profile_ids": [entry.get("profile_id") for entry in matches], **detected},
        )
    return dict(matches[0])


def resolve_du_profile(
    input_path: Path,
    *,
    profile_root: Path,
    identity_registry_path: Path,
) -> dict[str, Any]:
    input_path = Path(input_path)
    inventory = build_header_inventory(input_path)
    identities = _extract_du_identities(inventory)
    if len(identities) != 1:
        raise DuProfileResolutionError(
            "DU_IDENTITY_NOT_UNIQUE",
            "The iEPMS export must contain exactly one DU model/view identity.",
            {"detected_identities": identities},
        )

    detected = identities[0]
    registry = load_identity_registry(identity_registry_path)
    filename_identity: dict[str, str] | None = None
    try:
        filename_identity = parse_iepms_export_filename(input_path, registry)
    except SourceResolutionError as error:
        if error.code != "IEPMS_FILENAME_INVALID":
            raise DuProfileResolutionError(error.code, str(error), error.details) from error

    if filename_identity is not None:
        try:
            registry_entry = resolve_profile_route(
                registry,
                project_key=filename_identity["project_key"],
                du_model_name=filename_identity["du_model_name"],
            )
        except SourceResolutionError as error:
            raise DuProfileResolutionError(error.code, str(error), error.details) from error
        registered_model_id = str(registry_entry.get("du_model_id", ""))
        if detected["du_model_id"] != registered_model_id:
            raise DuProfileResolutionError(
                "SOURCE_FILENAME_WORKBOOK_IDENTITY_MISMATCH",
                "The filename Project + DU Model route does not match the workbook DU Model ID.",
                {
                    **filename_identity,
                    **detected,
                    "registered_du_model_id": registered_model_id,
                    "profile_id": registry_entry.get("profile_id"),
                },
            )
        selection_basis = "PROJECT_AND_DU_MODEL"
    else:
        registry_entry = _legacy_model_view_route(registry, detected)
        selection_basis = "DU_MODEL_AND_VIEW_LEGACY_FALLBACK"

    profile_id = str(registry_entry["profile_id"])
    profile_path = Path(profile_root) / f"{profile_id}.yaml"
    if not profile_path.exists():
        raise DuProfileResolutionError(
            "DU_PROFILE_FILE_MISSING",
            f"Registered DU Profile file is missing: {profile_path}",
            {"profile_id": profile_id},
        )

    profile = load_du_profile(profile_path)
    profile_status = str(profile.get("status", ""))
    if profile_status not in RUNNABLE_PROFILE_STATUSES:
        raise DuProfileResolutionError(
            "DU_PROFILE_NOT_RUNNABLE",
            f"DU Profile {profile_id} has non-runnable status {profile_status}.",
            {"profile_id": profile_id, "profile_status": profile_status},
        )

    identity = profile.get("identity", {})
    accepted_model_ids = {str(value) for value in identity.get("accepted_du_model_ids", [])}
    if detected["du_model_id"] not in accepted_model_ids:
        raise DuProfileResolutionError(
            "DU_PROFILE_IDENTITY_MISMATCH",
            "DU Profile model ID does not match the export.",
            {"profile_id": profile_id, **detected},
        )
    if filename_identity is not None:
        if str(identity.get("project_key", "")) != filename_identity["project_key"]:
            raise DuProfileResolutionError(
                "DU_PROFILE_IDENTITY_MISMATCH",
                "DU Profile Project Key does not match the source filename identity.",
                {"profile_id": profile_id, **filename_identity},
            )
    else:
        accepted_view_ids = {str(value) for value in identity.get("accepted_view_ids", [])}
        if detected["view_id"] not in accepted_view_ids:
            raise DuProfileResolutionError(
                "DU_PROFILE_IDENTITY_MISMATCH",
                "DU Profile view ID does not match the legacy export identity.",
            )

    header_hash = calculate_header_hash(inventory)
    approved_hashes = {
        str(value) for value in profile.get("export_structure", {}).get("approved_header_hashes", [])
    }
    if header_hash not in approved_hashes:
        raise DuProfileResolutionError(
            "HEADER_HASH_REVALIDATION_REQUIRED",
            f"The export structure does not match the approved header hash for {profile_id}.",
            {"profile_id": profile_id, "actual_header_hash": header_hash},
        )

    result = {
        "profile": profile,
        "profile_path": profile_path,
        "registry_entry": registry_entry,
        "inventory": inventory,
        "header_hash": header_hash,
        "profile_selection_basis": selection_basis,
        **detected,
    }
    if filename_identity is not None:
        result.update(filename_identity)
    return result
