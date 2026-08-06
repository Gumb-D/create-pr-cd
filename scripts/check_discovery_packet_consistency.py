"""Compatibility-aware consistency checks for historical approved DU packets."""
from __future__ import annotations

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
    previous_primary_selector = _impl._primary_discovery_entry
    _impl._primary_discovery_entry = _compatible_primary_discovery_entry
    try:
        return _ORIGINAL_VALIDATE(
            live_profiles,
            discovery_registry,
            unresolved_registry,
            readiness_registry,
            transition_registry,
            bridge_registry,
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
