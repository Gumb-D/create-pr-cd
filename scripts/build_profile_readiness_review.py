"""Build a discovery-only readiness review for priority DU profiles.

This packet summarizes why each current DRAFT profile remains blocked from any
production lifecycle transition. It is review guidance only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile_unverified_required_fields(profile: Mapping[str, Any]) -> list[str]:
    fields = []
    for canonical_field, config in profile.get("field_mapping", {}).items():
        if not config.get("required"):
            continue
        candidates = config.get("source_candidates", [])
        if not candidates:
            continue
        if any(candidate.get("mapping_status") != "APPROVED" for candidate in candidates):
            fields.append(str(canonical_field))
    return sorted(fields)


def _required_subset(profile: Mapping[str, Any], field_names: list[str]) -> list[str]:
    required_fields = {
        str(canonical_field)
        for canonical_field, config in profile.get("field_mapping", {}).items()
        if config.get("required")
    }
    return sorted(field_name for field_name in field_names if field_name in required_fields)


def build_readiness_entry(
    profile: Mapping[str, Any],
    unresolved_entry: Mapping[str, Any],
    bridge_entry: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    export_structure = profile.get("export_structure", {})
    summary = unresolved_entry.get("summary", {})
    missing_required_fields = list(summary.get("missing_required_fields", []))
    competing_candidate_fields = list(summary.get("competing_candidate_fields", []))
    single_candidate_unverified_fields = list(summary.get("single_candidate_unverified_fields", []))
    no_profile_selection_fields = list(summary.get("no_profile_selection_fields", []))
    shortlist_mismatch_fields = list(summary.get("shortlist_mismatch_fields", []))
    approved_header_hashes = list(export_structure.get("approved_header_hashes", []))
    bridge_fields = sorted((bridge_entry or {}).get("field_bridges", {}).keys())

    lifecycle_blockers = []
    if profile.get("status") != "PRODUCTION":
        lifecycle_blockers.append("PROFILE_NOT_PRODUCTION")
    if not approved_header_hashes:
        lifecycle_blockers.append("NO_APPROVED_HEADER_HASH")

    review_blockers = []
    if competing_candidate_fields:
        review_blockers.append("COMPETING_SHORTLIST_CANDIDATES")
    if single_candidate_unverified_fields:
        review_blockers.append("UNVERIFIED_SINGLE_CANDIDATE_FIELDS")
    if no_profile_selection_fields:
        review_blockers.append("NO_PROFILE_SELECTION_FIELDS")
    if shortlist_mismatch_fields:
        review_blockers.append("SHORTLIST_MISMATCH_FIELDS")
    if bridge_fields:
        review_blockers.append("CROSS_MODEL_BRIDGE_ONLY_FIELDS")

    overall_blockers = lifecycle_blockers + review_blockers
    if missing_required_fields:
        overall_blockers.insert(len(lifecycle_blockers), "MISSING_REQUIRED_FIELDS")
    if _profile_unverified_required_fields(profile):
        overall_blockers.insert(len(lifecycle_blockers), "REQUIRED_FIELDS_NOT_APPROVED")

    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "profile_status": profile["status"],
        "du_model_name": unresolved_entry.get("du_model_name", ""),
        "source_file_name": unresolved_entry.get("source_file_name", ""),
        "observed_header_hash": export_structure.get("observed_header_hash", ""),
        "approved_header_hashes": approved_header_hashes,
        "readiness_status": "PRODUCTION_READY" if not overall_blockers else "DISCOVERY_ONLY_BLOCKED",
        "blocker_summary": {
            "overall_blockers": overall_blockers,
            "lifecycle_blockers": lifecycle_blockers,
            "missing_required_fields": missing_required_fields,
            "unapproved_required_fields": _profile_unverified_required_fields(profile),
            "competing_candidate_fields": competing_candidate_fields,
            "required_competing_candidate_fields": _required_subset(profile, competing_candidate_fields),
            "single_candidate_unverified_fields": single_candidate_unverified_fields,
            "required_single_candidate_unverified_fields": _required_subset(profile, single_candidate_unverified_fields),
            "no_profile_selection_fields": no_profile_selection_fields,
            "required_no_profile_selection_fields": _required_subset(profile, no_profile_selection_fields),
            "shortlist_mismatch_fields": shortlist_mismatch_fields,
            "required_shortlist_mismatch_fields": _required_subset(profile, shortlist_mismatch_fields),
            "cross_model_bridge_fields": bridge_fields,
        },
        "release_prerequisites": [
            "Approve the DU model identity and four-layer source mappings.",
            "Approve at least one header hash for the profile version.",
            "Resolve missing required fields or keep the profile blocked.",
            "Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.",
            "Complete regression verification and UAT before any lifecycle promotion.",
        ],
        "notes": [
            "This readiness review is discovery-only and does not approve any mapping, header hash, lifecycle transition, or cross-model reuse.",
            "A profile can remain structurally informative while still being blocked from any production path.",
        ],
    }


def build_readiness_registry(
    profiles: Iterable[Mapping[str, Any]],
    unresolved_registry: Mapping[str, Any],
    bridge_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    unresolved_by_profile = {
        str(entry["profile_id"]): entry for entry in unresolved_registry.get("entries", [])
    }
    bridge_by_profile = {
        str(entry["profile_id"]): entry for entry in bridge_registry.get("entries", [])
    }
    entries = []
    for profile in profiles:
        profile_id = str(profile["profile_id"])
        unresolved_entry = unresolved_by_profile.get(profile_id)
        if unresolved_entry is None:
            raise ValueError(f"No unresolved review entry found for profile {profile_id}")
        entries.append(build_readiness_entry(profile, unresolved_entry, bridge_by_profile.get(profile_id)))
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_readiness_review",
        "entries": entries,
        "notes": [
            "Discovery-only readiness summary for priority DU profiles.",
            "Readiness here means approval-preparation visibility, not production eligibility.",
        ],
    }


def readiness_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Readiness Review",
        "",
        "Discovery-only summary of why the current priority DU profiles remain blocked from release.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']} ({entry['du_model_name']})")
        lines.append("")
        lines.append(f"- Readiness status: `{entry['readiness_status']}`")
        lines.append(f"- Profile status: `{entry['profile_status']}`")
        lines.append(f"- Profile version: `{entry['profile_version']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry['observed_header_hash']}`")
        lines.append(f"- Approved header hashes: `{len(entry.get('approved_header_hashes', []))}`")
        blocker_summary = entry.get("blocker_summary", {})
        lines.append(f"- Overall blockers: `{', '.join(blocker_summary.get('overall_blockers', []))}`")
        if blocker_summary.get("missing_required_fields"):
            lines.append(
                f"- Missing required fields: `{', '.join(blocker_summary['missing_required_fields'])}`"
            )
        if blocker_summary.get("competing_candidate_fields"):
            lines.append(
                f"- Competing candidate fields: `{', '.join(blocker_summary['competing_candidate_fields'])}`"
            )
        if blocker_summary.get("cross_model_bridge_fields"):
            lines.append(
                f"- Cross-model bridge-only fields: `{', '.join(blocker_summary['cross_model_bridge_fields'])}`"
            )
        lines.append("- Release prerequisites:")
        for item in entry.get("release_prerequisites", []):
            lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_readiness_outputs(
    profile_paths: Iterable[Path],
    unresolved_path: Path,
    bridge_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    unresolved_registry = _load_json(unresolved_path)
    bridge_registry = _load_json(bridge_path)
    registry = build_readiness_registry(profiles, unresolved_registry, bridge_registry)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    markdown_path.write_text(readiness_markdown(registry), encoding="utf-8")


if __name__ == "__main__":
    write_readiness_outputs(
        discover_du_profile_paths(),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("docs/MW_DU_Profile_Readiness_Review.md"),
    )
    print("Wrote profile readiness review outputs.")
