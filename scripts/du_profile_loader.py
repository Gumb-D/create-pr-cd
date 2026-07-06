"""DU export profile loading and structural validation.

Profiles are configuration only. A successful parse never means a profile is
production approved; the PR input gate enforces lifecycle and header-hash policy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

PROFILE_STATUSES = {"DRAFT", "PROFILED", "BUSINESS_VALIDATED", "PR_INPUT_READY", "PRODUCTION", "DEPRECATED"}
HEADER_HASH_POLICIES = {"strict"}
FINGERPRINT_KEYS = {"field_code", "wbs_stage", "task_name", "display_header"}


class ProfileValidationError(ValueError):
    """Raised when a DU profile is structurally invalid or unsafe to load."""


def _load_yaml_or_json(path: Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as error:
            raise ProfileValidationError(
                f"{path} uses YAML syntax. Install PyYAML or use JSON-compatible YAML for this foundation profile."
            ) from error
        return yaml.safe_load(text)


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileValidationError(f"{name} must be a mapping.")
    return value


def _require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileValidationError(f"{name} must be a non-empty string.")
    return value


def _require_string_list(value: Any, name: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ProfileValidationError(f"{name} must be a list of strings.")


def validate_du_profile(profile: Mapping[str, Any]) -> None:
    _require_string(profile.get("profile_id"), "profile_id")
    _require_string(profile.get("profile_version"), "profile_version")
    status = _require_string(profile.get("status"), "status")
    if status not in PROFILE_STATUSES:
        raise ProfileValidationError(f"status must be one of: {', '.join(sorted(PROFILE_STATUSES))}.")

    identity = _require_mapping(profile.get("identity"), "identity")
    _require_string(identity.get("project_key"), "identity.project_key")
    for field in ("accepted_du_models", "accepted_du_model_ids", "accepted_view_ids"):
        _require_string_list(identity.get(field), f"identity.{field}")

    export_structure = _require_mapping(profile.get("export_structure"), "export_structure")
    if export_structure.get("header_rows") != [0, 1, 2, 3]:
        raise ProfileValidationError("export_structure.header_rows must be exactly [0, 1, 2, 3].")
    policy = export_structure.get("header_hash_policy")
    if policy not in HEADER_HASH_POLICIES:
        raise ProfileValidationError("export_structure.header_hash_policy must be 'strict'.")
    _require_string_list(export_structure.get("approved_header_hashes"), "export_structure.approved_header_hashes")

    field_mapping = _require_mapping(profile.get("field_mapping"), "field_mapping")
    for canonical_field, config in field_mapping.items():
        config_mapping = _require_mapping(config, f"field_mapping.{canonical_field}")
        if not isinstance(config_mapping.get("required"), bool):
            raise ProfileValidationError(f"field_mapping.{canonical_field}.required must be boolean.")
        candidates = config_mapping.get("source_candidates")
        if not isinstance(candidates, list):
            raise ProfileValidationError(f"field_mapping.{canonical_field}.source_candidates must be a list.")
        for index, candidate in enumerate(candidates):
            candidate_mapping = _require_mapping(candidate, f"field_mapping.{canonical_field}.source_candidates[{index}]")
            fingerprint = _require_mapping(candidate_mapping.get("fingerprint"), "source candidate fingerprint")
            if set(fingerprint) != FINGERPRINT_KEYS:
                raise ProfileValidationError(
                    f"field_mapping.{canonical_field}.source_candidates[{index}].fingerprint must contain exactly {sorted(FINGERPRINT_KEYS)}."
                )
            if candidate_mapping.get("mapping_status") not in {"UNVERIFIED", "VERIFIED", "APPROVED"}:
                raise ProfileValidationError(
                    f"field_mapping.{canonical_field}.source_candidates[{index}].mapping_status must be UNVERIFIED, VERIFIED, or APPROVED."
                )

    if status == "PRODUCTION":
        approved_hashes = export_structure.get("approved_header_hashes", [])
        if not approved_hashes:
            raise ProfileValidationError("A PRODUCTION profile requires at least one approved header hash.")
        for canonical_field, config in field_mapping.items():
            if config.get("required") and not config.get("source_candidates"):
                raise ProfileValidationError(
                    f"A PRODUCTION profile cannot leave required field_mapping.{canonical_field} empty."
                )
            if config.get("required") and any(
                candidate.get("mapping_status") != "APPROVED" for candidate in config.get("source_candidates", [])
            ):
                raise ProfileValidationError(
                    f"A PRODUCTION profile requires APPROVED mappings for {canonical_field}."
                )


def load_du_profile(path: Path) -> Dict[str, Any]:
    profile = _load_yaml_or_json(Path(path))
    if not isinstance(profile, dict):
        raise ProfileValidationError(f"{path} must contain one mapping at the top level.")
    validate_du_profile(profile)
    return profile
