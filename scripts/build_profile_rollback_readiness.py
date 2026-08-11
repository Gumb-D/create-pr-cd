"""Build a fail-closed rollback-readiness review for DU profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile


RELEASED_STATUSES = {"PR_INPUT_READY", "PRODUCTION", "DEPRECATED"}
DEFAULT_ROLLBACK_BASELINE_SOURCE = Path("config/registries/mw_du_profile_rollback_baselines_source.yaml")

# Independently governed prior-version requirements. These invariants deliberately
# do not live in the editable rollback-baseline evidence source, so malformed
# source data cannot disable the fail-closed guard it is meant to satisfy.
GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "jendela_tx_migration_pr_v1": {
        "current_profile_version": "0.5.0",
        "rollback_profile_id": "jendela_tx_migration_pr_v1",
        "rollback_profile_version": "0.4.0",
        "rollback_header_hashes": [
            "f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056"
        ],
    }
}


def _validate_governed_rollback_target(
    profile: Mapping[str, Any],
    rollback_target_profile_id: Any,
    rollback_target_profile_version: Any,
    rollback_target_header_hashes: list[str],
    blockers: list[str],
) -> None:
    """Enforce an independently governed rollback target for every lifecycle path."""
    governed_requirement = GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS.get(
        str(profile.get("profile_id", ""))
    )
    if governed_requirement is None:
        return

    if str(rollback_target_profile_id or "") != governed_requirement["rollback_profile_id"]:
        blockers.append("ROLLBACK_TARGET_PROFILE_ID_MISMATCH")
    if str(rollback_target_profile_version or "") != governed_requirement["rollback_profile_version"]:
        blockers.append("ROLLBACK_TARGET_PROFILE_VERSION_MISMATCH")
    if list(rollback_target_header_hashes) != list(governed_requirement["rollback_header_hashes"]):
        blockers.append("ROLLBACK_TARGET_HEADER_HASH_MISMATCH")


def _validate_explicit_rollback_baseline(
    profile: Mapping[str, Any],
    rollback_baseline_entry: Mapping[str, Any],
    blockers: list[str],
) -> tuple[Any, Any, list[str]]:
    current_profile_version = str(profile.get("profile_version", ""))
    baseline_current_version = str(rollback_baseline_entry.get("current_profile_version", ""))
    rollback_target_profile_id = rollback_baseline_entry.get("rollback_profile_id")
    rollback_target_profile_version = rollback_baseline_entry.get("rollback_profile_version")
    raw_rollback_header_hashes = rollback_baseline_entry.get("rollback_header_hashes", [])
    if not isinstance(raw_rollback_header_hashes, list):
        blockers.append("ROLLBACK_HEADER_HASHES_INVALID")
        rollback_target_header_hashes: list[str] = []
    else:
        rollback_target_header_hashes = list(raw_rollback_header_hashes)

    if baseline_current_version != current_profile_version:
        blockers.append("ROLLBACK_BASELINE_CURRENT_VERSION_MISMATCH")
    if not rollback_target_profile_id or not rollback_target_profile_version:
        blockers.append("NO_RECORDED_ROLLBACK_TARGET")
    if not rollback_target_header_hashes:
        blockers.append("NO_RECORDED_ROLLBACK_HEADER_HASHES")
    if str(rollback_target_profile_version or "") == current_profile_version:
        blockers.append("ROLLBACK_TARGET_IS_CURRENT_PROFILE_VERSION")

    return rollback_target_profile_id, rollback_target_profile_version, rollback_target_header_hashes


def evaluate_rollback_readiness(
    profile: Mapping[str, Any],
    deprecation_entry: Mapping[str, Any] | None,
    rollback_baseline_entry: Mapping[str, Any] | None = None,
    explicit_prior_baseline_required: bool = False,
) -> Dict[str, Any]:
    profile_id = str(profile.get("profile_id", ""))
    approved_header_hashes = list(profile.get("export_structure", {}).get("approved_header_hashes", []))
    blockers: list[str] = []
    governed_prior_baseline_required = profile_id in GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS

    if not approved_header_hashes:
        blockers.append("NO_APPROVED_HEADER_HASH_BASELINE")
    if str(profile.get("status", "")) not in RELEASED_STATUSES:
        blockers.append("PROFILE_NOT_RELEASED")

    governed_requirement = GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS.get(profile_id)
    if governed_requirement is not None and str(profile.get("profile_version", "")) != governed_requirement["current_profile_version"]:
        blockers.append("GOVERNED_ROLLBACK_CURRENT_VERSION_MISMATCH")

    rollback_target_profile_id = None
    rollback_target_profile_version = None
    rollback_target_header_hashes: list[str] = []
    review_notes: list[str] = []
    used_explicit_prior_baseline = False

    if str(profile.get("status", "")) == "DEPRECATED":
        if not isinstance(deprecation_entry, Mapping) or str(deprecation_entry.get("deprecation_status", "")) != "DEPRECATION_RECORDED":
            blockers.append("DEPRECATION_NOT_RECORDED")
        else:
            rollback_target_profile_id = deprecation_entry.get("rollback_profile_id")
            rollback_target_profile_version = deprecation_entry.get("rollback_profile_version")
            rollback_target_header_hashes = list(deprecation_entry.get("superseded_header_hashes", []))
            if not rollback_target_profile_id or not rollback_target_profile_version:
                blockers.append("NO_RECORDED_ROLLBACK_TARGET")
    else:
        if isinstance(rollback_baseline_entry, Mapping):
            used_explicit_prior_baseline = True
            (
                rollback_target_profile_id,
                rollback_target_profile_version,
                rollback_target_header_hashes,
            ) = _validate_explicit_rollback_baseline(profile, rollback_baseline_entry, blockers)
        elif governed_prior_baseline_required or explicit_prior_baseline_required:
            blockers.append("EXPLICIT_PRIOR_ROLLBACK_BASELINE_REQUIRED")
        elif approved_header_hashes:
            rollback_target_profile_id = profile.get("profile_id")
            rollback_target_profile_version = profile.get("profile_version")
            rollback_target_header_hashes = approved_header_hashes

    if governed_requirement is not None and (
        rollback_target_profile_id
        or rollback_target_profile_version
        or rollback_target_header_hashes
    ):
        _validate_governed_rollback_target(
            profile,
            rollback_target_profile_id,
            rollback_target_profile_version,
            rollback_target_header_hashes,
            blockers,
        )

    status = "ROLLBACK_BASELINE_RECORDED" if not blockers else "ROLLBACK_BLOCKED"
    if status == "ROLLBACK_BLOCKED":
        review_notes.append("Rollback remains blocked until an approved profile/header-hash baseline exists.")
    elif used_explicit_prior_baseline:
        review_notes.append("Rollback baseline is documented from an explicit prior approved profile identity and header-hash set.")
    else:
        review_notes.append("Rollback baseline is documented from the current approved profile identity and header-hash set.")

    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "current_status": profile["status"],
        "observed_header_hash": profile.get("export_structure", {}).get("observed_header_hash", ""),
        "rollback_readiness_status": status,
        "rollback_target_profile_id": rollback_target_profile_id,
        "rollback_target_profile_version": rollback_target_profile_version,
        "rollback_target_header_hashes": rollback_target_header_hashes,
        "blockers": blockers,
        "notes": review_notes,
    }


def _index_unique_registry_entries(entries: Iterable[Any]) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    duplicate_profile_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or entry.get("profile_id") is None:
            continue
        profile_id = str(entry["profile_id"])
        if profile_id in indexed:
            duplicate_profile_ids.add(profile_id)
            continue
        indexed[profile_id] = entry
    return indexed, duplicate_profile_ids


def _block_entries_for_duplicate_source_ids(
    entries: list[Dict[str, Any]],
    duplicate_profile_ids: set[str],
) -> None:
    if not duplicate_profile_ids:
        return

    duplicate_ids = sorted(duplicate_profile_ids)
    duplicate_note = (
        "Rollback remains blocked because the baseline source contains duplicate "
        f"profile IDs: {', '.join(duplicate_ids)}."
    )
    for entry in entries:
        if "DUPLICATE_ROLLBACK_BASELINE_ENTRIES" not in entry["blockers"]:
            entry["blockers"].append("DUPLICATE_ROLLBACK_BASELINE_ENTRIES")
        entry["rollback_readiness_status"] = "ROLLBACK_BLOCKED"
        entry["rollback_target_profile_id"] = None
        entry["rollback_target_profile_version"] = None
        entry["rollback_target_header_hashes"] = []
        entry["notes"] = [duplicate_note]


def build_rollback_registry(
    profiles: Iterable[Mapping[str, Any]],
    deprecation_registry: Mapping[str, Any],
    rollback_baseline_registry: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    deprecation_by_profile = {
        str(entry["profile_id"]): entry
        for entry in deprecation_registry.get("entries", [])
        if isinstance(entry, Mapping) and entry.get("profile_id") is not None
    }
    rollback_baseline_by_profile, duplicate_rollback_profile_ids = _index_unique_registry_entries(
        (rollback_baseline_registry or {}).get("entries", [])
    )
    source_required_profile_ids = {
        str(profile_id)
        for profile_id in (rollback_baseline_registry or {}).get("required_profile_ids", [])
        if profile_id is not None
    }

    entries: list[Dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile["profile_id"])
        duplicate_baseline = profile_id in duplicate_rollback_profile_ids
        entry = evaluate_rollback_readiness(
            profile,
            deprecation_by_profile.get(profile_id),
            None if duplicate_baseline else rollback_baseline_by_profile.get(profile_id),
            profile_id in source_required_profile_ids,
        )
        entries.append(entry)

    # Duplicate IDs make the rollback evidence source itself ambiguous. Block
    # the complete generated registry even when a duplicated ID is stale or
    # mistyped and therefore does not correspond to any currently loaded profile.
    _block_entries_for_duplicate_source_ids(entries, duplicate_rollback_profile_ids)

    registry: Dict[str, Any] = {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_rollback_readiness",
        "entries": entries,
        "notes": [
            "This rollback review is fail-closed and documents whether a profile has an approved rollback baseline.",
            "A blocked result does not imply a defect; it can simply mean the profile has not reached an approved release state yet.",
            "Explicit prior-version rollback baseline evidence is sourced from config/registries/mw_du_profile_rollback_baselines_source.yaml.",
            "Profiles that require an explicit prior baseline are independently governed in build_profile_rollback_readiness.py.",
        ],
    }
    if duplicate_rollback_profile_ids:
        registry["duplicate_rollback_profile_ids"] = sorted(duplicate_rollback_profile_ids)
    return registry


def rollback_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Rollback Readiness",
        "",
        "Discovery-only rollback-readiness review for tracked DU profiles.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']}")
        lines.append("")
        lines.append(f"- Rollback readiness status: `{entry['rollback_readiness_status']}`")
        lines.append(f"- Current status: `{entry['current_status']}`")
        lines.append(f"- Profile version: `{entry['profile_version']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry['observed_header_hash']}`")
        if entry.get("rollback_target_profile_id"):
            lines.append(
                f"- Rollback target: `{entry['rollback_target_profile_id']}` `{entry['rollback_target_profile_version']}`"
            )
        if entry.get("rollback_target_header_hashes"):
            lines.append(
                f"- Rollback target header hashes: `{', '.join(entry['rollback_target_header_hashes'])}`"
            )
        if entry.get("blockers"):
            lines.append(f"- Blockers: `{', '.join(entry['blockers'])}`")
        for note in entry.get("notes", []):
            lines.append(f"- Note: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_rollback_outputs(
    profile_paths: Iterable[Path],
    deprecation_registry_path: Path,
    registry_path: Path,
    markdown_path: Path,
    rollback_baseline_source_path: Path = DEFAULT_ROLLBACK_BASELINE_SOURCE,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    deprecation_registry = json.loads(deprecation_registry_path.read_text(encoding="utf-8"))
    rollback_baseline_registry = json.loads(rollback_baseline_source_path.read_text(encoding="utf-8"))
    registry = build_rollback_registry(profiles, deprecation_registry, rollback_baseline_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(rollback_markdown(registry), encoding="utf-8")


def main() -> int:
    write_rollback_outputs(
        discover_du_profile_paths(),
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
        Path("config/registries/mw_du_profile_rollback_readiness.yaml"),
        Path("docs/MW_DU_Profile_Rollback_Readiness.md"),
    )
    print("Wrote profile rollback readiness outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
