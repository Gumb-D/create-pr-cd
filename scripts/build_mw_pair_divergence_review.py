"""Build a discovery-only divergence review for the MW EOS and ZTE MW profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _selected_candidate(profile: Mapping[str, Any], field_name: str) -> Mapping[str, Any] | None:
    candidates = profile.get("field_mapping", {}).get(field_name, {}).get("source_candidates", [])
    return candidates[0] if candidates else None


def _display_header(candidate: Mapping[str, Any] | None) -> str | None:
    if not candidate:
        return None
    return candidate.get("fingerprint", {}).get("display_header")


def build_pair_review(left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
    field_differences: Dict[str, Dict[str, Any]] = {}
    shared_missing_required_fields = []

    all_fields = sorted(set(left.get("field_mapping", {}).keys()) | set(right.get("field_mapping", {}).keys()))
    for field_name in all_fields:
        left_field = left.get("field_mapping", {}).get(field_name, {})
        right_field = right.get("field_mapping", {}).get(field_name, {})
        left_selected = _selected_candidate(left, field_name)
        right_selected = _selected_candidate(right, field_name)
        left_required = bool(left_field.get("required", False))
        right_required = bool(right_field.get("required", False))

        if left_selected is None and right_selected is None:
            if left_required and right_required:
                status = "BOTH_MISSING_REQUIRED"
                reason = "Both MW-family DRAFT profiles are still missing a selected source candidate for this required field."
                shared_missing_required_fields.append(field_name)
            else:
                status = "BOTH_MISSING_OPTIONAL"
                reason = "Neither profile currently selects a source candidate for this non-required field."
        elif left_selected is None or right_selected is None:
            status = "ONE_SIDE_MISSING"
            reason = "One profile has a selected source candidate while the other still lacks one."
        else:
            left_fp = left_selected.get("fingerprint", {})
            right_fp = right_selected.get("fingerprint", {})
            left_sig = tuple(str(left_fp.get(key, "")) for key in ("field_code", "wbs_stage", "task_name", "display_header"))
            right_sig = tuple(str(right_fp.get(key, "")) for key in ("field_code", "wbs_stage", "task_name", "display_header"))
            if left_sig == right_sig:
                status = "MATCHING_SELECTED_SOURCE"
                reason = "Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field."
            else:
                status = "DIFFERENT_SELECTED_SOURCE"
                reason = "The two MW profiles currently select different source columns for the same canonical field."

        field_differences[field_name] = {
            "comparison_status": status,
            "left_display_header": _display_header(left_selected),
            "right_display_header": _display_header(right_selected),
            "review_reason": reason,
        }

    return {
        "left_profile_id": left["profile_id"],
        "right_profile_id": right["profile_id"],
        "left_profile_version": left["profile_version"],
        "right_profile_version": right["profile_version"],
        "left_mapping_version": left["mapping_version"],
        "right_mapping_version": right["mapping_version"],
        "left_observed_header_hash": left.get("export_structure", {}).get("observed_header_hash", ""),
        "right_observed_header_hash": right.get("export_structure", {}).get("observed_header_hash", ""),
        "left_du_model_name": left["identity"]["accepted_du_models"][0],
        "right_du_model_name": right["identity"]["accepted_du_models"][0],
        "summary": {
            "shared_missing_required_fields": sorted(shared_missing_required_fields),
        },
        "field_differences": field_differences,
        "notes": [
            "This MW pair review is discovery-only and does not approve profile reuse.",
            "Matching selected sources still require header-hash approval, four-layer verification, and business validation.",
        ],
    }


def build_pair_registry(left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_mw_pair_divergence_review",
        "pair_reviews": [build_pair_review(left, right)],
    }


def pair_review_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW Pair Divergence Review",
        "",
        "Discovery-only comparison between the MW EOS Swap and ZTE TX MINI DRAFT profiles. This is review guidance, not approval for shared production mappings.",
    ]
    for review in registry.get("pair_reviews", []):
        lines.extend(
            [
                "",
                f"## {review['left_profile_id']} vs {review['right_profile_id']}",
                "",
                f"- Left profile version: `{review.get('left_profile_version', '')}`",
                f"- Right profile version: `{review.get('right_profile_version', '')}`",
                f"- Left observed header hash: `{review.get('left_observed_header_hash', '')}`",
                f"- Right observed header hash: `{review.get('right_observed_header_hash', '')}`",
                f"- Shared missing required fields: {', '.join(review['summary']['shared_missing_required_fields']) or 'None'}",
                "",
            ]
        )
        for field_name, diff in review.get("field_differences", {}).items():
            lines.append(f"### `{field_name}`")
            lines.append("")
            lines.append(f"- Comparison status: `{diff['comparison_status']}`")
            lines.append(f"- Left selected header: `{diff['left_display_header'] or 'None'}`")
            lines.append(f"- Right selected header: `{diff['right_display_header'] or 'None'}`")
            lines.append(f"- Reason: {diff['review_reason']}")
            lines.append("")
    return "\n".join(lines) + "\n"


def write_pair_outputs(left_path: Path, right_path: Path, registry_path: Path, markdown_path: Path) -> None:
    left = _load_json(left_path)
    right = _load_json(right_path)
    registry = build_pair_registry(left, right)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(pair_review_markdown(registry), encoding="utf-8")


def main() -> int:
    write_pair_outputs(
        Path("config/du_profiles/mw_eos_swap_pr_v1.yaml"),
        Path("config/du_profiles/zte_tx_mini_pr_v1.yaml"),
        Path("config/registries/mw_du_mw_pair_divergence_review.yaml"),
        Path("docs/MW_DU_MW_Pair_Divergence_Review.md"),
    )
    print("Wrote MW pair divergence review outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
