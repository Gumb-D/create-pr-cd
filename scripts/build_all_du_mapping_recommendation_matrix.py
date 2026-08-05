"""Build the all-DU discovery-only mapping recommendation matrix for PR #19."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from du_profile_loader import discover_du_profile_paths
from typing import Any, Dict, Iterable, List, Mapping, Sequence


TRACKED_CANONICAL_FIELDS: Sequence[str] = (
    "site_code",
    "tx_sow_raw",
    "region",
    "subcontractor_ti",
    "existing_tss_pr_status",
    "existing_ti_pr_status",
    "site_name",
    "du_key",
    "state",
    "latitude",
    "longitude",
    "antenna_size_ne",
    "antenna_size_fe",
    "tx_upgrade_scope_raw",
    "tx_sow_details",
    "boq_configuration",
    "ne_sow_details",
    "fe_sow_details",
)

REQUIRED_FIELDS = {
    "site_code",
    "tx_sow_raw",
    "region",
    "subcontractor_ti",
    "existing_tss_pr_status",
    "existing_ti_pr_status",
}

CONDITIONAL_FIELDS = {
    "state",
    "latitude",
    "longitude",
    "antenna_size_ne",
    "antenna_size_fe",
    "tx_upgrade_scope_raw",
    "tx_sow_details",
    "boq_configuration",
    "ne_sow_details",
    "fe_sow_details",
}

GROUP_METADATA = {
    "same_or_highly_similar_to_tx_mini": "Same or highly similar to TX Mini",
    "similar_to_mw_eos_swap": "Similar to MW EOS Swap",
    "different_structure_pr_critical_present": "Structurally different but PR-critical fields appear present",
    "missing_pr_critical_fields_quarantine_candidate": "Missing PR-critical fields / quarantine candidate",
    "unreadable_or_unsupported_source_format": "Unreadable or unsupported source format",
    "duplicate_or_competing_export_variants": "Duplicate or competing export variants",
}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_tuple(fingerprint: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return tuple(
        str(fingerprint.get(key, ""))
        for key in ("field_code", "wbs_stage", "task_name", "display_header")
    )


def _requirement_class(field_name: str) -> str:
    if field_name in REQUIRED_FIELDS:
        return "required"
    if field_name in CONDITIONAL_FIELDS:
        return "conditional"
    return "optional"


def _candidate_is_plausible(candidate: Mapping[str, Any]) -> bool:
    fingerprint = candidate.get("fingerprint", {})
    sheet_name = str(candidate.get("sheet_name", "")).strip().lower()
    display = str(fingerprint.get("display_header", "")).strip()
    return sheet_name == "data" and bool(display)


def _find_profiler_root() -> Path:
    candidates = (
        Path("output/du-20260706-profile"),
        Path("Info/reference/du-20260706-profile"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No DU profiler artifact root found under output/ or Info/reference/.")


def _inventory_paths_by_name(inventory_registry: Mapping[str, Any]) -> Dict[str, str]:
    by_name: Dict[str, str] = {}
    preferred: Dict[str, str] = {}
    for item in inventory_registry.get("inventory", []):
        name = str(item.get("original_file_name", ""))
        relative = str(item.get("relative_path", ""))
        if not name:
            continue
        by_name.setdefault(name, relative)
        if relative.lower().startswith("du_exports\\"):
            preferred[name] = relative
    by_name.update(preferred)
    return by_name


def _load_profiler_artifacts(profiler_root: Path) -> Dict[str, Dict[str, Any]]:
    artifacts: Dict[str, Dict[str, Any]] = {}
    for path in sorted(profiler_root.iterdir()):
        if not path.is_dir():
            continue
        inventory_path = path / "header_inventory.json"
        candidates_path = path / "canonical_field_candidates.json"
        header_hash_path = path / "header_hash.txt"
        if not inventory_path.exists() or not candidates_path.exists() or not header_hash_path.exists():
            continue
        inventory = _load_json(inventory_path)
        artifacts[inventory["source"]["file_name"]] = {
            "header_inventory": inventory,
            "candidates_report": _load_json(candidates_path),
            "observed_header_hash": header_hash_path.read_text(encoding="utf-8").strip(),
        }
    return artifacts


def _find_header_column(
    header_inventory: Mapping[str, Any],
    candidate: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if candidate is None:
        return None
    fingerprint = _fingerprint_tuple(candidate.get("fingerprint", {}))
    sheet_name = str(candidate.get("sheet_name", ""))
    for sheet in header_inventory.get("sheets", []):
        if sheet_name and str(sheet.get("sheet_name", "")) != sheet_name:
            continue
        for column in sheet.get("columns", []):
            if _fingerprint_tuple(column.get("fingerprint", {})) == fingerprint:
                return column
    return None


def _choose_primary_candidate(
    profile_field: Mapping[str, Any],
    report_field: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    report_candidates = list(report_field.get("candidates", []))
    seeded = list(profile_field.get("source_candidates", []))
    if seeded:
        seeded_fp = _fingerprint_tuple(seeded[0].get("fingerprint", {}))
        for candidate in report_candidates:
            if _fingerprint_tuple(candidate.get("fingerprint", {})) == seeded_fp:
                return candidate
    plausible = [candidate for candidate in report_candidates if _candidate_is_plausible(candidate)]
    if plausible:
        return plausible[0]
    return report_candidates[0] if report_candidates else None


def _seeded_fingerprint_missing_reason(
    profile_field: Mapping[str, Any],
    report_field: Mapping[str, Any],
) -> str:
    seeded = list(profile_field.get("source_candidates", []))
    if not seeded:
        return ""
    seeded_fp = _fingerprint_tuple(seeded[0].get("fingerprint", {}))
    for candidate in report_field.get("candidates", []):
        if _fingerprint_tuple(candidate.get("fingerprint", {})) == seeded_fp:
            return ""
    return "Seeded fingerprint was not rediscovered in current profiler candidates."


def _donor_similarity(
    candidate: Mapping[str, Any] | None,
    donor_profile: Mapping[str, Any] | None,
    field_name: str,
    self_profile_id: str,
) -> str:
    if donor_profile is None:
        return "NO_DONOR_SOURCE"
    if self_profile_id == donor_profile.get("profile_id"):
        return "SELF_REFERENCE"
    donor_field = donor_profile.get("field_mapping", {}).get(field_name, {})
    donor_candidates = donor_field.get("source_candidates", [])
    if not donor_candidates:
        return "NO_DONOR_SOURCE"
    if candidate is None:
        return "DIFFERENT_FINGERPRINT"
    candidate_fp = candidate.get("fingerprint", {})
    donor_fp = donor_candidates[0].get("fingerprint", {})
    if _fingerprint_tuple(candidate_fp) == _fingerprint_tuple(donor_fp):
        return "EXACT_FINGERPRINT_MATCH"
    if str(candidate_fp.get("display_header", "")).strip().lower() == str(donor_fp.get("display_header", "")).strip().lower():
        return "SAME_DISPLAY_HEADER"
    if str(candidate_fp.get("field_code", "")).strip() == str(donor_fp.get("field_code", "")).strip():
        return "SAME_FIELD_CODE"
    return "DIFFERENT_FINGERPRINT"


def _ai_recommendation(
    field_name: str,
    profile_field: Mapping[str, Any],
    report_field: Mapping[str, Any],
    bridge_field: Mapping[str, Any] | None,
    seeded_fingerprint_missing_reason: str = "",
) -> tuple[str, str, str]:
    plausible_candidates = [candidate for candidate in report_field.get("candidates", []) if _candidate_is_plausible(candidate)]
    status = str(report_field.get("status", "MISSING"))
    seeded_candidates = list(profile_field.get("source_candidates", []))

    if not plausible_candidates:
        missing_reason = "No plausible data-sheet candidate was discovered for this field."
        if seeded_fingerprint_missing_reason:
            missing_reason = f"{seeded_fingerprint_missing_reason} {missing_reason}".strip()
        if bridge_field:
            missing_reason = f"{missing_reason} {bridge_field.get('review_reason', '')}".strip()
        return "MISSING", "", missing_reason

    if status == "AMBIGUOUS" or len(plausible_candidates) > 1:
        ambiguity_reason = f"{len(plausible_candidates)} plausible candidates still need four-layer review."
        if seeded_fingerprint_missing_reason:
            ambiguity_reason = f"{seeded_fingerprint_missing_reason} {ambiguity_reason}".strip()
        return (
            "AMBIGUOUS",
            ambiguity_reason,
            "",
        )

    if seeded_fingerprint_missing_reason:
        if field_name in REQUIRED_FIELDS:
            return "MEDIUM_CONFIDENCE_REVIEW", seeded_fingerprint_missing_reason, ""
        return "LOW_CONFIDENCE_REVIEW", seeded_fingerprint_missing_reason, ""

    if seeded_candidates and str(seeded_candidates[0].get("mapping_status", "")) == "APPROVED":
        return "HIGH_CONFIDENCE_MATCH", "", ""

    if field_name in REQUIRED_FIELDS:
        return "MEDIUM_CONFIDENCE_REVIEW", "", ""
    return "LOW_CONFIDENCE_REVIEW", "", ""


def _confidence_level(ai_recommendation: str) -> str:
    return {
        "HIGH_CONFIDENCE_MATCH": "high",
        "MEDIUM_CONFIDENCE_REVIEW": "medium",
        "LOW_CONFIDENCE_REVIEW": "low",
        "MISSING": "none",
        "AMBIGUOUS": "low",
        "NOT_APPLICABLE": "none",
    }[ai_recommendation]


def _group_bucket(
    discovery_entry: Mapping[str, Any],
    grouping_entry: Mapping[str, Any] | None,
    unresolved_entry: Mapping[str, Any] | None,
    duplicate_count: int,
) -> str:
    if discovery_entry.get("profile_id") in (None, ""):
        return "unreadable_or_unsupported_source_format"
    if duplicate_count > 1:
        return "duplicate_or_competing_export_variants"
    if grouping_entry is None:
        return "unreadable_or_unsupported_source_format"
    missing_required = list((unresolved_entry or {}).get("summary", {}).get("missing_required_fields", []))
    if missing_required:
        return "missing_pr_critical_fields_quarantine_candidate"
    top_neighbors = grouping_entry.get("closest_neighbors", [])
    tx_similarity = 1.0 if discovery_entry.get("profile_id") == "tx_mini_pr_v1" else 0.0
    mw_similarity = 1.0 if discovery_entry.get("profile_id") == "mw_eos_swap_pr_v1" else 0.0
    for neighbor in top_neighbors:
        similarity = float(neighbor.get("fingerprint_similarity", 0.0))
        if neighbor.get("profile_id") == "tx_mini_pr_v1":
            tx_similarity = max(tx_similarity, similarity)
        if neighbor.get("profile_id") == "mw_eos_swap_pr_v1":
            mw_similarity = max(mw_similarity, similarity)
    if tx_similarity >= 0.80:
        return "same_or_highly_similar_to_tx_mini"
    if mw_similarity >= 0.45:
        return "similar_to_mw_eos_swap"
    return "different_structure_pr_critical_present"


def _group_summary(
    group_id: str,
    entries: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    blockers: List[str] = []
    for entry in entries:
        blockers.extend(entry.get("group_blockers", []))
    unique_blockers = sorted(dict.fromkeys(blockers))
    return {
        "group_id": group_id,
        "group_label": GROUP_METADATA[group_id],
        "du_models": sorted(dict.fromkeys(str(entry["du_model_name"]) for entry in entries)),
        "reference_files": sorted(dict.fromkeys(str(entry["source_file_name"]) for entry in entries)),
        "shared_mapping_pattern": "Discovery-only grouping derived from exact fingerprint overlap and current unresolved field state.",
        "differences_from_tx_mini": "Compare per-row donor similarity statuses in the local matrix output.",
        "differences_from_mw_eos": "Compare per-row donor similarity statuses in the local matrix output.",
        "pr_critical_blockers": unique_blockers,
        "recommended_next_implementation_sequence": (
            "Start with the highest-confidence rows in this group, then review ambiguous PR-critical fields before any profile implementation."
        ),
    }


def build_matrix_registry(
    *,
    discovery_registry: Mapping[str, Any],
    grouping_registry: Mapping[str, Any],
    unresolved_registry: Mapping[str, Any],
    bridge_registry: Mapping[str, Any],
    profiles: Mapping[str, Mapping[str, Any]],
    inventory_registry: Mapping[str, Any],
    profiler_artifacts: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    inventory_paths = _inventory_paths_by_name(inventory_registry)
    unresolved_by_profile = {entry["profile_id"]: entry for entry in unresolved_registry.get("entries", [])}
    bridge_by_profile = {entry["profile_id"]: entry for entry in bridge_registry.get("entries", [])}
    grouping_by_profile = {entry.get("profile_id"): entry for entry in grouping_registry.get("entries", [])}
    duplicates_by_du = defaultdict(int)
    for entry in discovery_registry.get("entries", []):
        duplicates_by_du[str(entry.get("du_model_name", ""))] += 1

    tx_mini_profile = profiles.get("tx_mini_pr_v1")
    mw_eos_profile = profiles.get("mw_eos_swap_pr_v1")

    rows: List[Dict[str, Any]] = []
    export_summaries: List[Dict[str, Any]] = []

    for discovery_entry in discovery_registry.get("entries", []):
        raw_profile_id = discovery_entry.get("profile_id")
        profile_id = str(raw_profile_id) if raw_profile_id is not None else None
        artifact = profiler_artifacts.get(str(discovery_entry["source_file_name"]))
        if profile_id is None or profile_id not in profiles:
            group_id = "unreadable_or_unsupported_source_format"
            export_summaries.append(
                {
                    "profile_id": raw_profile_id,
                    "du_model_name": discovery_entry["du_model_name"],
                    "source_file_name": discovery_entry["source_file_name"],
                    "group_id": group_id,
                    "group_label": GROUP_METADATA[group_id],
                    "group_blockers": ["profile_id_missing"],
                    "recommendation_counts": {},
                    "status_note": "No profile_id was assigned for this discovery entry, so row-level profile field mapping was skipped.",
                }
            )
            continue
        profile = profiles[profile_id]
        if artifact is None:
            group_id = "unreadable_or_unsupported_source_format"
            export_summaries.append(
                {
                    "profile_id": raw_profile_id,
                    "du_model_name": discovery_entry["du_model_name"],
                    "source_file_name": discovery_entry["source_file_name"],
                    "group_id": group_id,
                    "group_label": GROUP_METADATA[group_id],
                    "group_blockers": ["profiler_artifact_missing"],
                    "recommendation_counts": {},
                    "status_note": "Profiler artifacts were not available for this discovery entry, so row-level profile field mapping was skipped.",
                }
            )
            continue
        header_inventory = artifact["header_inventory"]
        candidates_report = artifact["candidates_report"]
        unresolved_entry = unresolved_by_profile.get(profile_id, {})
        bridge_entry = bridge_by_profile.get(profile_id, {})
        grouping_entry = grouping_by_profile.get(profile_id)
        group_id = _group_bucket(
            discovery_entry,
            grouping_entry,
            unresolved_entry,
            duplicates_by_du[str(discovery_entry.get("du_model_name", ""))],
        )
        group_blockers = list(unresolved_entry.get("summary", {}).get("missing_required_fields", []))
        group_blockers.extend(unresolved_entry.get("summary", {}).get("competing_candidate_fields", []))

        recommendation_counts: Dict[str, int] = defaultdict(int)
        for field_name in TRACKED_CANONICAL_FIELDS:
            profile_field = profile.get("field_mapping", {}).get(field_name, {})
            report_field = candidates_report.get("fields", {}).get(field_name, {"status": "MISSING", "candidates": []})
            primary_candidate = _choose_primary_candidate(profile_field, report_field)
            seeded_fingerprint_missing_reason = _seeded_fingerprint_missing_reason(profile_field, report_field)
            header_column = _find_header_column(header_inventory, primary_candidate)
            bridge_field = bridge_entry.get("field_bridges", {}).get(field_name)
            ai_recommendation, ambiguity_reason, missing_reason = _ai_recommendation(
                field_name,
                profile_field,
                report_field,
                bridge_field,
                seeded_fingerprint_missing_reason,
            )
            recommendation_counts[ai_recommendation] += 1
            fingerprint = dict(primary_candidate.get("fingerprint", {})) if primary_candidate else {
                "field_code": "",
                "wbs_stage": "",
                "task_name": "",
                "display_header": "",
            }
            source_header_values = list((header_column or {}).get("raw_header_values", ["", "", "", ""]))
            row = {
                "du_model_candidate": discovery_entry["du_model_name"],
                "profile_id_candidate": profile_id,
                "original_reference_file_name": discovery_entry["source_file_name"],
                "local_relative_path_under_info_reference": inventory_paths.get(discovery_entry["source_file_name"], ""),
                "sheet_or_view_candidate": str(primary_candidate.get("sheet_name", "")) if primary_candidate else str(discovery_entry.get("view_label", "")),
                "canonical_pr_field": field_name,
                "requirement_class": _requirement_class(field_name),
                "candidate_four_layer_fingerprint": fingerprint,
                "source_header_values": source_header_values,
                "transform_candidate": " -> ".join(profile_field.get("transforms", [])) if profile_field.get("transforms") else "(none proposed)",
                "similarity_to_tx_mini_approved_mapping": _donor_similarity(primary_candidate, tx_mini_profile, field_name, profile_id),
                "similarity_to_mw_eos_discovered_mapping": _donor_similarity(primary_candidate, mw_eos_profile, field_name, profile_id),
                "confidence_level": _confidence_level(ai_recommendation),
                "ambiguity_reason": ambiguity_reason,
                "missing_field_reason": missing_reason,
                "ai_recommendation_class": ai_recommendation,
                "human_decision": "",
                "business_note": "",
            }
            rows.append(row)

        export_summaries.append(
            {
                "profile_id": profile_id,
                "du_model_name": discovery_entry["du_model_name"],
                "source_file_name": discovery_entry["source_file_name"],
                "group_id": group_id,
                "group_label": GROUP_METADATA[group_id],
                "group_blockers": sorted(dict.fromkeys(group_blockers)),
                "recommendation_counts": dict(sorted(recommendation_counts.items())),
            }
        )

    grouped_entries: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for entry in export_summaries:
        grouped_entries[str(entry["group_id"])].append(entry)

    groups = [_group_summary(group_id, entries) for group_id, entries in sorted(grouped_entries.items())]
    return {
        "schema_version": "1.0",
        "artifact_type": "all_du_mapping_recommendation_matrix",
        "export_count": len(export_summaries),
        "row_count": len(rows),
        "groups": groups,
        "export_summaries": export_summaries,
        "rows": rows,
        "notes": [
            "This matrix is discovery-only and does not approve mappings, profile lifecycle transitions, or ECC output.",
            "Rows use four-layer fingerprints as the authoritative source-column identity. Excel column position is not approval evidence.",
        ],
    }


def matrix_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# All-DU Mapping Recommendation Matrix (LOCAL-ONLY REVIEW COPY)",
        "",
        "Sanitized discovery-only matrix across the tracked MW DU exports.",
        "",
        f"- Export count: `{registry.get('export_count', 0)}`",
        f"- Matrix rows: `{registry.get('row_count', 0)}`",
        "",
        "| DU model | Field | Requirement | Recommendation | Confidence | TX Mini similarity | MW EOS similarity |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in registry.get("rows", []):
        lines.append(
            "| {du} | `{field}` | `{req}` | `{rec}` | `{conf}` | `{tx}` | `{mw}` |".format(
                du=row["du_model_candidate"].replace("|", "\\|"),
                field=row["canonical_pr_field"],
                req=row["requirement_class"],
                rec=row["ai_recommendation_class"],
                conf=row["confidence_level"],
                tx=row["similarity_to_tx_mini_approved_mapping"],
                mw=row["similarity_to_mw_eos_discovered_mapping"],
            )
        )
    return "\n".join(lines) + "\n"


def review_summary_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU All-DU Discovery Mapping Review",
        "",
        "Discovery-only summary for the all-MW-DU mapping recommendation matrix generated for Issue `#19`.",
        "",
        f"- Export count: `{registry.get('export_count', 0)}`",
        f"- Matrix rows: `{registry.get('row_count', 0)}`",
        "",
        "## Group Summary",
        "",
    ]
    for group in registry.get("groups", []):
        lines.append(f"### {group['group_label']}")
        lines.append("")
        lines.append(f"- DU models: {', '.join(group.get('du_models', [])) or 'None'}")
        lines.append(f"- Reference files: {', '.join(group.get('reference_files', [])) or 'None'}")
        lines.append(f"- PR-critical blockers: {', '.join(group.get('pr_critical_blockers', [])) or 'None'}")
        lines.append(f"- Recommended next sequence: {group.get('recommended_next_implementation_sequence', '')}")
        lines.append("")

    lines.extend(
        [
            "## Export Summary",
            "",
            "| DU model | Group | High | Medium | Low | Missing | Ambiguous |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for entry in registry.get("export_summaries", []):
        counts = entry.get("recommendation_counts", {})
        lines.append(
            "| {du} | {group} | {high} | {medium} | {low} | {missing} | {ambiguous} |".format(
                du=entry["du_model_name"].replace("|", "\\|"),
                group=entry["group_label"].replace("|", "\\|"),
                high=counts.get("HIGH_CONFIDENCE_MATCH", 0),
                medium=counts.get("MEDIUM_CONFIDENCE_REVIEW", 0),
                low=counts.get("LOW_CONFIDENCE_REVIEW", 0),
                missing=counts.get("MISSING", 0),
                ambiguous=counts.get("AMBIGUOUS", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- This report is sanitized and metadata-only. It includes no raw customer rows or site lists.",
            "- The full row-level matrix is written to ignored local `output/` artifacts for human review.",
            "- No mapping approval, lifecycle promotion, or ECC enablement is performed by this artifact.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_all_du_mapping_review_outputs(
    profiler_root: Path,
    discovery_registry_path: Path,
    grouping_registry_path: Path,
    unresolved_registry_path: Path,
    bridge_registry_path: Path,
    profile_paths: Iterable[Path],
    inventory_path: Path,
    review_markdown_path: Path,
    output_json_path: Path,
    output_markdown_path: Path,
) -> Dict[str, Any]:
    discovery_registry = _load_json(discovery_registry_path)
    grouping_registry = _load_json(grouping_registry_path)
    unresolved_registry = _load_json(unresolved_registry_path)
    bridge_registry = _load_json(bridge_registry_path)
    inventory_registry = _load_json(inventory_path)
    profiles = {
        path.stem: _load_json(path)
        for path in profile_paths
    }
    profiler_artifacts = _load_profiler_artifacts(profiler_root)
    registry = build_matrix_registry(
        discovery_registry=discovery_registry,
        grouping_registry=grouping_registry,
        unresolved_registry=unresolved_registry,
        bridge_registry=bridge_registry,
        profiles=profiles,
        inventory_registry=inventory_registry,
        profiler_artifacts=profiler_artifacts,
    )
    review_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    review_markdown_path.write_text(review_summary_markdown(registry), encoding="utf-8")
    output_json_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_markdown_path.write_text(matrix_markdown(registry), encoding="utf-8")
    return registry


def main() -> int:
    profiler_root = _find_profiler_root()
    profile_paths = discover_du_profile_paths()
    registry = write_all_du_mapping_review_outputs(
        profiler_root,
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        profile_paths,
        Path("output/local_du_reference_inventory.json"),
        Path("docs/MW_DU_All_DU_Discovery_Mapping_Review.md"),
        Path("output/all_du_mapping_recommendation_matrix.json"),
        Path("output/all_du_mapping_recommendation_matrix.md"),
    )
    print(
        f"Wrote all-DU mapping recommendation matrix for {registry['export_count']} exports "
        f"({registry['row_count']} rows)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
