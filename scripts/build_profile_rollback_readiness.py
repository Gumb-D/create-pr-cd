"""Build a fail-closed rollback-readiness review for DU profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import load_du_profile


RELEASED_STATUSES = {"PR_INPUT_READY", "PRODUCTION", "DEPRECATED"}


def evaluate_rollback_readiness(
    profile: Mapping[str, Any],
    deprecation_entry: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    approved_header_hashes = list(profile.get("export_structure", {}).get("approved_header_hashes", []))
    blockers: list[str] = []

    if not approved_header_hashes:
        blockers.append("NO_APPROVED_HEADER_HASH_BASELINE")
    if str(profile.get("status", "")) not in RELEASED_STATUSES:
        blockers.append("PROFILE_NOT_RELEASED")

    rollback_target_profile_id = None
    rollback_target_profile_version = None
    rollback_target_header_hashes: list[str] = []
    review_notes: list[str] = []

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
        if approved_header_hashes:
            rollback_target_profile_id = profile.get("profile_id")
            rollback_target_profile_version = profile.get("profile_version")
            rollback_target_header_hashes = approved_header_hashes

    status = "ROLLBACK_BASELINE_RECORDED" if not blockers else "ROLLBACK_BLOCKED"
    if status == "ROLLBACK_BLOCKED":
        review_notes.append("Rollback remains blocked until an approved profile/header-hash baseline exists.")
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


def build_rollback_registry(
    profiles: Iterable[Mapping[str, Any]],
    deprecation_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    deprecation_by_profile = {
        str(entry["profile_id"]): entry
        for entry in deprecation_registry.get("entries", [])
        if isinstance(entry, Mapping) and entry.get("profile_id") is not None
    }
    entries = [
        evaluate_rollback_readiness(profile, deprecation_by_profile.get(str(profile["profile_id"])))
        for profile in profiles
    ]
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_rollback_readiness",
        "entries": entries,
        "notes": [
            "This rollback review is fail-closed and documents whether a profile has an approved rollback baseline.",
            "A blocked result does not imply a defect; it can simply mean the profile has not reached an approved release state yet.",
        ],
    }


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
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    deprecation_registry = json.loads(deprecation_registry_path.read_text(encoding="utf-8"))
    registry = build_rollback_registry(profiles, deprecation_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(rollback_markdown(registry), encoding="utf-8")


def main() -> int:
    write_rollback_outputs(
        [
            Path("config/du_profiles/tx_mini_pr_v1.yaml"),
            Path("config/du_profiles/mw_eos_swap_pr_v1.yaml"),
            Path("config/du_profiles/tx_rollout_2023_pr_v1.yaml"),
            Path("config/du_profiles/jendela_tx_migration_pr_v1.yaml"),
            Path("config/du_profiles/zte_tx_mini_pr_v1.yaml"),
            Path("config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml"),
            Path("config/du_profiles/celcomdigi_bau_2024_pr_v1.yaml"),
            Path("config/du_profiles/celcomdigi_usp_pr_v1.yaml"),
            Path("config/du_profiles/cd_consolidation_2023_decom_pr_v1.yaml"),
            Path("config/du_profiles/cd_consolidation_2023_rollout_pr_v1.yaml"),
        ],
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
        Path("config/registries/mw_du_profile_rollback_readiness.yaml"),
        Path("docs/MW_DU_Profile_Rollback_Readiness.md"),
    )
    print("Wrote profile rollback readiness outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
