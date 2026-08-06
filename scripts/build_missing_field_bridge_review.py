"""Build discovery-only bridge guidance for missing required skill fields."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


PROFILE_FIELD_TO_DISCOVERY_KEY = {
    "tx_before_migration": "tx_before_migration",
    "final_backhaul": "final_backhaul",
    "existing_tss_pr_status": "existing_tss_pr",
    "existing_ti_pr_status": "existing_ti_pr",
}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _discovery_by_source(discovery_registry: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {entry["source_file_name"]: entry for entry in discovery_registry.get("entries", [])}


def _grouping_by_source(grouping_registry: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {entry["source_file_name"]: entry for entry in grouping_registry.get("entries", [])}


def build_bridge_entry(
    unresolved_entry: Mapping[str, Any],
    grouping_registry: Mapping[str, Any],
    discovery_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    grouping_entry = _grouping_by_source(grouping_registry)[unresolved_entry["source_file_name"]]
    discovery_entries = list(discovery_registry.get("entries", []))
    field_bridges: Dict[str, Dict[str, Any]] = {}

    for field_name in unresolved_entry.get("summary", {}).get("missing_required_fields", []):
        discovery_key = PROFILE_FIELD_TO_DISCOVERY_KEY[field_name]
        best_source = None

        for neighbor in grouping_entry.get("closest_neighbors", []):
            match = next(
                (
                    entry
                    for entry in discovery_entries
                    if entry["source_file_name"] == neighbor["source_file_name"]
                ),
                None,
            )
            if match and match.get("skill_field_presence", {}).get(discovery_key):
                best_source = {
                    "du_model_name": match["du_model_name"],
                    "source_file_name": match["source_file_name"],
                    "observed_header_hash": match["observed_header_hash"],
                    "source_similarity_to_target": neighbor["fingerprint_similarity"],
                    "profile_id": match.get("profile_id"),
                }
                break

        if best_source is None:
            for entry in sorted(
                discovery_entries,
                key=lambda item: (
                    0 if item.get("skill_field_presence", {}).get(discovery_key) else 1,
                    item["source_file_name"],
                ),
            ):
                if entry.get("skill_field_presence", {}).get(discovery_key):
                    best_source = {
                        "du_model_name": entry["du_model_name"],
                        "source_file_name": entry["source_file_name"],
                        "observed_header_hash": entry["observed_header_hash"],
                        "source_similarity_to_target": 0.0,
                        "profile_id": entry.get("profile_id"),
                    }
                    break

        if best_source is None:
            field_bridges[field_name] = {
                "bridge_status": "NO_SOURCE_EXPORT_FOUND",
                "review_reason": "No profiled export currently shows presence for this missing required skill field.",
                "best_source_export": None,
            }
            continue

        field_bridges[field_name] = {
            "bridge_status": "CROSS_MODEL_REVIEW_REQUIRED",
            "review_reason": "Another profiled export carries the missing field, but cross-model reuse is discovery-only and still requires manual four-layer review.",
            "best_source_export": best_source,
        }

    return {
        "profile_id": unresolved_entry["profile_id"],
        "profile_version": unresolved_entry.get("profile_version", ""),
        "mapping_version": unresolved_entry.get("mapping_version", ""),
        "observed_header_hash": unresolved_entry.get("observed_header_hash", ""),
        "du_model_name": unresolved_entry["du_model_name"],
        "source_file_name": unresolved_entry["source_file_name"],
        "field_bridges": field_bridges,
        "notes": [
            "This bridge review is discovery-only and does not approve borrowing mappings or business rules across DU models.",
            "A bridge candidate is a review lead, not a reusable production mapping.",
        ],
    }


def build_bridge_registry(
    unresolved_registry: Mapping[str, Any],
    grouping_registry: Mapping[str, Any],
    discovery_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_missing_field_bridge_review",
        "entries": [
            build_bridge_entry(entry, grouping_registry, discovery_registry)
            for entry in unresolved_registry.get("entries", [])
        ],
    }


def bridge_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Missing-Field Bridge Review",
        "",
        "Discovery-only bridge guidance for required fields that are still missing in governed DU profiles. This does not approve any cross-model mapping reuse.",
    ]
    for entry in registry.get("entries", []):
        lines.extend(["", f"## {entry['profile_id']} ({entry['du_model_name']})", ""])
        lines.append(f"- Profile version: `{entry.get('profile_version', '')}`")
        lines.append(f"- Mapping version: `{entry.get('mapping_version', '')}`")
        lines.append(f"- Observed header hash: `{entry.get('observed_header_hash', '')}`")
        lines.append("")
        for field_name, field_bridge in entry.get("field_bridges", {}).items():
            lines.append(f"### `{field_name}`")
            lines.append("")
            lines.append(f"- Bridge status: `{field_bridge['bridge_status']}`")
            lines.append(f"- Reason: {field_bridge['review_reason']}")
            best = field_bridge.get("best_source_export")
            if best is None:
                lines.append("- Best source export: `None`")
            else:
                lines.append(
                    "- Best source export: `{du_model}` from `{source}` similarity=`{similarity:.3f}` profile=`{profile}`".format(
                        du_model=best["du_model_name"],
                        source=best["source_file_name"],
                        similarity=best["source_similarity_to_target"],
                        profile=best.get("profile_id") or "None",
                    )
                )
            lines.append("")
    return "\n".join(lines) + "\n"


def write_bridge_outputs(
    unresolved_path: Path,
    grouping_path: Path,
    discovery_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    unresolved_registry = _load_json(unresolved_path)
    grouping_registry = _load_json(grouping_path)
    discovery_registry = _load_json(discovery_path)
    registry = build_bridge_registry(unresolved_registry, grouping_registry, discovery_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(bridge_markdown(registry), encoding="utf-8")


def main() -> int:
    write_bridge_outputs(
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("docs/MW_DU_Missing_Field_Bridge_Review.md"),
    )
    print("Wrote missing-field bridge review outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
