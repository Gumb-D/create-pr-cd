"""Build a conservative lifecycle-transition review for DU profiles.

The review is intentionally fail-closed: if evidence is incomplete, the profile
is not considered eligible for promotion.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import PROFILE_STATUSES, load_du_profile

TRANSITION_TARGETS = ("PROFILED", "BUSINESS_VALIDATED", "PR_INPUT_READY", "PRODUCTION")


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_transition(readiness_entry: Mapping[str, Any], target_status: str) -> Dict[str, Any]:
    if target_status not in PROFILE_STATUSES:
        raise ValueError(f"Unknown target status: {target_status}")
    blockers = readiness_entry.get("blocker_summary", {})
    lifecycle_blockers = list(blockers.get("lifecycle_blockers", []))
    non_production_lifecycle_blockers = [reason for reason in lifecycle_blockers if reason != "PROFILE_NOT_PRODUCTION"]
    missing_required_fields = list(blockers.get("missing_required_fields", []))
    unapproved_required_fields = list(blockers.get("unapproved_required_fields", []))
    competing_candidate_fields = list(
        blockers.get("required_competing_candidate_fields", blockers.get("competing_candidate_fields", []))
    )
    single_candidate_unverified_fields = list(
        blockers.get(
            "required_single_candidate_unverified_fields",
            blockers.get("single_candidate_unverified_fields", []),
        )
    )
    no_profile_selection_fields = list(
        blockers.get("required_no_profile_selection_fields", blockers.get("no_profile_selection_fields", []))
    )
    shortlist_mismatch_fields = list(
        blockers.get("required_shortlist_mismatch_fields", blockers.get("shortlist_mismatch_fields", []))
    )
    cross_model_bridge_fields = list(blockers.get("cross_model_bridge_fields", []))

    denied_reasons: list[str] = []
    if target_status == "PROFILED":
        if missing_required_fields:
            denied_reasons.append("MISSING_REQUIRED_FIELDS")
        if no_profile_selection_fields:
            denied_reasons.append("NO_PROFILE_SELECTION_FIELDS")
        if shortlist_mismatch_fields:
            denied_reasons.append("SHORTLIST_MISMATCH_FIELDS")
    elif target_status == "BUSINESS_VALIDATED":
        denied_reasons.extend(non_production_lifecycle_blockers)
        if missing_required_fields:
            denied_reasons.append("MISSING_REQUIRED_FIELDS")
        if unapproved_required_fields:
            denied_reasons.append("REQUIRED_FIELDS_NOT_APPROVED")
        if competing_candidate_fields:
            denied_reasons.append("COMPETING_SHORTLIST_CANDIDATES")
        if no_profile_selection_fields:
            denied_reasons.append("NO_PROFILE_SELECTION_FIELDS")
        if shortlist_mismatch_fields:
            denied_reasons.append("SHORTLIST_MISMATCH_FIELDS")
    elif target_status == "PR_INPUT_READY":
        denied_reasons.extend(non_production_lifecycle_blockers)
        if missing_required_fields:
            denied_reasons.append("MISSING_REQUIRED_FIELDS")
        if unapproved_required_fields:
            denied_reasons.append("REQUIRED_FIELDS_NOT_APPROVED")
        if competing_candidate_fields:
            denied_reasons.append("COMPETING_SHORTLIST_CANDIDATES")
        if single_candidate_unverified_fields:
            denied_reasons.append("UNVERIFIED_SINGLE_CANDIDATE_FIELDS")
        if no_profile_selection_fields:
            denied_reasons.append("NO_PROFILE_SELECTION_FIELDS")
        if shortlist_mismatch_fields:
            denied_reasons.append("SHORTLIST_MISMATCH_FIELDS")
        if cross_model_bridge_fields:
            denied_reasons.append("CROSS_MODEL_BRIDGE_ONLY_FIELDS")
    else:
        denied_reasons.extend(lifecycle_blockers)
        if missing_required_fields:
            denied_reasons.append("MISSING_REQUIRED_FIELDS")
        if unapproved_required_fields:
            denied_reasons.append("REQUIRED_FIELDS_NOT_APPROVED")
        if competing_candidate_fields:
            denied_reasons.append("COMPETING_SHORTLIST_CANDIDATES")
        if single_candidate_unverified_fields:
            denied_reasons.append("UNVERIFIED_SINGLE_CANDIDATE_FIELDS")
        if no_profile_selection_fields:
            denied_reasons.append("NO_PROFILE_SELECTION_FIELDS")
        if shortlist_mismatch_fields:
            denied_reasons.append("SHORTLIST_MISMATCH_FIELDS")
        if cross_model_bridge_fields:
            denied_reasons.append("CROSS_MODEL_BRIDGE_ONLY_FIELDS")
    return {
        "target_status": target_status,
        "eligible": not denied_reasons,
        "denied_reasons": denied_reasons,
    }


def build_transition_entry(profile: Mapping[str, Any], readiness_entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "current_status": profile["status"],
        "du_model_name": readiness_entry.get("du_model_name", ""),
        "observed_header_hash": readiness_entry.get("observed_header_hash", ""),
        "transition_targets": [evaluate_transition(readiness_entry, target) for target in TRANSITION_TARGETS],
        "notes": [
            "This transition review is conservative and fail-closed.",
            "Eligibility here means the repository evidence does not show a blocker for the target state; it is not a substitute for business approval or UAT.",
        ],
    }


def build_transition_registry(
    profiles: Iterable[Mapping[str, Any]],
    readiness_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    readiness_by_profile = {
        str(entry["profile_id"]): entry for entry in readiness_registry.get("entries", [])
    }
    entries = []
    for profile in profiles:
        readiness_entry = readiness_by_profile.get(str(profile["profile_id"]))
        if readiness_entry is None:
            raise ValueError(f"No readiness entry found for profile {profile['profile_id']}")
        entries.append(build_transition_entry(profile, readiness_entry))
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_transition_review",
        "entries": entries,
        "notes": [
            "Discovery-only lifecycle promotion review for priority DU profiles.",
            "Unproven or incomplete evidence results in a denied transition.",
        ],
    }


def transition_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Transition Review",
        "",
        "Discovery-only lifecycle promotion review for the current priority DU profiles.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']} ({entry['du_model_name']})")
        lines.append("")
        lines.append(f"- Current status: `{entry['current_status']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry['observed_header_hash']}`")
        for target in entry.get("transition_targets", []):
            if target["eligible"]:
                lines.append(f"- `{target['target_status']}`: `ELIGIBLE`")
            else:
                lines.append(
                    f"- `{target['target_status']}`: `DENIED` "
                    f"because `{', '.join(target['denied_reasons'])}`"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_transition_outputs(
    profile_paths: Iterable[Path],
    readiness_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    readiness_registry = _load_json(readiness_path)
    registry = build_transition_registry(profiles, readiness_registry)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    markdown_path.write_text(transition_markdown(registry), encoding="utf-8")


if __name__ == "__main__":
    write_transition_outputs(
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
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("docs/MW_DU_Profile_Transition_Review.md"),
    )
    print("Wrote profile transition review outputs.")
