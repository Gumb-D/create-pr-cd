"""Compatibility-aware consistency checks for historical approved DU packets."""
from __future__ import annotations

import copy

import check_discovery_packet_consistency_impl as _impl
from check_discovery_packet_consistency_impl import *  # noqa: F401,F403


_ORIGINAL_VALIDATE = _impl.validate_discovery_packet_consistency


def _packet_compatible_profiles(profiles, discovery_registry):
    """Validate historical packet hashes without rewriting live Profile identity.

    Discovery artifacts may retain an approved historical source layout while
    profile-centric governance tracks the configured current layout. Every
    packet hash must still be explicitly registered as observed or approved.
    """

    live_profiles = list(profiles)
    entries_by_profile = _impl._group_by_profile(discovery_registry)
    for profile in live_profiles:
        profile_id = str(profile.get("profile_id", ""))
        discovery_entries = entries_by_profile.get(profile_id, [])
        if not discovery_entries:
            continue

        structure = profile.get("export_structure", {})
        current_hash = str(structure.get("observed_header_hash", "")).strip()
        observed_hashes = {
            str(value).strip()
            for value in structure.get("observed_header_hashes", []) or []
            if str(value).strip()
        }
        approved_hashes = {
            str(value).strip()
            for value in structure.get("approved_header_hashes", []) or []
            if str(value).strip()
        }
        known_hashes = observed_hashes | approved_hashes | ({current_hash} if current_hash else set())
        packet_hashes = {
            str(entry.get("observed_header_hash", "")).strip()
            for entry in discovery_entries
        }
        if "" in packet_hashes:
            raise _impl.ProfileValidationError(
                f"Discovery registry header-hash mismatch for {profile_id}: packet hash is blank"
            )
        unknown_hashes = sorted(packet_hashes - known_hashes)
        if unknown_hashes:
            raise _impl.ProfileValidationError(
                f"Discovery registry header-hash mismatch for {profile_id}: "
                f"{unknown_hashes} are not registered as observed or approved"
            )

        if current_hash not in packet_hashes:
            historical_candidates = [
                entry
                for entry in discovery_entries
                if str(entry.get("observed_header_hash", "")).strip() in approved_hashes
            ]
            if len(historical_candidates) != 1:
                raise _impl.ProfileValidationError(
                    f"Discovery registry primary-layout mismatch for {profile_id}: "
                    f"current hash {current_hash} is absent and exactly one approved historical packet was expected"
                )

    return live_profiles


def _compatible_primary_discovery_entry(profile, entries):
    """Select the current packet, or one approved historical packet if absent."""

    structure = profile.get("export_structure", {})
    current_hash = str(structure.get("observed_header_hash", "")).strip()
    current_matches = [
        entry
        for entry in entries
        if str(entry.get("observed_header_hash", "")).strip() == current_hash
    ]
    if len(current_matches) == 1:
        return current_matches[0]
    if len(current_matches) > 1:
        raise _impl.ProfileValidationError(
            f"Discovery registry primary-layout mismatch for {profile.get('profile_id')}: "
            f"expected exactly one entry for {current_hash}, found {len(current_matches)}"
        )

    approved_hashes = {
        str(value).strip()
        for value in structure.get("approved_header_hashes", []) or []
        if str(value).strip()
    }
    historical_candidates = [
        entry
        for entry in entries
        if str(entry.get("observed_header_hash", "")).strip() in approved_hashes
    ]
    if len(historical_candidates) == 1:
        return historical_candidates[0]

    raise _impl.ProfileValidationError(
        f"Discovery registry primary-layout mismatch for {profile.get('profile_id')}: "
        f"current hash {current_hash} is absent and found {len(historical_candidates)} approved historical packets"
    )


def _aligned_packet_registries(
    profiles,
    discovery_registry,
    unresolved_registry,
    bridge_registry,
):
    """Validate packet evidence, then align copies for the legacy strict checker.

    Unresolved and bridge artifacts are packet-centric and therefore retain the
    selected discovery packet hash. The legacy checker predates multiple
    approved layouts and expects every profile-indexed artifact to carry the
    live Profile hash. Validate the real packet relationship first, then rewrite
    only in-memory copies so the remaining legacy checks can run unchanged.
    """

    aligned_unresolved = copy.deepcopy(unresolved_registry)
    aligned_bridge = copy.deepcopy(bridge_registry)
    unresolved_by_profile = _impl._index_by_profile(aligned_unresolved)
    bridge_by_profile = _impl._index_by_profile(aligned_bridge)
    discovery_by_profile = _impl._group_by_profile(discovery_registry)

    for profile in profiles:
        profile_id = str(profile.get("profile_id", ""))
        discovery_entries = discovery_by_profile.get(profile_id, [])
        unresolved_entry = unresolved_by_profile.get(profile_id)
        bridge_entry = bridge_by_profile.get(profile_id)
        if not discovery_entries or unresolved_entry is None or bridge_entry is None:
            continue

        packet_entry = _compatible_primary_discovery_entry(profile, discovery_entries)
        packet_hash = str(packet_entry.get("observed_header_hash", "")).strip()
        packet_source = str(packet_entry.get("source_file_name", ""))
        unresolved_hash = str(unresolved_entry.get("observed_header_hash", "")).strip()
        bridge_hash = str(bridge_entry.get("observed_header_hash", "")).strip()
        unresolved_source = str(unresolved_entry.get("source_file_name", ""))
        bridge_source = str(bridge_entry.get("source_file_name", ""))

        if unresolved_hash != packet_hash:
            raise _impl.ProfileValidationError(
                f"Unresolved review packet header-hash mismatch for {profile_id}: "
                f"{unresolved_hash} != {packet_hash}"
            )
        if unresolved_source != packet_source:
            raise _impl.ProfileValidationError(
                f"Unresolved review packet source mismatch for {profile_id}: "
                f"{unresolved_source} != {packet_source}"
            )
        if bridge_hash != packet_hash:
            raise _impl.ProfileValidationError(
                f"Bridge review packet header-hash mismatch for {profile_id}: "
                f"{bridge_hash} != {packet_hash}"
            )
        if bridge_source != packet_source:
            raise _impl.ProfileValidationError(
                f"Bridge review packet source mismatch for {profile_id}: "
                f"{bridge_source} != {packet_source}"
            )

        live_hash = str(profile.get("export_structure", {}).get("observed_header_hash", "")).strip()
        unresolved_entry["observed_header_hash"] = live_hash
        bridge_entry["observed_header_hash"] = live_hash

    return aligned_unresolved, aligned_bridge


def validate_discovery_packet_consistency(
    profiles,
    discovery_registry,
    unresolved_registry,
    readiness_registry,
    transition_registry,
    bridge_registry,
    deprecation_registry,
    traceability_registry,
    rollback_registry,
    coverage_registry,
):
    live_profiles = _packet_compatible_profiles(profiles, discovery_registry)
    aligned_unresolved, aligned_bridge = _aligned_packet_registries(
        live_profiles,
        discovery_registry,
        unresolved_registry,
        bridge_registry,
    )
    previous_primary_selector = _impl._primary_discovery_entry
    _impl._primary_discovery_entry = _compatible_primary_discovery_entry
    try:
        return _ORIGINAL_VALIDATE(
            live_profiles,
            discovery_registry,
            aligned_unresolved,
            readiness_registry,
            transition_registry,
            aligned_bridge,
            deprecation_registry,
            traceability_registry,
            rollback_registry,
            coverage_registry,
        )
    finally:
        _impl._primary_discovery_entry = previous_primary_selector


def _with_compatible_validator(callable_, *args, **kwargs):
    previous = _impl.validate_discovery_packet_consistency
    _impl.validate_discovery_packet_consistency = validate_discovery_packet_consistency
    try:
        return callable_(*args, **kwargs)
    finally:
        _impl.validate_discovery_packet_consistency = previous


def validate_live_discovery_packets(*args, **kwargs):
    return _with_compatible_validator(_impl.validate_live_discovery_packets, *args, **kwargs)


def main() -> int:
    return _with_compatible_validator(_impl.main)


if __name__ == "__main__":
    raise SystemExit(main())
