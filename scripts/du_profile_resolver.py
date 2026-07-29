#!/usr/bin/env python3
"""Resolve an approved DU profile from an original four-header iEPMS export."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from du_profile_loader import load_du_profile
from profile_du_export import build_header_inventory, calculate_header_hash


RUNNABLE_PROFILE_STATUSES = {"PR_INPUT_READY", "PRODUCTION"}


class DuProfileResolutionError(ValueError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _load_registry(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
    registry = _load_registry(identity_registry_path)
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

    registry_entry = matches[0]
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
    if detected["du_model_id"] not in {str(value) for value in identity.get("accepted_du_model_ids", [])}:
        raise DuProfileResolutionError("DU_PROFILE_IDENTITY_MISMATCH", "DU Profile model ID does not match the export.")
    if detected["view_id"] not in {str(value) for value in identity.get("accepted_view_ids", [])}:
        raise DuProfileResolutionError("DU_PROFILE_IDENTITY_MISMATCH", "DU Profile view ID does not match the export.")

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

    return {
        "profile": profile,
        "profile_path": profile_path,
        "registry_entry": registry_entry,
        "inventory": inventory,
        "header_hash": header_hash,
        **detected,
    }
