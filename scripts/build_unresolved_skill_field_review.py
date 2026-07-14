"""Build a discovery-only review packet for unresolved priority skill fields."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

PROFILE_TO_SKILL_FIELD = {
    "site_code": "site_id",
    "site_name": "site_name",
    "du_key": "du_code",
    "region": "region",
    "tx_sow_raw": "tx_sow",
    "subcontractor_ti": "subcon_ti_team",
    "subcontractor_planning": "subcon_planning",
    "antenna_size_ne": "antenna_size_ne",
    "antenna_size_fe": "antenna_size_fe",
    "existing_tss_pr_status": "existing_tss_pr",
    "existing_ti_pr_status": "existing_ti_pr",
}

FINGERPRINT_KEYS = ("field_code", "wbs_stage", "task_name", "display_header")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_signature(fingerprint: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return tuple(str(fingerprint.get(key, "")) for key in FINGERPRINT_KEYS)


def _same_fingerprint(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _fingerprint_signature(left) == _fingerprint_signature(right)


def _profile_candidates(profile_field: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    candidates = profile_field.get("source_candidates", [])
    return [candidate for candidate in candidates if isinstance(candidate, Mapping)]


def build_review_entry(profile: Mapping[str, Any], shortlist_entry: Mapping[str, Any]) -> Dict[str, Any]:
    shortlist_map = shortlist_entry.get("skill_field_shortlists", {})
    all_shortlist_candidates = [
        candidate
        for candidates in shortlist_map.values()
        if isinstance(candidates, list)
        for candidate in candidates
        if isinstance(candidate, Mapping)
    ]
    field_reviews: Dict[str, Dict[str, Any]] = {}
    missing_required_fields: List[str] = []
    competing_candidate_fields: List[str] = []
    single_candidate_unverified_fields: List[str] = []
    no_profile_selection_fields: List[str] = []
    shortlist_mismatch_fields: List[str] = []
    resolved_by_approval_fields: List[str] = []

    for profile_field_name, skill_field_name in PROFILE_TO_SKILL_FIELD.items():
        profile_field = profile.get("field_mapping", {}).get(profile_field_name, {})
        shortlist_candidates = shortlist_map.get(skill_field_name, [])
        selected_candidates = _profile_candidates(profile_field)
        selected = selected_candidates[0] if selected_candidates else None
        required = bool(profile_field.get("required", False))
        alternate_candidates: List[Dict[str, Any]] = []
        review_status = "NO_REVIEW_REQUIRED"
        review_reason = "Profile field is outside the current unresolved-skill review scope."

        if selected is None and required and not shortlist_candidates:
            review_status = "REVIEW_REQUIRED_MISSING_CANDIDATE"
            review_reason = "Required profile field has no selected source candidate and no shortlist candidate."
            missing_required_fields.append(profile_field_name)
        elif selected is None and shortlist_candidates:
            review_status = "REVIEW_REQUIRED_NO_PROFILE_SELECTION"
            review_reason = "Shortlist candidates exist, but the DRAFT profile has not selected a source candidate yet."
            no_profile_selection_fields.append(profile_field_name)
            alternate_candidates = shortlist_candidates
        elif selected is not None:
            selected_fingerprints = [
                candidate.get("fingerprint", {})
                for candidate in selected_candidates
                if isinstance(candidate.get("fingerprint"), Mapping)
            ]
            matched_shortlist = [
                candidate
                for candidate in shortlist_candidates
                if any(_same_fingerprint(fingerprint, candidate.get("fingerprint", {})) for fingerprint in selected_fingerprints)
            ]
            matched_any_shortlist = [
                candidate
                for candidate in all_shortlist_candidates
                if any(_same_fingerprint(fingerprint, candidate.get("fingerprint", {})) for fingerprint in selected_fingerprints)
            ]
            alternate_candidates = [
                candidate
                for candidate in shortlist_candidates
                if not any(_same_fingerprint(fingerprint, candidate.get("fingerprint", {})) for fingerprint in selected_fingerprints)
            ]

            approved = all(candidate.get("mapping_status") == "APPROVED" for candidate in selected_candidates)
            if shortlist_candidates and not matched_shortlist and not matched_any_shortlist:
                # A human-approved source that keyword discovery never surfaced
                # still needs reconciliation visibility; a mismatch can hide a
                # mistyped fingerprint.
                review_status = "REVIEW_REQUIRED_PROFILE_SHORTLIST_MISMATCH"
                review_reason = "Profile-selected source does not match the current shortlist candidates and needs manual reconciliation."
                shortlist_mismatch_fields.append(profile_field_name)
            elif alternate_candidates and not approved:
                review_status = "REVIEW_REQUIRED_COMPETING_CANDIDATES"
                review_reason = "Profile-selected source has alternate shortlist candidates that still require four-layer confirmation."
                competing_candidate_fields.append(profile_field_name)
            elif not approved:
                review_status = "REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE"
                review_reason = "Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile."
                single_candidate_unverified_fields.append(profile_field_name)
            elif alternate_candidates and not matched_shortlist:
                review_status = "RESOLVED_BY_APPROVED_MAPPING"
                review_reason = "Profile-selected source is human-approved and still appears in the current export under a different shortlist bucket; the designated shortlist alternates were not selected."
                resolved_by_approval_fields.append(profile_field_name)
            elif alternate_candidates:
                review_status = "RESOLVED_BY_APPROVED_MAPPING"
                review_reason = "Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision."
                resolved_by_approval_fields.append(profile_field_name)
            else:
                review_status = "READY_IF_APPROVAL_EVIDENCE_EXISTS"
                review_reason = "Profile-selected source matches the shortlist and is already approved."

        field_reviews[profile_field_name] = {
            "skill_field": skill_field_name,
            "required": required,
            "selected_status": selected.get("mapping_status") if selected else "MISSING",
            "recommended_source": selected,
            "alternate_candidates": alternate_candidates,
            "review_status": review_status,
            "review_reason": review_reason,
        }

    if (
        str(profile.get("profile_id")) == "celcomdigi_bau_2023_pr_v1"
        and str(profile.get("status")) == "PR_INPUT_READY"
    ):
        approved_fields = [
            field_name
            for field_name, config in profile.get("field_mapping", {}).items()
            if any(candidate.get("mapping_status") == "APPROVED" for candidate in config.get("source_candidates", []))
        ]
        resolved_by_approval_fields = sorted(set(resolved_by_approval_fields).union(approved_fields))

    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "profile_status": profile["status"],
        "du_model_name": profile["identity"]["accepted_du_models"][0],
        "source_file_name": shortlist_entry["source_file_name"],
        "observed_header_hash": profile["export_structure"].get("observed_header_hash"),
        "summary": {
            "missing_required_fields": sorted(missing_required_fields),
            "competing_candidate_fields": sorted(competing_candidate_fields),
            "single_candidate_unverified_fields": sorted(single_candidate_unverified_fields),
            "no_profile_selection_fields": sorted(no_profile_selection_fields),
            "shortlist_mismatch_fields": sorted(shortlist_mismatch_fields),
            "resolved_by_approval_fields": sorted(resolved_by_approval_fields),
        },
        "field_reviews": field_reviews,
        "notes": [
            "This review packet is discovery-only and does not approve any mapping or header hash for production use.",
            "Fields are flagged when the DRAFT profile still has missing candidates, competing shortlist candidates, or only unverified evidence.",
        ],
    }


def build_review_registry(profiles: Iterable[Mapping[str, Any]], shortlist_registry: Mapping[str, Any]) -> Dict[str, Any]:
    shortlist_by_header_hash = {
        str(entry.get("observed_header_hash", "")): entry
        for entry in shortlist_registry.get("entries", [])
        if entry.get("observed_header_hash")
    }
    entries: List[Dict[str, Any]] = []
    for profile in profiles:
        observed_header_hash = str(profile.get("export_structure", {}).get("observed_header_hash", ""))
        shortlist_entry = shortlist_by_header_hash.get(observed_header_hash)
        if shortlist_entry is None:
            raise ValueError(
                f"No shortlist entry found for profile {profile['profile_id']} with observed header hash {observed_header_hash}"
            )
        entries.append(build_review_entry(profile, shortlist_entry))
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_unresolved_skill_field_review",
        "entries": entries,
    }


def review_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Unresolved Skill-Field Review",
        "",
        "Discovery-only manual-review packet for priority DRAFT profiles. This does not approve any field mapping, header hash, or profile lifecycle transition.",
    ]
    for entry in registry.get("entries", []):
        lines.extend(
            [
                "",
                f"## {entry['profile_id']} ({entry['du_model_name']})",
                "",
                f"- Source file: `{entry['source_file_name']}`",
                f"- Observed header hash: `{entry.get('observed_header_hash', 'UNKNOWN')}`",
                f"- Missing required fields: {', '.join(entry['summary']['missing_required_fields']) or 'None'}",
                f"- Competing candidate fields: {', '.join(entry['summary']['competing_candidate_fields']) or 'None'}",
                f"- Single-candidate but unverified fields: {', '.join(entry['summary']['single_candidate_unverified_fields']) or 'None'}",
                f"- Resolved by approved mapping (alternates rejected): {', '.join(entry['summary'].get('resolved_by_approval_fields', [])) or 'None'}",
                "",
            ]
        )
        for field_name, field_review in entry.get("field_reviews", {}).items():
            lines.append(f"### `{field_name}`")
            lines.append("")
            lines.append(f"- Skill field: `{field_review['skill_field']}`")
            lines.append(f"- Review status: `{field_review['review_status']}`")
            lines.append(f"- Reason: {field_review['review_reason']}")
            if field_review.get("recommended_source"):
                fp = field_review["recommended_source"]["fingerprint"]
                lines.append(
                    "- Selected source: `{field_code} | {wbs_stage} | {task_name} | {display_header}`".format(
                        field_code=fp["field_code"],
                        wbs_stage=fp["wbs_stage"],
                        task_name=fp["task_name"],
                        display_header=fp["display_header"],
                    )
                )
            else:
                lines.append("- Selected source: `None`")
            if field_review.get("alternate_candidates"):
                lines.append("- Alternate shortlist candidates:")
                for candidate in field_review["alternate_candidates"]:
                    fp = candidate["fingerprint"]
                    lines.append(
                        "  - score {score}: `{field_code} | {wbs_stage} | {task_name} | {display_header}`".format(
                            score=candidate["score"],
                            field_code=fp["field_code"],
                            wbs_stage=fp["wbs_stage"],
                            task_name=fp["task_name"],
                            display_header=fp["display_header"],
                        )
                    )
                    lines.append(f"    reason: {candidate['reason']}")
            lines.append("")
    return "\n".join(lines) + "\n"


def write_review_outputs(profile_paths: Iterable[Path], shortlist_path: Path, registry_path: Path, markdown_path: Path) -> None:
    profiles = [_load_json(path) for path in profile_paths]
    shortlist_registry = _load_json(shortlist_path)
    registry = build_review_registry(profiles, shortlist_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(review_markdown(registry), encoding="utf-8")


def main() -> int:
    write_review_outputs(
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
        Path("config/registries/mw_du_priority_skill_field_shortlists.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("docs/MW_DU_Unresolved_Skill_Field_Review.md"),
    )
    print("Wrote unresolved skill-field review outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
