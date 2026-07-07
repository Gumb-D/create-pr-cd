"""Build a 10-export coverage review over the discovery registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


TRACKED_DRAFT_PROFILE = "TRACKED_DRAFT_PROFILE"
DONOR_REVIEW_CANDIDATE = "DONOR_REVIEW_CANDIDATE"
BACKLOG_DISCOVERY_ONLY = "BACKLOG_DISCOVERY_ONLY"


def _missing_skill_fields(entry: Mapping[str, Any]) -> list[str]:
    presence = entry.get("skill_field_presence", {})
    if not isinstance(presence, Mapping):
        return []
    return [str(field) for field, present in presence.items() if present is False]


def _coverage_status(entry: Mapping[str, Any]) -> tuple[str, str]:
    if entry.get("profile_id"):
        return (
            TRACKED_DRAFT_PROFILE,
            "Continue tracked profile review through the existing DRAFT discovery packet.",
        )

    presence = entry.get("skill_field_presence", {})
    if isinstance(presence, Mapping) and presence.get("existing_tss_pr") and presence.get("existing_ti_pr"):
        return (
            DONOR_REVIEW_CANDIDATE,
            "Preserve as a donor-review candidate only; do not treat this export as an approved reusable mapping source.",
        )

    return (
        BACKLOG_DISCOVERY_ONLY,
        "Keep in discovery backlog until a future review wave explicitly selects this export for profile onboarding.",
    )


def build_coverage_registry(discovery_registry: Mapping[str, Any]) -> Dict[str, Any]:
    entries = []
    tracked = 0
    donor = 0
    backlog = 0
    for item in discovery_registry.get("entries", []):
        if not isinstance(item, Mapping):
            continue
        coverage_status, next_action = _coverage_status(item)
        if coverage_status == TRACKED_DRAFT_PROFILE:
            tracked += 1
        elif coverage_status == DONOR_REVIEW_CANDIDATE:
            donor += 1
        else:
            backlog += 1
        entries.append(
            {
                "du_model_name": item.get("du_model_name", ""),
                "source_file_name": item.get("source_file_name", ""),
                "coverage_status": coverage_status,
                "profile_id": item.get("profile_id"),
                "profile_status": item.get("profile_status"),
                "profile_version": item.get("profile_version"),
                "mapping_version": item.get("mapping_version"),
                "observed_header_hash": item.get("observed_header_hash", ""),
                "missing_skill_fields": _missing_skill_fields(item),
                "next_action": next_action,
            }
        )
    return {
        "schema_version": "1.0",
        "registry_type": "du_export_coverage_review",
        "summary": {
            "total_exports": len(entries),
            "tracked_profile_exports": tracked,
            "donor_review_candidates": donor,
            "backlog_discovery_only_exports": backlog,
        },
        "entries": entries,
        "notes": [
            "This coverage review summarizes the current evidence position across the 10 profiled DU exports.",
            "Coverage status here is discovery-only planning evidence and does not approve any profile or reusable source mapping.",
        ],
    }


def coverage_markdown(registry: Mapping[str, Any]) -> str:
    summary = registry.get("summary", {})
    lines = [
        "# MW DU Export Coverage Review",
        "",
        "Discovery-only coverage review across the 10 profiled DU exports.",
        "",
        "## Summary",
        "",
        f"- Total exports: `{summary.get('total_exports', 0)}`",
        f"- Tracked profile exports: `{summary.get('tracked_profile_exports', 0)}`",
        f"- Donor-review candidates: `{summary.get('donor_review_candidates', 0)}`",
        f"- Backlog discovery-only exports: `{summary.get('backlog_discovery_only_exports', 0)}`",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry.get('du_model_name', '')}")
        lines.append("")
        lines.append(f"- Source file: `{entry.get('source_file_name', '')}`")
        lines.append(f"- Coverage status: `{entry.get('coverage_status', '')}`")
        if entry.get("profile_id"):
            lines.append(
                f"- Profile: `{entry.get('profile_id')}` `{entry.get('profile_version')}` "
                f"(mapping `{entry.get('mapping_version')}`)"
            )
        lines.append(f"- Observed header hash: `{entry.get('observed_header_hash', '')}`")
        missing = entry.get("missing_skill_fields", [])
        if missing:
            lines.append(f"- Missing skill fields: `{', '.join(missing)}`")
        lines.append(f"- Next action: {entry.get('next_action', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_coverage_outputs(
    discovery_registry_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    discovery_registry = json.loads(discovery_registry_path.read_text(encoding="utf-8"))
    registry = build_coverage_registry(discovery_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(coverage_markdown(registry), encoding="utf-8")


if __name__ == "__main__":
    write_coverage_outputs(
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_export_coverage_review.yaml"),
        Path("docs/MW_DU_Export_Coverage_Review.md"),
    )
    print("Wrote DU export coverage review outputs.")
