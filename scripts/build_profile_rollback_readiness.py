"""Build a fail-closed rollback-readiness review for DU profiles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile

RELEASED_STATUSES = {"PR_INPUT_READY", "PRODUCTION", "DEPRECATED"}
DEFAULT_ROLLBACK_BASELINE_SOURCE = Path("config/registries/mw_du_profile_rollback_baselines_source.yaml")
REPO_ROOT = Path(__file__).resolve().parent.parent

GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "jendela_tx_migration_pr_v1": {
        "current_profile_version": "0.5.0",
        "rollback_profile_id": "jendela_tx_migration_pr_v1",
        "rollback_profile_version": "0.4.0",
        "rollback_header_hashes": ["f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056"],
        "rollback_profile_artifact_path": "config/du_profiles/archive/jendela_tx_migration_pr_v1_0.4.0.yaml",
        "rollback_profile_blob_sha": "f6226b676c0d6905988d6379040ec76f6e066ca9",
        "rollback_source_commit_sha": "6f0253edad2a4bb3abfef838e918379110bbd046",
    }
}


def _validate_governed_rollback_target(profile, rollback_target_profile_id, rollback_target_profile_version, rollback_target_header_hashes, blockers):
    requirement = GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS.get(str(profile.get("profile_id", "")))
    if requirement is None:
        return
    if str(rollback_target_profile_id or "") != requirement["rollback_profile_id"]:
        blockers.append("ROLLBACK_TARGET_PROFILE_ID_MISMATCH")
    if str(rollback_target_profile_version or "") != requirement["rollback_profile_version"]:
        blockers.append("ROLLBACK_TARGET_PROFILE_VERSION_MISMATCH")
    if list(rollback_target_header_hashes) != list(requirement["rollback_header_hashes"]):
        blockers.append("ROLLBACK_TARGET_HEADER_HASH_MISMATCH")


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _validate_governed_rollback_artifact(profile, baseline, blockers):
    requirement = GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS.get(str(profile.get("profile_id", "")))
    if requirement is None:
        return
    path_text = str(baseline.get("rollback_profile_artifact_path", "") or "")
    expected_blob = str(baseline.get("rollback_profile_blob_sha", "") or "")
    source_commit = str(baseline.get("rollback_source_commit_sha", "") or "")
    if path_text != requirement["rollback_profile_artifact_path"]:
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_PATH_MISMATCH")
    if expected_blob != requirement["rollback_profile_blob_sha"]:
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_BLOB_MISMATCH")
    if source_commit != requirement["rollback_source_commit_sha"]:
        blockers.append("ROLLBACK_PROFILE_SOURCE_COMMIT_MISMATCH")
    if not path_text:
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_MISSING")
        return
    artifact_path = (REPO_ROOT / path_text).resolve()
    try:
        artifact_path.relative_to(REPO_ROOT)
    except ValueError:
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_PATH_INVALID")
        return
    if not artifact_path.is_file():
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_MISSING")
        return
    artifact_bytes = artifact_path.read_bytes()
    if _git_blob_sha(artifact_bytes) != expected_blob:
        if "ROLLBACK_PROFILE_ARTIFACT_BLOB_MISMATCH" not in blockers:
            blockers.append("ROLLBACK_PROFILE_ARTIFACT_BLOB_MISMATCH")
        return
    try:
        archived = json.loads(artifact_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_INVALID")
        return
    if not isinstance(archived, Mapping):
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_INVALID")
        return
    if str(archived.get("profile_id", "")) != str(baseline.get("rollback_profile_id", "")):
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_IDENTITY_MISMATCH")
    if str(archived.get("profile_version", "")) != str(baseline.get("rollback_profile_version", "")):
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_VERSION_MISMATCH")
    archived_hashes = list(archived.get("export_structure", {}).get("approved_header_hashes", []))
    raw_hashes = baseline.get("rollback_header_hashes", [])
    target_hashes = raw_hashes if isinstance(raw_hashes, list) else []
    if archived_hashes != list(target_hashes):
        blockers.append("ROLLBACK_PROFILE_ARTIFACT_HEADER_HASH_MISMATCH")


def _valid_hash_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_explicit_rollback_baseline(profile, baseline, blockers):
    current_version = str(profile.get("profile_version", ""))
    baseline_current_version = str(baseline.get("current_profile_version", ""))
    target_id = baseline.get("rollback_profile_id")
    target_version = baseline.get("rollback_profile_version")
    raw_hashes = baseline.get("rollback_header_hashes", [])
    if not _valid_hash_list(raw_hashes):
        blockers.append("ROLLBACK_HEADER_HASHES_INVALID")
        target_hashes: list[str] = []
    else:
        target_hashes = list(raw_hashes)
    if baseline_current_version != current_version:
        blockers.append("ROLLBACK_BASELINE_CURRENT_VERSION_MISMATCH")
    if not target_id or not target_version:
        blockers.append("NO_RECORDED_ROLLBACK_TARGET")
    if not target_hashes:
        blockers.append("NO_RECORDED_ROLLBACK_HEADER_HASHES")
    if str(target_version or "") == current_version:
        blockers.append("ROLLBACK_TARGET_IS_CURRENT_PROFILE_VERSION")
    _validate_governed_rollback_artifact(profile, baseline, blockers)
    return target_id, target_version, target_hashes


def evaluate_rollback_readiness(profile, deprecation_entry, rollback_baseline_entry=None, explicit_prior_baseline_required=False) -> Dict[str, Any]:
    profile_id = str(profile.get("profile_id", ""))
    approved_hashes = list(profile.get("export_structure", {}).get("approved_header_hashes", []))
    blockers: list[str] = []
    governed_required = profile_id in GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS
    if not approved_hashes:
        blockers.append("NO_APPROVED_HEADER_HASH_BASELINE")
    if str(profile.get("status", "")) not in RELEASED_STATUSES:
        blockers.append("PROFILE_NOT_RELEASED")
    requirement = GOVERNED_PRIOR_ROLLBACK_REQUIREMENTS.get(profile_id)
    if requirement is not None and str(profile.get("profile_version", "")) != requirement["current_profile_version"]:
        blockers.append("GOVERNED_ROLLBACK_CURRENT_VERSION_MISMATCH")

    target_id = None
    target_version = None
    target_hashes: list[str] = []
    notes: list[str] = []
    used_explicit = False
    if str(profile.get("status", "")) == "DEPRECATED":
        if not isinstance(deprecation_entry, Mapping) or str(deprecation_entry.get("deprecation_status", "")) != "DEPRECATION_RECORDED":
            blockers.append("DEPRECATION_NOT_RECORDED")
        else:
            target_id = deprecation_entry.get("rollback_profile_id")
            target_version = deprecation_entry.get("rollback_profile_version")
            raw = deprecation_entry.get("superseded_header_hashes", [])
            target_hashes = list(raw) if _valid_hash_list(raw) else []
            if not target_id or not target_version:
                blockers.append("NO_RECORDED_ROLLBACK_TARGET")
    else:
        if isinstance(rollback_baseline_entry, Mapping):
            used_explicit = True
            target_id, target_version, target_hashes = _validate_explicit_rollback_baseline(profile, rollback_baseline_entry, blockers)
        elif governed_required or explicit_prior_baseline_required:
            blockers.append("EXPLICIT_PRIOR_ROLLBACK_BASELINE_REQUIRED")
        elif approved_hashes:
            target_id = profile.get("profile_id")
            target_version = profile.get("profile_version")
            target_hashes = approved_hashes

    if requirement is not None and (target_id or target_version or target_hashes):
        _validate_governed_rollback_target(profile, target_id, target_version, target_hashes, blockers)
    status = "ROLLBACK_BASELINE_RECORDED" if not blockers else "ROLLBACK_BLOCKED"
    if status == "ROLLBACK_BLOCKED":
        notes.append("Rollback remains blocked until an approved profile/header-hash baseline exists.")
    elif used_explicit:
        notes.append("Rollback baseline is documented from an explicit prior approved profile identity and header-hash set.")
    else:
        notes.append("Rollback baseline is documented from the current approved profile identity and header-hash set.")
    return {
        "profile_id": profile["profile_id"], "profile_version": profile["profile_version"], "mapping_version": profile["mapping_version"],
        "current_status": profile["status"], "observed_header_hash": profile.get("export_structure", {}).get("observed_header_hash", ""),
        "rollback_readiness_status": status, "rollback_target_profile_id": target_id, "rollback_target_profile_version": target_version,
        "rollback_target_header_hashes": target_hashes, "blockers": blockers, "notes": notes,
    }


def _index_unique_registry_entries(entries: Iterable[Any]):
    indexed: dict[str, Mapping[str, Any]] = {}
    duplicates: set[str] = set()
    invalid_indexes: set[int] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("profile_id"), str) or not str(entry.get("profile_id", "")).strip():
            invalid_indexes.add(index)
            continue
        profile_id = str(entry["profile_id"])
        if profile_id in indexed:
            duplicates.add(profile_id)
            continue
        indexed[profile_id] = entry
    return indexed, duplicates, invalid_indexes


def _source_collection(registry, name, invalid_collections):
    raw = (registry or {}).get(name, [])
    if not isinstance(raw, list):
        invalid_collections.add(name)
        return []
    return raw


def _force_block(entries, blocker, note):
    for entry in entries:
        if blocker not in entry["blockers"]:
            entry["blockers"].append(blocker)
        entry["rollback_readiness_status"] = "ROLLBACK_BLOCKED"
        entry["rollback_target_profile_id"] = None
        entry["rollback_target_profile_version"] = None
        entry["rollback_target_header_hashes"] = []
        entry["notes"] = [note]


def build_rollback_registry(profiles, deprecation_registry, rollback_baseline_registry=None) -> Dict[str, Any]:
    deprecation_by_profile = {
        str(entry["profile_id"]): entry for entry in deprecation_registry.get("entries", [])
        if isinstance(entry, Mapping) and entry.get("profile_id") is not None
    }
    invalid_collections: set[str] = set()
    source_entries = _source_collection(rollback_baseline_registry, "entries", invalid_collections)
    required_ids = _source_collection(rollback_baseline_registry, "required_profile_ids", invalid_collections)
    baseline_by_profile, duplicate_ids, invalid_entry_indexes = _index_unique_registry_entries(source_entries)
    source_required_ids = {str(x) for x in required_ids if x is not None}

    entries: list[Dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile["profile_id"])
        entry = evaluate_rollback_readiness(
            profile,
            deprecation_by_profile.get(profile_id),
            None if profile_id in duplicate_ids else baseline_by_profile.get(profile_id),
            profile_id in source_required_ids,
        )
        entries.append(entry)

    if duplicate_ids:
        _force_block(entries, "DUPLICATE_ROLLBACK_BASELINE_ENTRIES", "Rollback remains blocked because the baseline source contains duplicate profile IDs: " + ", ".join(sorted(duplicate_ids)) + ".")
    if invalid_collections:
        _force_block(entries, "ROLLBACK_BASELINE_SOURCE_COLLECTION_INVALID", "Rollback remains blocked because baseline source collections are malformed: " + ", ".join(sorted(invalid_collections)) + ".")
    if invalid_entry_indexes:
        _force_block(entries, "ROLLBACK_BASELINE_SOURCE_ENTRY_INVALID", "Rollback remains blocked because baseline source contains malformed entries at indexes: " + ", ".join(str(i) for i in sorted(invalid_entry_indexes)) + ".")

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
    if duplicate_ids:
        registry["duplicate_rollback_profile_ids"] = sorted(duplicate_ids)
    if invalid_collections:
        registry["invalid_rollback_source_collections"] = sorted(invalid_collections)
    if invalid_entry_indexes:
        registry["invalid_rollback_source_entry_indexes"] = sorted(invalid_entry_indexes)
    return registry


def rollback_markdown(registry: Mapping[str, Any]) -> str:
    lines = ["# MW DU Profile Rollback Readiness", "", "Discovery-only rollback-readiness review for tracked DU profiles.", ""]
    for entry in registry.get("entries", []):
        lines.extend([
            f"## {entry['profile_id']}", "",
            f"- Rollback readiness status: `{entry['rollback_readiness_status']}`",
            f"- Current status: `{entry['current_status']}`",
            f"- Profile version: `{entry['profile_version']}`",
            f"- Mapping version: `{entry['mapping_version']}`",
            f"- Observed header hash: `{entry['observed_header_hash']}`",
        ])
        if entry.get("rollback_target_profile_id"):
            lines.append(f"- Rollback target: `{entry['rollback_target_profile_id']}` `{entry['rollback_target_profile_version']}`")
        if entry.get("rollback_target_header_hashes"):
            lines.append(f"- Rollback target header hashes: `{', '.join(entry['rollback_target_header_hashes'])}`")
        if entry.get("blockers"):
            lines.append(f"- Blockers: `{', '.join(entry['blockers'])}`")
        for note in entry.get("notes", []):
            lines.append(f"- Note: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_rollback_outputs(profile_paths, deprecation_registry_path, registry_path, markdown_path, rollback_baseline_source_path=DEFAULT_ROLLBACK_BASELINE_SOURCE):
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
