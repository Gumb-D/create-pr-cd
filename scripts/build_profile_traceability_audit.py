"""Build a traceability audit over the generated MW DU profile-centric artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile


ARTIFACT_SPECS = {
    "discovery": {"entry_key": "entries", "type": "layout_entries"},
    "unresolved": {"entry_key": "entries", "type": "profile_entry"},
    "bridge": {"entry_key": "entries", "type": "profile_entry"},
    "readiness": {"entry_key": "entries", "type": "profile_entry"},
    "action_queue": {"entry_key": "entries", "type": "profile_entry"},
    "review_matrix": {"entry_key": "profile_summaries", "type": "profile_summary"},
    "coverage": {"entry_key": "entries", "type": "layout_entries"},
    "transition": {"entry_key": "entries", "type": "profile_entry"},
    "deprecation": {"entry_key": "entries", "type": "profile_entry"},
    "rollback": {"entry_key": "entries", "type": "profile_entry"},
}


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_entries(
    registry: Mapping[str, Any],
    entry_key: str,
    artifact_type: str,
) -> Dict[str, Any]:
    grouped: Dict[str, list[Mapping[str, Any]]] = {}
    for entry in registry.get(entry_key, []):
        if not isinstance(entry, Mapping) or entry.get("profile_id") is None:
            continue
        grouped.setdefault(str(entry["profile_id"]), []).append(entry)
    if artifact_type == "layout_entries":
        return grouped
    index: Dict[str, Mapping[str, Any]] = {}
    for profile_id, entries in grouped.items():
        if len(entries) != 1:
            raise ValueError(f"Profile-centric artifact contains duplicate entries for {profile_id}")
        index[profile_id] = entries[0]
    return index


def _artifact_traceability(
    artifact_id: str,
    artifact_entry: Mapping[str, Any] | list[Mapping[str, Any]] | None,
    profile: Mapping[str, Any],
) -> Dict[str, Any]:
    expected_profile_version = str(profile["profile_version"])
    expected_mapping_version = str(profile["mapping_version"])
    structure = profile.get("export_structure", {})
    expected_header_hash = str(structure.get("observed_header_hash", ""))
    known_hashes = {expected_header_hash}
    known_hashes.update(str(value) for value in structure.get("observed_header_hashes", []) or [])
    known_hashes.update(str(value) for value in structure.get("approved_header_hashes", []) or [])
    known_hashes.discard("")

    if artifact_entry is None or artifact_entry == []:
        return {
            "artifact_id": artifact_id,
            "artifact_status": "MISSING_PROFILE_ENTRY",
            "profile_version_matches": False,
            "mapping_version_matches": False,
            "observed_header_hash_matches": False,
        }

    entries = artifact_entry if isinstance(artifact_entry, list) else [artifact_entry]
    profile_version_matches = all(
        str(entry.get("profile_version", "")) == expected_profile_version for entry in entries
    )
    mapping_version_matches = all(
        str(entry.get("mapping_version", "")) == expected_mapping_version for entry in entries
    )
    entry_hashes = {str(entry.get("observed_header_hash", "")) for entry in entries}
    observed_header_hash_matches = (
        expected_header_hash in entry_hashes
        and bool(entry_hashes)
        and entry_hashes.issubset(known_hashes)
    )
    artifact_status = (
        "TRACEABLE"
        if profile_version_matches and mapping_version_matches and observed_header_hash_matches
        else "TRACEABILITY_REVIEW_REQUIRED"
    )
    return {
        "artifact_id": artifact_id,
        "artifact_status": artifact_status,
        "profile_version_matches": profile_version_matches,
        "mapping_version_matches": mapping_version_matches,
        "observed_header_hash_matches": observed_header_hash_matches,
    }


def build_traceability_registry(
    profiles: Iterable[Mapping[str, Any]],
    registries: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    indexed = {
        artifact_id: _index_entries(
            registry,
            ARTIFACT_SPECS[artifact_id]["entry_key"],
            ARTIFACT_SPECS[artifact_id]["type"],
        )
        for artifact_id, registry in registries.items()
    }

    entries = []
    for profile in profiles:
        artifacts = []
        for artifact_id in ARTIFACT_SPECS:
            artifacts.append(_artifact_traceability(artifact_id, indexed[artifact_id].get(str(profile["profile_id"])), profile))
        traceability_status = (
            "TRACEABLE"
            if all(item["artifact_status"] == "TRACEABLE" for item in artifacts)
            else "TRACEABILITY_REVIEW_REQUIRED"
        )
        entries.append(
            {
                "profile_id": profile["profile_id"],
                "profile_version": profile["profile_version"],
                "mapping_version": profile["mapping_version"],
                "observed_header_hash": profile.get("export_structure", {}).get("observed_header_hash", ""),
                "traceability_status": traceability_status,
                "artifacts": artifacts,
            }
        )

    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_traceability_audit",
        "entries": entries,
        "notes": [
            "This audit checks whether generated profile-centric artifacts carry the live profile version, mapping version, and observed header hash.",
            "A TRACEABLE result means the artifact identity fields line up with the current live profile; it does not imply production approval.",
        ],
    }


def traceability_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Traceability Audit",
        "",
        "Discovery-only audit of profile-version and header-hash traceability across generated profile-centric artifacts.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']}")
        lines.append("")
        lines.append(f"- Traceability status: `{entry['traceability_status']}`")
        lines.append(f"- Profile version: `{entry['profile_version']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry['observed_header_hash']}`")
        lines.append("- Artifacts:")
        for artifact in entry.get("artifacts", []):
            lines.append(
                "  - `{artifact_id}` `{artifact_status}` version={version} mapping={mapping} header_hash={header_hash}".format(
                    artifact_id=artifact["artifact_id"],
                    artifact_status=artifact["artifact_status"],
                    version=artifact["profile_version_matches"],
                    mapping=artifact["mapping_version_matches"],
                    header_hash=artifact["observed_header_hash_matches"],
                )
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_traceability_outputs(
    profile_paths: Iterable[Path],
    registry_paths: Mapping[str, Path],
    registry_path: Path,
    markdown_path: Path,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    registries = {
        artifact_id: _load_json(path)
        for artifact_id, path in registry_paths.items()
    }
    registry = build_traceability_registry(profiles, registries)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(traceability_markdown(registry), encoding="utf-8")


def main() -> int:
    write_traceability_outputs(
        discover_du_profile_paths(),
        {
            "discovery": Path("config/registries/mw_du_model_discovery_registry.yaml"),
            "unresolved": Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
            "bridge": Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
            "readiness": Path("config/registries/mw_du_profile_readiness_review.yaml"),
            "action_queue": Path("config/registries/mw_du_profile_action_queue.yaml"),
            "review_matrix": Path("config/registries/mw_du_profile_review_matrix.yaml"),
            "coverage": Path("config/registries/mw_du_export_coverage_review.yaml"),
            "transition": Path("config/registries/mw_du_profile_transition_review.yaml"),
            "deprecation": Path("config/registries/mw_du_profile_deprecation_review.yaml"),
            "rollback": Path("config/registries/mw_du_profile_rollback_readiness.yaml"),
        },
        Path("config/registries/mw_du_profile_traceability_audit.yaml"),
        Path("docs/MW_DU_Profile_Traceability_Audit.md"),
    )
    print("Wrote profile traceability audit outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
