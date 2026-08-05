"""Fail-closed consistency checks across generated MW DU discovery artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from du_profile_loader import ProfileValidationError, load_du_profile, load_du_profiles

EXPECTED_TRACEABILITY_ARTIFACT_IDS = (
    "discovery",
    "unresolved",
    "bridge",
    "readiness",
    "action_queue",
    "review_matrix",
    "coverage",
    "transition",
    "deprecation",
    "rollback",
)


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_by_profile(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for entry in registry.get("entries", []):
        if not isinstance(entry, Mapping) or entry.get("profile_id") is None:
            continue
        profile_id = str(entry["profile_id"])
        if profile_id in index:
            raise ProfileValidationError(
                f"Profile-centric registry contains duplicate entries for {profile_id}."
            )
        index[profile_id] = entry
    return index


def _group_by_profile(registry: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for entry in registry.get("entries", []):
        if not isinstance(entry, Mapping) or entry.get("profile_id") is None:
            continue
        grouped.setdefault(str(entry["profile_id"]), []).append(entry)
    return grouped


def _known_header_hashes(profile: Mapping[str, Any]) -> set[str]:
    structure = profile.get("export_structure", {})
    values = {str(structure.get("observed_header_hash", "")).strip()}
    for field in ("observed_header_hashes", "approved_header_hashes"):
        values.update(str(value).strip() for value in structure.get(field, []) or [])
    return {value for value in values if value}


def _primary_discovery_entry(
    profile: Mapping[str, Any],
    entries: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    primary_hash = str(profile.get("export_structure", {}).get("observed_header_hash", "")).strip()
    matches = [entry for entry in entries if str(entry.get("observed_header_hash", "")).strip() == primary_hash]
    if len(matches) != 1:
        raise ProfileValidationError(
            f"Discovery registry primary-layout mismatch for {profile.get('profile_id')}: "
            f"expected exactly one entry for {primary_hash}, found {len(matches)}"
        )
    return matches[0]


def _expected_untracked_coverage_status(discovery_entry: Mapping[str, Any]) -> str:
    presence = discovery_entry.get("skill_field_presence", {})
    if isinstance(presence, Mapping) and presence.get("existing_tss_pr") and presence.get("existing_ti_pr"):
        return "DONOR_REVIEW_CANDIDATE"
    return "BACKLOG_DISCOVERY_ONLY"


def _expected_missing_skill_fields(discovery_entry: Mapping[str, Any]) -> list[str]:
    presence = discovery_entry.get("skill_field_presence", {})
    if not isinstance(presence, Mapping):
        return []
    return sorted(str(field) for field, present in presence.items() if present is False)


def validate_discovery_packet_consistency(
    profiles: Iterable[Mapping[str, Any]],
    discovery_registry: Mapping[str, Any],
    unresolved_registry: Mapping[str, Any],
    readiness_registry: Mapping[str, Any],
    transition_registry: Mapping[str, Any],
    bridge_registry: Mapping[str, Any],
    deprecation_registry: Mapping[str, Any],
    traceability_registry: Mapping[str, Any],
    rollback_registry: Mapping[str, Any],
    coverage_registry: Mapping[str, Any],
) -> None:
    discovery_entries_by_profile = _group_by_profile(discovery_registry)
    unresolved_by_profile = _index_by_profile(unresolved_registry)
    readiness_by_profile = _index_by_profile(readiness_registry)
    transition_by_profile = _index_by_profile(transition_registry)
    bridge_by_profile = _index_by_profile(bridge_registry)
    deprecation_by_profile = _index_by_profile(deprecation_registry)
    traceability_by_profile = _index_by_profile(traceability_registry)
    rollback_by_profile = _index_by_profile(rollback_registry)
    coverage_by_source = {
        str(entry.get("source_file_name")): entry
        for entry in coverage_registry.get("entries", [])
        if isinstance(entry, Mapping) and entry.get("source_file_name") is not None
    }
    coverage_entries = [
        entry for entry in coverage_registry.get("entries", [])
        if isinstance(entry, Mapping)
    ]

    for profile in profiles:
        profile_id = str(profile["profile_id"])
        mapping_version = str(profile["mapping_version"])
        status = str(profile["status"])
        observed_header_hash = str(profile.get("export_structure", {}).get("observed_header_hash", ""))

        for name, index in (
            ("unresolved", unresolved_by_profile),
            ("readiness", readiness_by_profile),
            ("transition", transition_by_profile),
            ("bridge", bridge_by_profile),
            ("deprecation", deprecation_by_profile),
            ("traceability", traceability_by_profile),
            ("rollback", rollback_by_profile),
        ):
            if profile_id not in index:
                raise ProfileValidationError(f"Profile {profile_id} is missing from the {name} registry.")

        discovery_entries = discovery_entries_by_profile.get(profile_id, [])
        if not discovery_entries:
            raise ProfileValidationError(f"Profile {profile_id} is missing from the discovery registry.")
        known_hashes = _known_header_hashes(profile)
        for discovery_candidate in discovery_entries:
            if str(discovery_candidate.get("profile_status")) != status:
                raise ProfileValidationError(
                    f"Discovery registry status mismatch for {profile_id}: "
                    f"{discovery_candidate.get('profile_status')} != {status}"
                )
            packet_hash = str(discovery_candidate.get("observed_header_hash", "")).strip()
            if packet_hash not in known_hashes:
                raise ProfileValidationError(
                    f"Discovery registry header-hash mismatch for {profile_id}: "
                    f"{packet_hash} is not registered as observed or approved"
                )
        discovery_entry = _primary_discovery_entry(profile, discovery_entries)

        unresolved_entry = unresolved_by_profile[profile_id]
        if str(unresolved_entry.get("profile_status")) != status:
            raise ProfileValidationError(
                f"Unresolved review status mismatch for {profile_id}: {unresolved_entry.get('profile_status')} != {status}"
            )
        if str(unresolved_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Unresolved review header-hash mismatch for {profile_id}: {unresolved_entry.get('observed_header_hash')} != {observed_header_hash}"
            )

        readiness_entry = readiness_by_profile[profile_id]
        if str(readiness_entry.get("profile_status")) != status:
            raise ProfileValidationError(
                f"Readiness review status mismatch for {profile_id}: {readiness_entry.get('profile_status')} != {status}"
            )
        if str(readiness_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Readiness review mapping-version mismatch for {profile_id}: {readiness_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(readiness_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Readiness review header-hash mismatch for {profile_id}: {readiness_entry.get('observed_header_hash')} != {observed_header_hash}"
            )

        transition_entry = transition_by_profile[profile_id]
        if str(transition_entry.get("current_status")) != status:
            raise ProfileValidationError(
                f"Transition review status mismatch for {profile_id}: {transition_entry.get('current_status')} != {status}"
            )
        if str(transition_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Transition review mapping-version mismatch for {profile_id}: {transition_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(transition_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Transition review header-hash mismatch for {profile_id}: {transition_entry.get('observed_header_hash')} != {observed_header_hash}"
            )

        bridge_entry = bridge_by_profile[profile_id]
        if str(bridge_entry.get("profile_version")) != str(profile.get("profile_version", "")):
            raise ProfileValidationError(
                f"Bridge review profile-version mismatch for {profile_id}: {bridge_entry.get('profile_version')} != {profile.get('profile_version', '')}"
            )
        if str(bridge_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Bridge review mapping-version mismatch for {profile_id}: {bridge_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(bridge_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Bridge review header-hash mismatch for {profile_id}: {bridge_entry.get('observed_header_hash')} != {observed_header_hash}"
            )
        unresolved_missing = sorted(unresolved_entry.get("summary", {}).get("missing_required_fields", []))
        bridge_fields = sorted(bridge_entry.get("field_bridges", {}).keys())
        if unresolved_missing != bridge_fields:
            raise ProfileValidationError(
                f"Bridge review field mismatch for {profile_id}: {bridge_fields} != {unresolved_missing}"
            )

        deprecation_entry = deprecation_by_profile[profile_id]
        if str(deprecation_entry.get("current_status")) != status:
            raise ProfileValidationError(
                f"Deprecation review status mismatch for {profile_id}: {deprecation_entry.get('current_status')} != {status}"
            )
        if str(deprecation_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Deprecation review mapping-version mismatch for {profile_id}: {deprecation_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(deprecation_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Deprecation review header-hash mismatch for {profile_id}: {deprecation_entry.get('observed_header_hash')} != {observed_header_hash}"
            )

        traceability_entry = traceability_by_profile[profile_id]
        if str(traceability_entry.get("profile_version")) != str(profile.get("profile_version", "")):
            raise ProfileValidationError(
                f"Traceability audit profile-version mismatch for {profile_id}: {traceability_entry.get('profile_version')} != {profile.get('profile_version', '')}"
            )
        if str(traceability_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Traceability audit mapping-version mismatch for {profile_id}: {traceability_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(traceability_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Traceability audit header-hash mismatch for {profile_id}: {traceability_entry.get('observed_header_hash')} != {observed_header_hash}"
            )
        if str(traceability_entry.get("traceability_status")) != "TRACEABLE":
            raise ProfileValidationError(
                f"Traceability audit status mismatch for {profile_id}: {traceability_entry.get('traceability_status')} != TRACEABLE"
            )
        traceability_artifacts = list(traceability_entry.get("artifacts", []))
        artifact_ids = [
            str(artifact.get("artifact_id"))
            for artifact in traceability_artifacts
            if isinstance(artifact, Mapping)
        ]
        if sorted(artifact_ids) != sorted(EXPECTED_TRACEABILITY_ARTIFACT_IDS):
            raise ProfileValidationError(
                f"Traceability audit artifact coverage mismatch for {profile_id}: {sorted(artifact_ids)} != {sorted(EXPECTED_TRACEABILITY_ARTIFACT_IDS)}"
            )
        for artifact in traceability_artifacts:
            if str(artifact.get("artifact_status")) != "TRACEABLE":
                raise ProfileValidationError(
                    f"Traceability audit artifact mismatch for {profile_id} {artifact.get('artifact_id')}: {artifact.get('artifact_status')} != TRACEABLE"
                )

        rollback_entry = rollback_by_profile[profile_id]
        if str(rollback_entry.get("current_status")) != status:
            raise ProfileValidationError(
                f"Rollback review status mismatch for {profile_id}: {rollback_entry.get('current_status')} != {status}"
            )
        if str(rollback_entry.get("profile_version")) != str(profile.get("profile_version", "")):
            raise ProfileValidationError(
                f"Rollback review profile-version mismatch for {profile_id}: {rollback_entry.get('profile_version')} != {profile.get('profile_version', '')}"
            )
        if str(rollback_entry.get("mapping_version")) != mapping_version:
            raise ProfileValidationError(
                f"Rollback review mapping-version mismatch for {profile_id}: {rollback_entry.get('mapping_version')} != {mapping_version}"
            )
        if str(rollback_entry.get("observed_header_hash")) != observed_header_hash:
            raise ProfileValidationError(
                f"Rollback review header-hash mismatch for {profile_id}: {rollback_entry.get('observed_header_hash')} != {observed_header_hash}"
            )

        for discovery_candidate in discovery_entries:
            source_file_name = str(discovery_candidate.get("source_file_name", ""))
            coverage_entry = coverage_by_source.get(source_file_name)
            if coverage_entry is None:
                raise ProfileValidationError(
                    f"Coverage review is missing source file {source_file_name} for profile {profile_id}."
                )
            if str(coverage_entry.get("coverage_status")) != "TRACKED_DRAFT_PROFILE":
                raise ProfileValidationError(
                    f"Coverage review tracked-profile mismatch for {profile_id}: "
                    f"{coverage_entry.get('coverage_status')} != TRACKED_DRAFT_PROFILE"
                )
            if str(coverage_entry.get("profile_id")) != profile_id:
                raise ProfileValidationError(
                    f"Coverage review tracked-profile mismatch for {profile_id}: "
                    f"{coverage_entry.get('profile_id')} != {profile_id}"
                )
            if str(coverage_entry.get("profile_version")) != str(profile.get("profile_version", "")):
                raise ProfileValidationError(
                    f"Coverage review profile-version mismatch for {profile_id}: "
                    f"{coverage_entry.get('profile_version')} != {profile.get('profile_version', '')}"
                )
            if str(coverage_entry.get("mapping_version")) != mapping_version:
                raise ProfileValidationError(
                    f"Coverage review mapping-version mismatch for {profile_id}: "
                    f"{coverage_entry.get('mapping_version')} != {mapping_version}"
                )
            expected_hash = str(discovery_candidate.get("observed_header_hash", ""))
            if str(coverage_entry.get("observed_header_hash")) != expected_hash:
                raise ProfileValidationError(
                    f"Coverage review header-hash mismatch for {profile_id}: "
                    f"{coverage_entry.get('observed_header_hash')} != {expected_hash}"
                )

    for discovery_entry in discovery_registry.get("entries", []):
        if not isinstance(discovery_entry, Mapping):
            continue
        if discovery_entry.get("profile_id") is not None:
            continue
        source_file_name = str(discovery_entry.get("source_file_name", ""))
        coverage_entry = coverage_by_source.get(source_file_name)
        if coverage_entry is None:
            raise ProfileValidationError(f"Coverage review is missing untracked source file {source_file_name}.")
        expected_status = _expected_untracked_coverage_status(discovery_entry)
        if str(coverage_entry.get("coverage_status")) != expected_status:
            raise ProfileValidationError(
                f"Coverage review donor/backlog mismatch for {source_file_name}: {coverage_entry.get('coverage_status')} != {expected_status}"
            )
        if coverage_entry.get("profile_id") is not None:
            raise ProfileValidationError(
                f"Coverage review untracked source file {source_file_name} must not claim profile_id {coverage_entry.get('profile_id')}."
            )
        if str(coverage_entry.get("observed_header_hash")) != str(discovery_entry.get("observed_header_hash", "")):
            raise ProfileValidationError(
                f"Coverage review header-hash mismatch for {source_file_name}: {coverage_entry.get('observed_header_hash')} != {discovery_entry.get('observed_header_hash', '')}"
            )
        expected_missing = _expected_missing_skill_fields(discovery_entry)
        actual_missing = sorted(str(field) for field in coverage_entry.get("missing_skill_fields", []))
        if actual_missing != expected_missing:
            raise ProfileValidationError(
                f"Coverage review missing-skill-fields mismatch for {source_file_name}: {actual_missing} != {expected_missing}"
            )

    summary = coverage_registry.get("summary", {})
    expected_counts = {
        "total_exports": len(coverage_entries),
        "tracked_profile_exports": sum(
            1 for entry in coverage_entries if str(entry.get("coverage_status")) == "TRACKED_DRAFT_PROFILE"
        ),
        "donor_review_candidates": sum(
            1 for entry in coverage_entries if str(entry.get("coverage_status")) == "DONOR_REVIEW_CANDIDATE"
        ),
        "backlog_discovery_only_exports": sum(
            1 for entry in coverage_entries if str(entry.get("coverage_status")) == "BACKLOG_DISCOVERY_ONLY"
        ),
    }
    for key, expected_value in expected_counts.items():
        if int(summary.get(key, -1)) != expected_value:
            raise ProfileValidationError(
                f"Coverage review summary mismatch for {key}: {summary.get(key)} != {expected_value}"
            )


def validate_live_discovery_packets() -> None:
    profiles = load_du_profiles()
    validate_discovery_packet_consistency(
        profiles,
        _load_json(Path("config/registries/mw_du_model_discovery_registry.yaml")),
        _load_json(Path("config/registries/mw_du_unresolved_skill_field_review.yaml")),
        _load_json(Path("config/registries/mw_du_profile_readiness_review.yaml")),
        _load_json(Path("config/registries/mw_du_profile_transition_review.yaml")),
        _load_json(Path("config/registries/mw_du_missing_field_bridge_review.yaml")),
        _load_json(Path("config/registries/mw_du_profile_deprecation_review.yaml")),
        _load_json(Path("config/registries/mw_du_profile_traceability_audit.yaml")),
        _load_json(Path("config/registries/mw_du_profile_rollback_readiness.yaml")),
        _load_json(Path("config/registries/mw_du_export_coverage_review.yaml")),
    )


if __name__ == "__main__":
    validate_live_discovery_packets()
    print("Discovery packet consistency check passed.")
