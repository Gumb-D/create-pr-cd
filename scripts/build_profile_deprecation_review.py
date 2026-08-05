"""Build a controlled deprecation review for DU profiles and header hashes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _production_transition(transition_entry: Mapping[str, Any]) -> Mapping[str, Any]:
    for item in transition_entry.get("transition_targets", []):
        if isinstance(item, Mapping) and item.get("target_status") == "PRODUCTION":
            return item
    raise ValueError(f"No PRODUCTION transition target found for profile {transition_entry.get('profile_id')}")


def evaluate_deprecation(
    profile: Mapping[str, Any],
    production_transition: Mapping[str, Any],
) -> Dict[str, Any]:
    deprecation = profile.get("deprecation")
    if not isinstance(deprecation, Mapping):
        return {
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "mapping_version": profile["mapping_version"],
            "current_status": profile["status"],
            "observed_header_hash": profile.get("export_structure", {}).get("observed_header_hash", ""),
            "deprecation_status": "NO_DEPRECATION_PLAN",
            "superseded_header_hashes": [],
            "successor_profile_id": None,
            "successor_profile_version": None,
            "rollback_profile_id": None,
            "rollback_profile_version": None,
            "blockers": [],
            "notes": [
                "No deprecation plan is recorded for this profile.",
                "A controlled deprecation requires a DEPRECATED lifecycle state plus successor and rollback evidence.",
            ],
        }

    blockers: list[str] = []
    if profile.get("status") != "DEPRECATED":
        blockers.append("STATUS_NOT_DEPRECATED")
    if not production_transition.get("eligible", False):
        blockers.append("NOT_PREVIOUSLY_PRODUCTION_ELIGIBLE")

    approved_hashes = set(profile.get("export_structure", {}).get("approved_header_hashes", []))
    superseded_hashes = list(deprecation.get("superseded_header_hashes", []))
    if not superseded_hashes:
        blockers.append("NO_SUPERSEDED_HEADER_HASHES")
    elif any(hash_value not in approved_hashes for hash_value in superseded_hashes):
        blockers.append("SUPERSEDED_HASH_NOT_IN_APPROVED_SET")

    status = "DEPRECATION_RECORDED" if not blockers else "DEPRECATION_DENIED"
    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "current_status": profile["status"],
        "observed_header_hash": profile.get("export_structure", {}).get("observed_header_hash", ""),
        "deprecation_status": status,
        "superseded_header_hashes": superseded_hashes,
        "successor_profile_id": deprecation.get("successor_profile_id"),
        "successor_profile_version": deprecation.get("successor_profile_version"),
        "rollback_profile_id": deprecation.get("rollback_profile_id"),
        "rollback_profile_version": deprecation.get("rollback_profile_version"),
        "blockers": blockers,
        "notes": [
            "Deprecation remains fail-closed until the profile was previously production-eligible and the superseded header hashes are recorded.",
            "A deprecation record preserves successor and rollback references; it does not approve any new production mapping.",
        ],
    }


def build_deprecation_registry(
    profiles: Iterable[Mapping[str, Any]],
    transition_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    transition_by_profile = {
        str(entry["profile_id"]): entry for entry in transition_registry.get("entries", [])
    }
    entries = []
    for profile in profiles:
        transition_entry = transition_by_profile.get(str(profile["profile_id"]))
        if transition_entry is None:
            raise ValueError(f"No transition review entry found for profile {profile['profile_id']}")
        entries.append(evaluate_deprecation(profile, _production_transition(transition_entry)))
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_deprecation_review",
        "entries": entries,
        "notes": [
            "Discovery-only deprecation review for tracked DU profiles.",
            "Profiles without a recorded deprecation plan remain outside the deprecation path.",
        ],
    }


def deprecation_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Deprecation Review",
        "",
        "Discovery-only deprecation review for the tracked DU profiles.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']}")
        lines.append("")
        lines.append(f"- Current status: `{entry['current_status']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry['observed_header_hash']}`")
        lines.append(f"- Deprecation status: `{entry['deprecation_status']}`")
        if entry.get("successor_profile_id"):
            lines.append(
                f"- Successor: `{entry['successor_profile_id']}` `{entry['successor_profile_version']}`"
            )
        if entry.get("rollback_profile_id"):
            lines.append(
                f"- Rollback target: `{entry['rollback_profile_id']}` `{entry['rollback_profile_version']}`"
            )
        if entry.get("superseded_header_hashes"):
            lines.append(
                f"- Superseded header hashes: `{', '.join(entry.get('superseded_header_hashes', []))}`"
            )
        if entry.get("blockers"):
            lines.append(f"- Blockers: `{', '.join(entry['blockers'])}`")
        for note in entry.get("notes", []):
            lines.append(f"- Note: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_deprecation_outputs(
    profile_paths: Iterable[Path],
    transition_registry_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    transition_registry = _load_json(transition_registry_path)
    registry = build_deprecation_registry(profiles, transition_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(deprecation_markdown(registry), encoding="utf-8")


def main() -> int:
    write_deprecation_outputs(
        discover_du_profile_paths(),
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
        Path("docs/MW_DU_Profile_Deprecation_Review.md"),
    )
    print("Wrote profile deprecation review outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
