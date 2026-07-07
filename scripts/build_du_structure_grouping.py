"""Build discovery-only DU structure grouping guidance from profiler artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from build_du_discovery_registry import build_discovery_registry


FINGERPRINT_KEYS = ("field_code", "wbs_stage", "task_name", "display_header")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_signature(fingerprint: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return tuple(str(fingerprint.get(key, "")) for key in FINGERPRINT_KEYS)


def load_profile_artifact(profile_dir: Path) -> Dict[str, Any]:
    inventory = _load_json(profile_dir / "header_inventory.json")
    fingerprint_set = set()
    for sheet in inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            fingerprint_set.add(_fingerprint_signature(column.get("fingerprint", {})))
    return {
        "profile_dir": str(profile_dir),
        "source_file_name": inventory["source"]["file_name"],
        "observed_header_hash": (profile_dir / "header_hash.txt").read_text(encoding="utf-8").strip(),
        "fingerprint_set": fingerprint_set,
        "fingerprint_count": len(fingerprint_set),
    }


def fingerprint_similarity(left: set[tuple[str, str, str, str]], right: set[tuple[str, str, str, str]]) -> float:
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def _signal_for_similarity(similarity: float) -> tuple[str, str]:
    if similarity >= 0.60:
        return "POSSIBLE_REUSE_REVIEW", "Closest neighbor shares a strong majority of exact four-layer fingerprints."
    if similarity >= 0.45:
        return "PARTIAL_REUSE_REVIEW", "Closest neighbor shares some structure, but differences are large enough to require careful profile comparison."
    return "SEPARATE_PROFILE_LIKELY", "Closest neighbor overlap is low, so a separate profile is more likely than direct reuse."


def build_grouping_entry(
    artifact: Mapping[str, Any],
    all_artifacts: Iterable[Mapping[str, Any]],
    discovery_entry: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    neighbors: List[Dict[str, Any]] = []
    for other in all_artifacts:
        if other["source_file_name"] == artifact["source_file_name"]:
            continue
        shared = len(artifact["fingerprint_set"] & other["fingerprint_set"])
        union = len(artifact["fingerprint_set"] | other["fingerprint_set"])
        neighbors.append(
            {
                "source_file_name": other["source_file_name"],
                "du_model_name": (discovery_entry or {}).get("du_model_name") if False else None,
                "observed_header_hash": other["observed_header_hash"],
                "fingerprint_similarity": fingerprint_similarity(artifact["fingerprint_set"], other["fingerprint_set"]),
                "shared_fingerprint_count": shared,
                "union_fingerprint_count": union,
            }
        )
    neighbors.sort(
        key=lambda item: (
            -float(item["fingerprint_similarity"]),
            item["source_file_name"],
        )
    )
    closest = neighbors[:3]
    top_similarity = closest[0]["fingerprint_similarity"] if closest else 0.0
    grouping_signal, grouping_reason = _signal_for_similarity(top_similarity)
    result = {
        "source_file_name": artifact["source_file_name"],
        "observed_header_hash": artifact["observed_header_hash"],
        "fingerprint_count": artifact["fingerprint_count"],
        "grouping_signal": grouping_signal,
        "grouping_reason": grouping_reason,
        "closest_neighbors": closest,
    }
    if discovery_entry:
        result.update(
            {
                "project_key": discovery_entry["project_key"],
                "du_model_name": discovery_entry["du_model_name"],
                "du_model_id": discovery_entry["du_model_id"],
                "view_label": discovery_entry["view_label"],
                "view_id": discovery_entry["view_id"],
                "profile_id": discovery_entry.get("profile_id"),
            }
        )
    return result


def build_grouping_registry(profile_root: Path) -> Dict[str, Any]:
    artifacts = [load_profile_artifact(path) for path in sorted(profile_root.iterdir()) if path.is_dir()]
    discovery_registry = build_discovery_registry(profile_root)
    discovery_by_source = {entry["source_file_name"]: entry for entry in discovery_registry.get("entries", [])}
    entries = [
        build_grouping_entry(artifact, artifacts, discovery_by_source.get(artifact["source_file_name"]))
        for artifact in artifacts
    ]
    for entry in entries:
        for neighbor in entry["closest_neighbors"]:
            discovery_neighbor = discovery_by_source.get(neighbor["source_file_name"], {})
            neighbor["du_model_name"] = discovery_neighbor.get("du_model_name")
            neighbor["view_label"] = discovery_neighbor.get("view_label")
            neighbor["profile_id"] = discovery_neighbor.get("profile_id")
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_structure_grouping",
        "entries": entries,
    }


def grouping_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Structure Grouping Review",
        "",
        "Discovery-only structural overlap review based on exact four-layer fingerprint sets. This is reuse guidance, not approval for shared production profiles.",
    ]
    for entry in registry.get("entries", []):
        lines.extend(
            [
                "",
                f"## {entry.get('du_model_name', entry['source_file_name'])}",
                "",
                f"- Source file: `{entry['source_file_name']}`",
                f"- Header hash: `{entry['observed_header_hash']}`",
                f"- Fingerprint count: `{entry['fingerprint_count']}`",
                f"- Grouping signal: `{entry['grouping_signal']}`",
                f"- Reason: {entry['grouping_reason']}",
                "- Closest neighbors:",
            ]
        )
        for neighbor in entry.get("closest_neighbors", []):
            lines.append(
                "  - `{source}` ({du_model}) similarity=`{similarity:.3f}` shared=`{shared}` union=`{union}` profile=`{profile}`".format(
                    source=neighbor["source_file_name"],
                    du_model=neighbor.get("du_model_name") or "Unknown",
                    similarity=neighbor["fingerprint_similarity"],
                    shared=neighbor["shared_fingerprint_count"],
                    union=neighbor["union_fingerprint_count"],
                    profile=neighbor.get("profile_id") or "None",
                )
            )
    return "\n".join(lines) + "\n"


def write_grouping_outputs(profile_root: Path, registry_path: Path, markdown_path: Path) -> None:
    registry = build_grouping_registry(profile_root)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(grouping_markdown(registry), encoding="utf-8")


def main() -> int:
    write_grouping_outputs(
        Path("output/du-20260706-profile"),
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("docs/MW_DU_Structure_Grouping_Review.md"),
    )
    print("Wrote DU structure grouping review outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
