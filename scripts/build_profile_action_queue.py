"""Build a prioritized governance action queue for DU profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from du_profile_loader import discover_du_profile_paths, load_du_profile


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _priority(profile_id: str, rank: int) -> str:
    return f"{profile_id}:{rank:02d}"


def _queue_item(
    rank: int,
    profile_id: str,
    action_type: str,
    summary: str,
    *,
    field_name: str | None = None,
    evidence_hint: str | None = None,
) -> Dict[str, Any]:
    item = {
        "priority_id": _priority(profile_id, rank),
        "action_type": action_type,
        "summary": summary,
    }
    if field_name is not None:
        item["field_name"] = field_name
    if evidence_hint is not None:
        item["evidence_hint"] = evidence_hint
    return item


def build_action_queue_entry(
    profile: Mapping[str, Any],
    readiness_entry: Mapping[str, Any],
    unresolved_entry: Mapping[str, Any],
    bridge_entry: Mapping[str, Any],
) -> Dict[str, Any]:
    profile_id = str(profile["profile_id"])
    queue = []
    rank = 1

    for field_name in unresolved_entry.get("summary", {}).get("missing_required_fields", []):
        best_source = bridge_entry.get("field_bridges", {}).get(field_name, {}).get("best_source_export")
        hint = None
        if best_source is not None:
            hint = (
                f"Review donor export {best_source['du_model_name']} with similarity "
                f"{best_source['source_similarity_to_target']:.3f} before deciding derived, manual, or blocking treatment."
            )
        queue.append(
            _queue_item(
                rank,
                profile_id,
                "RESOLVE_MISSING_REQUIRED_FIELD",
                f"Resolve required field `{field_name}` before any lifecycle promotion.",
                field_name=field_name,
                evidence_hint=hint,
            )
        )
        rank += 1

    for field_name in unresolved_entry.get("summary", {}).get("competing_candidate_fields", []):
        queue.append(
            _queue_item(
                rank,
                profile_id,
                "CONFIRM_COMPETING_CANDIDATE",
                f"Choose one exact four-layer source for `{field_name}` from the competing shortlist candidates.",
                field_name=field_name,
                evidence_hint="Use the unresolved review packet to compare the currently selected source against alternates.",
            )
        )
        rank += 1

    for field_name in unresolved_entry.get("summary", {}).get("single_candidate_unverified_fields", []):
        queue.append(
            _queue_item(
                rank,
                profile_id,
                "VERIFY_SINGLE_CANDIDATE",
                f"Verify the current single shortlist-aligned source for `{field_name}`.",
                field_name=field_name,
                evidence_hint="Confirm the four-layer fingerprint and business meaning before changing mapping_status.",
            )
        )
        rank += 1

    if not readiness_entry.get("approved_header_hashes"):
        queue.append(
            _queue_item(
                rank,
                profile_id,
                "APPROVE_HEADER_HASH",
                "Approve at least one header hash for this profile version after the field review is complete.",
                evidence_hint=f"Current observed header hash: {readiness_entry.get('observed_header_hash', '')}",
            )
        )
        rank += 1

    if readiness_entry.get("readiness_status") != "PRODUCTION_READY":
        queue.append(
            _queue_item(
                rank,
                profile_id,
                "HOLD_LIFECYCLE_PROMOTION",
                "Keep the profile blocked from lifecycle promotion until required mappings, header-hash approval, and regression evidence are complete.",
                evidence_hint="Use the transition review as the final stop/go check before any status change.",
            )
        )

    return {
        "profile_id": profile_id,
        "profile_version": profile["profile_version"],
        "mapping_version": profile["mapping_version"],
        "profile_status": profile["status"],
        "du_model_name": readiness_entry.get("du_model_name", ""),
        "readiness_status": readiness_entry.get("readiness_status", ""),
        "observed_header_hash": readiness_entry.get("observed_header_hash", ""),
        "action_queue": queue,
        "notes": [
            "This governance queue records required blockers and optional follow-up review work; it does not grant production permission.",
            "Optional discovery actions remain visible for production Profiles but do not create a lifecycle hold.",
        ],
    }


def build_action_queue_registry(
    profiles: Iterable[Mapping[str, Any]],
    readiness_registry: Mapping[str, Any],
    unresolved_registry: Mapping[str, Any],
    bridge_registry: Mapping[str, Any],
) -> Dict[str, Any]:
    readiness_by_profile = {
        str(entry["profile_id"]): entry for entry in readiness_registry.get("entries", [])
    }
    unresolved_by_profile = {
        str(entry["profile_id"]): entry for entry in unresolved_registry.get("entries", [])
    }
    bridge_by_profile = {
        str(entry["profile_id"]): entry for entry in bridge_registry.get("entries", [])
    }

    entries = []
    for profile in profiles:
        profile_id = str(profile["profile_id"])
        readiness_entry = readiness_by_profile.get(profile_id)
        unresolved_entry = unresolved_by_profile.get(profile_id)
        bridge_entry = bridge_by_profile.get(profile_id)
        if readiness_entry is None or unresolved_entry is None or bridge_entry is None:
            raise ValueError(f"Missing review packet dependency for profile {profile_id}")
        entries.append(
            build_action_queue_entry(profile, readiness_entry, unresolved_entry, bridge_entry)
        )
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_action_queue",
        "entries": entries,
        "notes": [
            "Prioritized governance action queue for current DU Profiles.",
            "Required blockers and optional discovery follow-up are kept distinct.",
        ],
    }


def action_queue_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Action Queue",
        "",
        "Prioritized governance action queue for the current DU Profiles.",
        "",
    ]
    for entry in registry.get("entries", []):
        lines.append(f"## {entry['profile_id']} ({entry['du_model_name']})")
        lines.append("")
        lines.append(f"- Readiness status: `{entry['readiness_status']}`")
        lines.append(f"- Profile status: `{entry['profile_status']}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry.get('observed_header_hash', '')}`")
        lines.append("- Action queue:")
        if not entry.get("action_queue"):
            lines.append("  - `NONE`: No required blocker or optional follow-up action is currently recorded.")
        for item in entry.get("action_queue", []):
            field_suffix = f" `{item['field_name']}`" if item.get("field_name") else ""
            lines.append(
                f"  - `{item['priority_id']}` `{item['action_type']}`{field_suffix}: {item['summary']}"
            )
            if item.get("evidence_hint"):
                lines.append(f"    hint: {item['evidence_hint']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_action_queue_outputs(
    profile_paths: Iterable[Path],
    readiness_path: Path,
    unresolved_path: Path,
    bridge_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    profiles = [load_du_profile(path) for path in profile_paths]
    readiness_registry = _load_json(readiness_path)
    unresolved_registry = _load_json(unresolved_path)
    bridge_registry = _load_json(bridge_path)
    registry = build_action_queue_registry(
        profiles,
        readiness_registry,
        unresolved_registry,
        bridge_registry,
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(action_queue_markdown(registry), encoding="utf-8")


def main() -> int:
    write_action_queue_outputs(
        discover_du_profile_paths(),
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("config/registries/mw_du_profile_action_queue.yaml"),
        Path("docs/MW_DU_Profile_Action_Queue.md"),
    )
    print("Wrote profile action queue outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
