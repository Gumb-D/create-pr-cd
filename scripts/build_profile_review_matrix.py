"""Build a cross-profile discovery-only review matrix from profile action queues."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _action_rank(action_type: str) -> int:
    return {
        "RESOLVE_MISSING_REQUIRED_FIELD": 1,
        "CONFIRM_COMPETING_CANDIDATE": 2,
        "VERIFY_SINGLE_CANDIDATE": 3,
        "APPROVE_HEADER_HASH": 4,
        "HOLD_LIFECYCLE_PROMOTION": 5,
    }.get(action_type, 99)


def _queue_key(item: Mapping[str, Any]) -> Tuple[str, str]:
    return str(item["action_type"]), str(item.get("field_name") or "")


def build_review_matrix_registry(action_queue_registry: Mapping[str, Any]) -> Dict[str, Any]:
    profile_summaries: List[Dict[str, Any]] = []
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for entry in action_queue_registry.get("entries", []):
        profile_id = str(entry["profile_id"])
        queue = list(entry.get("action_queue", []))
        action_type_counts: Dict[str, int] = {}
        for item in queue:
            action_type = str(item["action_type"])
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1

            key = _queue_key(item)
            batch_item = grouped.setdefault(
                key,
                {
                    "action_type": action_type,
                    "field_name": item.get("field_name"),
                    "summary": item["summary"],
                    "profiles": [],
                    "profile_priority_ids": [],
                    "evidence_hints": [],
                },
            )
            batch_item["profiles"].append(profile_id)
            batch_item["profile_priority_ids"].append(str(item["priority_id"]))
            hint = item.get("evidence_hint")
            if hint and hint not in batch_item["evidence_hints"]:
                batch_item["evidence_hints"].append(hint)

        profile_summaries.append(
            {
                "profile_id": profile_id,
                "profile_version": entry.get("profile_version", ""),
                "du_model_name": entry.get("du_model_name", ""),
                "mapping_version": entry.get("mapping_version", ""),
                "observed_header_hash": entry.get("observed_header_hash", ""),
                "readiness_status": entry.get("readiness_status", ""),
                "action_count": len(queue),
                "action_type_counts": action_type_counts,
            }
        )

    batch_review_queue = sorted(
        grouped.values(),
        key=lambda item: (
            _action_rank(str(item["action_type"])),
            -len(item["profiles"]),
            str(item.get("field_name") or ""),
            str(item["summary"]),
        ),
    )
    for index, item in enumerate(batch_review_queue, start=1):
        item["profiles"] = sorted(item["profiles"])
        item["profile_priority_ids"] = sorted(item["profile_priority_ids"])
        item["profile_count"] = len(item["profiles"])
        item["batch_priority"] = index

    profile_summaries.sort(key=lambda item: str(item["profile_id"]))

    return {
        "schema_version": "1.0",
        "registry_type": "discovery_profile_review_matrix",
        "profile_count": len(profile_summaries),
        "profile_summaries": profile_summaries,
        "batch_review_queue": batch_review_queue,
        "notes": [
            "This review matrix is discovery-only and batches repeated manual-review themes across current DRAFT profiles.",
            "Batch priorities are review-order guidance only and do not approve any mapping, header hash, or lifecycle transition.",
        ],
    }


def review_matrix_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Profile Review Matrix",
        "",
        "Discovery-only cross-profile review matrix for the current DRAFT profiles.",
        "",
        f"- Profile count: `{registry.get('profile_count', 0)}`",
        f"- Batched review items: `{len(registry.get('batch_review_queue', []))}`",
        "",
        "## Batch Review Queue",
        "",
    ]

    for item in registry.get("batch_review_queue", []):
        field_suffix = f" `{item['field_name']}`" if item.get("field_name") else ""
        lines.append(
            f"- Batch priority `{item['batch_priority']:02d}` `{item['action_type']}`{field_suffix}: {item['summary']}"
        )
        lines.append(
            f"  profiles ({item['profile_count']}): {', '.join(item.get('profiles', []))}"
        )
        lines.append(
            f"  priority ids: {', '.join(item.get('profile_priority_ids', []))}"
        )
        for hint in item.get("evidence_hints", []):
            lines.append(f"  hint: {hint}")

    lines.extend(
        [
            "",
            "## Profile Summary",
            "",
        ]
    )
    for entry in registry.get("profile_summaries", []):
        lines.append(f"### {entry['profile_id']} ({entry['du_model_name']})")
        lines.append("")
        lines.append(f"- Readiness status: `{entry['readiness_status']}`")
        lines.append(f"- Profile version: `{entry.get('profile_version', '')}`")
        lines.append(f"- Mapping version: `{entry['mapping_version']}`")
        lines.append(f"- Observed header hash: `{entry.get('observed_header_hash', '')}`")
        lines.append(f"- Action count: `{entry['action_count']}`")
        lines.append("- Action type counts:")
        for action_type, count in sorted(entry.get("action_type_counts", {}).items(), key=lambda item: (_action_rank(item[0]), item[0])):
            lines.append(f"  - `{action_type}`: `{count}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_review_matrix_outputs(
    action_queue_path: Path,
    registry_path: Path,
    markdown_path: Path,
) -> None:
    action_queue_registry = _load_json(action_queue_path)
    registry = build_review_matrix_registry(action_queue_registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(review_matrix_markdown(registry), encoding="utf-8")


def main() -> int:
    write_review_matrix_outputs(
        Path("config/registries/mw_du_profile_action_queue.yaml"),
        Path("config/registries/mw_du_profile_review_matrix.yaml"),
        Path("docs/MW_DU_Profile_Review_Matrix.md"),
    )
    print("Wrote profile review matrix outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
