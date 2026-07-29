"""Compatibility-aware consistency checks for historical approved DU packets."""
from __future__ import annotations

import copy

import check_discovery_packet_consistency_impl as _impl
from check_discovery_packet_consistency_impl import *  # noqa: F401,F403


_ORIGINAL_VALIDATE = _impl.validate_discovery_packet_consistency


def _packet_compatible_profiles(profiles, discovery_registry):
    """Validate historical packet identity, then align copies for strict checks.

    Discovery artifacts describe the exact export from which they were built. A
    profile may later approve another compatible header hash without rewriting
    that historical packet. The packet remains valid only when its hash is still
    explicitly approved by the current profile.
    """

    discovery_by_profile = _impl._index_by_profile(discovery_registry)
    compatible = []
    for raw_profile in profiles:
        profile = copy.deepcopy(raw_profile)
        profile_id = str(profile.get("profile_id", ""))
        discovery_entry = discovery_by_profile.get(profile_id)
        if discovery_entry is None:
            compatible.append(profile)
            continue

        current_hash = str(profile.get("export_structure", {}).get("observed_header_hash", ""))
        approved_hashes = {
            str(value)
            for value in profile.get("export_structure", {}).get("approved_header_hashes", [])
            if str(value)
        }
        packet_hash = str(discovery_entry.get("observed_header_hash", ""))
        if not packet_hash or packet_hash not in approved_hashes:
            raise _impl.ProfileValidationError(
                f"Discovery registry header-hash mismatch for {profile_id}: "
                f"{packet_hash or '(blank)'} is not in approved_header_hashes"
            )

        if packet_hash != current_hash:
            profile.setdefault("export_structure", {})["observed_header_hash"] = packet_hash
            historical_version = str(discovery_entry.get("profile_version", "")).strip()
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
