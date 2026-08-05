"""Compatibility-aware consistency checks for historical approved DU packets."""
from __future__ import annotations

import copy

import check_discovery_packet_consistency_impl as _impl
from check_discovery_packet_consistency_impl import *  # noqa: F401,F403


_ORIGINAL_VALIDATE = _impl.validate_discovery_packet_consistency


def _packet_compatible_profiles(profiles, discovery_registry):
    """Validate historical packet layouts, then align profile copies for strict checks.

    Discovery artifacts may contain multiple source layouts for one Project + DU
    Model profile family. Every packet hash must be explicitly recorded as an
    observed layout or approved historical layout. Profile-centric governance
    remains aligned to the configured primary observed layout.
    """

    entries_by_profile = _impl._group_by_profile(discovery_registry)
    compatible = []
    for raw_profile in profiles:
        profile = copy.deepcopy(raw_profile)
        profile_id = str(profile.get("profile_id", ""))
        discovery_entries = entries_by_profile.get(profile_id, [])
        if not discovery_entries:
            compatible.append(profile)
            continue

        structure = profile.setdefault("export_structure", {})
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
                    f"current hash {current_hash} is absent"
                )
            historical = historical_candidates[0]
            structure["observed_header_hash"] = str(historical["observed_header_hash"])
            historical_version = str(historical.get("profile_version", "")).strip()
            if not historical_version:
                raise _impl.ProfileValidationError(
                    f"Discovery registry profile-version mismatch for {profile_id}: historical version is blank"
                )
            profile["profile_version"] = historical_version
        compatible.append(profile)
    return compatible


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
    compatible_profiles = _packet_compatible_profiles(profiles, discovery_registry)
    return _ORIGINAL_VALIDATE(
        compatible_profiles,
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
