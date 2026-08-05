"""Fail-closed consistency checks between profile status and transition review.

This module verifies that a profile file does not claim a lifecycle status that
the current transition-review evidence does not support.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, ProfileValidationError, load_du_profile

STATUS_REQUIREMENTS = {
    "DRAFT": (),
    "PROFILED": ("PROFILED",),
    "BUSINESS_VALIDATED": ("PROFILED", "BUSINESS_VALIDATED"),
    "PR_INPUT_READY": ("PROFILED", "BUSINESS_VALIDATED", "PR_INPUT_READY"),
    "PRODUCTION": ("PRODUCTION",),
    "DEPRECATED": ("PRODUCTION",),
}


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _transition_map(transition_entry: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {
        str(item["target_status"]): item
        for item in transition_entry.get("transition_targets", [])
        if isinstance(item, Mapping)
    }


def _deprecation_allowed(deprecation_entry: Mapping[str, Any] | None) -> bool:
    if not isinstance(deprecation_entry, Mapping):
        return False
    return str(deprecation_entry.get("deprecation_status", "")) == "DEPRECATION_RECORDED"


def validate_profile_status_consistency(
    profile: Mapping[str, Any],
    transition_entry: Mapping[str, Any],
    deprecation_entry: Mapping[str, Any] | None = None,
) -> None:
    status = str(profile.get("status", ""))
    required_targets = STATUS_REQUIREMENTS.get(status)
    if required_targets is None:
        raise ProfileValidationError(f"Unsupported status for consistency check: {status}")
    if not required_targets:
        return

    transitions = _transition_map(transition_entry)
    failed_targets = []
    for target in required_targets:
        result = transitions.get(target)
        if result is None:
            failed_targets.append(f"{target}:MISSING_REVIEW_ENTRY")
            continue
        if not result.get("eligible", False):
            reasons = ",".join(str(reason) for reason in result.get("denied_reasons", []))
            failed_targets.append(f"{target}:{reasons or 'DENIED'}")

    if failed_targets:
        profile_id = profile.get("profile_id", "<unknown>")
        raise ProfileValidationError(
            f"Profile {profile_id} declares status {status}, but transition review denies: {'; '.join(failed_targets)}"
        )
    if status == "DEPRECATED" and not _deprecation_allowed(deprecation_entry):
        profile_id = profile.get("profile_id", "<unknown>")
        raise ProfileValidationError(
            f"Profile {profile_id} declares status DEPRECATED, but deprecation review is not recorded."
        )


def validate_profiles_against_transition_registry(
    profile_paths: Iterable[Path],
    transition_registry_path: Path,
    deprecation_registry_path: Path | None = None,
) -> None:
    registry = _load_json(transition_registry_path)
    by_profile = {
        str(entry["profile_id"]): entry for entry in registry.get("entries", [])
    }
    deprecation_by_profile: Dict[str, Mapping[str, Any]] = {}
    if deprecation_registry_path is not None:
        deprecation_registry = _load_json(deprecation_registry_path)
        deprecation_by_profile = {
            str(entry["profile_id"]): entry for entry in deprecation_registry.get("entries", [])
        }
    for path in profile_paths:
        profile = load_du_profile(path)
        transition_entry = by_profile.get(str(profile["profile_id"]))
        if transition_entry is None:
            raise ProfileValidationError(f"No transition review entry found for profile {profile['profile_id']}")
        validate_profile_status_consistency(
            profile,
            transition_entry,
            deprecation_by_profile.get(str(profile["profile_id"])),
        )


if __name__ == "__main__":
    validate_profiles_against_transition_registry(
        discover_du_profile_paths(),
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
    )
    print("Profile status consistency check passed.")
