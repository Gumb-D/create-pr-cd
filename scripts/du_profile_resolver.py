#!/usr/bin/env python3
"""Resolve an approved DU profile from an original four-header iEPMS export."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from du_export_adapter import resolve_profile_field_mappings
from du_profile_loader import load_du_profile
from iepms_export_source_resolver import (
    SourceResolutionError,
    load_identity_registry,
    parse_iepms_export_filename,
    resolve_profile_route,
)
from profile_du_export import (
    build_header_inventory,
    extract_du_identities,
    resolve_approved_header_structure,
)


RUNNABLE_PROFILE_STATUSES = {"PR_INPUT_READY", "PRODUCTION"}


class DuProfileResolutionError(ValueError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _model_id_fallback_route(
    registry: Mapping[str, Any],
    detected: Mapping[str, str],
) -> dict[str, Any]:
    matches = [
        dict(entry)
        for entry in registry.get("profiles", [])
        if isinstance(entry, Mapping)
        and str(entry.get("du_model_id", "")) == detected["du_model_id"]
    ]
    if not matches:
        raise DuProfileResolutionError(
            "DU_PROFILE_NOT_FOUND",
            f"No DU Profile is registered for DU Model ID {detected['du_model_id']}.",
            dict(detected),
        )
    if len(matches) != 1:
        raise DuProfileResolutionError(
            "DU_PROFILE_IDENTITY_AMBIGUOUS",
            "More than one DU Profile is registered for the detected DU Model ID and Project identity is unavailable.",
            {
                **detected,
                "profile_ids": sorted(str(entry.get("profile_id", "")) for entry in matches),
                "project_keys": sorted(str(entry.get("project_key", "")) for entry in matches),
            },
        )
    return matches[0]


def resolve_du_profile(
    input_path: Path,
    *,
    profile_root: Path,
    identity_registry_path: Path,
) -> dict[str, Any]:
    input_path = Path(input_path)
    inventory = build_header_inventory(input_path)
    identities = extract_du_identities(inventory)
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
        registry_entry = _model_id_fallback_route(registry, detected)
        selection_basis = "DU_MODEL_ID_FALLBACK"

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
    if filename_identity is not None and str(identity.get("project_key", "")) != filename_identity["project_key"]:
        raise DuProfileResolutionError(
            "DU_PROFILE_IDENTITY_MISMATCH",
            "DU Profile Project Key does not match the source filename identity.",
            {"profile_id": profile_id, **filename_identity},
        )

    header_validation = resolve_approved_header_structure(inventory, profile)
    required_field_approval = None
    if not header_validation["approved"]:
        mappings = resolve_profile_field_mappings(inventory, profile)
        required_fields = {
            name: config
            for name, config in profile.get("field_mapping", {}).items()
            if config.get("required")
        }
        failures = {}
        for name in required_fields:
            resolution = mappings.get(name, {"status": "MISSING", "matches": []})
            matches = resolution.get("matches", [])
            if (
                resolution.get("status") != "RESOLVED"
                or not matches
                or any(match.get("mapping_status") != "APPROVED" for match in matches)
            ):
                failures[name] = resolution.get("status", "MISSING")
        if not failures:
            required_field_approval = {
                name: [match["fingerprint"] for match in mappings[name]["matches"]]
                for name in required_fields
            }
            header_validation = {
                **header_validation,
                "approved": True,
                "approved_header_hash": None,
                "approval_basis": "REQUIRED_APPROVED_FIELDS_RESOLVED",
            }
        else:
            header_validation = {**header_validation, "required_field_failures": failures}
    if not header_validation["approved"]:
        raise DuProfileResolutionError(
            "HEADER_HASH_REVALIDATION_REQUIRED",
            f"The export structure does not match an approved header layout for {profile_id}.",
            {
                "profile_id": profile_id,
                "actual_header_hash": header_validation["raw_header_hash"],
                "structural_header_hash": header_validation["structural_header_hash"],
                "approval_basis": header_validation["approval_basis"],
            },
        )

    result = {
        "profile": profile,
        "profile_path": profile_path,
        "registry_entry": registry_entry,
        "inventory": inventory,
        "header_hash": header_validation["raw_header_hash"],
        "raw_header_hash": header_validation["raw_header_hash"],
        "structural_header_hash": header_validation["structural_header_hash"],
        "approved_header_hash": header_validation["approved_header_hash"],
        "header_hash_approval_basis": header_validation["approval_basis"],
        "profile_selection_basis": selection_basis,
        "required_field_approval": required_field_approval,
        **detected,
    }
    if filename_identity is not None:
        result.update(filename_identity)
    return result