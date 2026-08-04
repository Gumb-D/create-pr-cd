"""Build discovery-only skill-field mapping shortlists from profiler outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


SKILL_FIELDS = (
    "site_id",
    "site_name",
    "du_code",
    "region",
    "tx_sow",
    "tx_before_migration",
    "final_backhaul",
    "antenna_size_ne",
    "antenna_size_fe",
    "subcon_tss_team",
    "subcon_ti_team",
    "subcon_planning",
    "tx_integrated_actual_end_date",
    "existing_tss_pr",
    "existing_ti_pr",
)


def _text_for_column(column: Mapping[str, Any]) -> str:
    fp = column.get("fingerprint", {})
    return " | ".join(str(fp.get(key, "")) for key in ("field_code", "wbs_stage", "task_name", "display_header")).lower()


def _reason_and_score(field: str, column: Mapping[str, Any]) -> tuple[int, str] | None:
    fp = column.get("fingerprint", {})
    display = str(fp.get("display_header", "")).strip().lower()
    wbs_stage = str(fp.get("wbs_stage", "")).strip().lower()
    task_name = str(fp.get("task_name", "")).strip().lower()
    text = _text_for_column(column)

    if field == "site_id":
        if display == "customer site code":
            return 100, "Exact skill field match for Site ID."
        if "site id" in display:
            return 70, "Alternate site ID style field."
    elif field == "site_name":
        if display == "customer site name":
            return 100, "Exact skill field match for Site Name."
        if "site name" in display:
            return 70, "Alternate site-name style field."
    elif field == "du_code":
        if display == "du code":
            return 100, "Exact skill field match for DU Code."
        if "du code" in text:
            return 70, "DU code phrase present in fingerprint."
    elif field == "region":
        if display == "region" and wbs_stage == "site basic info":
            return 100, "Direct Site Basic Info region field."
        if display == "region":
            return 70, "Region label present but not in the strongest section."
        if "sub region" in display:
            return 40, "Sub-region field; likely secondary."
    elif field == "tx_sow":
        if display == "tx sow":
            return 100, "Direct Tx SOW field."
        if "microwave tx sow" in display:
            return 85, "Direct Microwave Tx SOW variant."
        if "tx sow (lld)" in display or "plan tx sow" in display:
            return 80, "Likely direct SOW planning field."
        if "tx sow details" in display:
            return 45, "SOW details field; likely evidence, not primary trigger."
    elif field == "tx_before_migration":
        if display == "tx before migration":
            return 100, "Exact Jendela migration-source field."
    elif field == "final_backhaul":
        if display == "final backhaul":
            return 100, "Exact Jendela migration-destination field."
    elif field == "antenna_size_ne":
        if "antenna size ne" in display:
            return 100, "Direct NE antenna size field."
    elif field == "antenna_size_fe":
        if "antenna size fe" in display:
            return 100, "Direct FE antenna size field."
    elif field == "subcon_tss_team":
        if display == "subcon - tss team":
            return 100, "Exact TSS team field."
        if display == "subcon - tss":
            return 85, "Direct TSS subcontractor field."
    elif field == "subcon_ti_team":
        if display == "subcon - ti team":
            return 100, "Exact TI team field."
        if display == "subcon - ti":
            return 85, "Direct TI subcontractor field."
    elif field == "subcon_planning":
        if display == "subcon - planning":
            return 100, "Exact Planning subcontractor field."
        if display == "subcon planning":
            return 85, "Direct Planning subcontractor variant."
        if display in {"subcon pr - planning", "subcon - pr planning"}:
            return 55, "PR-oriented Planning field."
    elif field == "tx_integrated_actual_end_date":
        if "tx integrated actual end date" in display:
            return 100, "Exact Operation Backoffice trigger field."
        if "integrated actual end date" in display:
            return 70, "Likely Operation Backoffice trigger variant."
    elif field == "existing_tss_pr":
        if display == "pr tss status":
            return 100, "Exact TSS PR status field."
        if display == "subcon pr - tss":
            return 100, "Direct TSS PR reference/status field."
        if display == "pr tss rectification status":
            return 65, "TSS rectification status field."
        if "tss pr" in text or "pr tss" in text:
            return 35, "Weak TSS PR phrase match."
    elif field == "existing_ti_pr":
        if display == "pr ti status":
            return 100, "Exact TI PR status field."
        if display == "subcon pr - ti":
            return 100, "Direct TI PR reference/status field."
        if display == "pr ti rectification status":
            return 65, "TI rectification status field."
        if "ti pr" in text or "pr ti" in text:
            return 35, "Weak TI PR phrase match."

    return None


def shortlist_skill_fields(header_inventory: Mapping[str, Any], *, top_n: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    columns: List[Mapping[str, Any]] = []
    for sheet in header_inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            columns.append(column)

    shortlists: Dict[str, List[Dict[str, Any]]] = {}
    for field in SKILL_FIELDS:
        candidates: List[Dict[str, Any]] = []
        for column in columns:
            scored = _reason_and_score(field, column)
            if scored is None:
                continue
            score, reason = scored
            candidates.append(
                {
                    "score": score,
                    "reason": reason,
                    "fingerprint": column["fingerprint"],
                    "source_position": column["source_position"],
                }
            )
        candidates.sort(
            key=lambda item: (
                -int(item["score"]),
                item["fingerprint"]["display_header"],
                item["source_position"]["one_based_index"],
            )
        )
        shortlists[field] = candidates[:top_n]
    return shortlists


def build_profile_shortlist(profile_dir: Path) -> Dict[str, Any]:
    inventory = json.loads((profile_dir / "header_inventory.json").read_text(encoding="utf-8"))
    observed_header_hash = (profile_dir / "header_hash.txt").read_text(encoding="utf-8").strip()
    return {
        "source_file_name": inventory["source"]["file_name"],
        "observed_header_hash": observed_header_hash,
        "skill_field_shortlists": shortlist_skill_fields(inventory),
    }


def build_shortlist_registry(profile_dirs: Iterable[Path]) -> Dict[str, Any]:
    entries = [build_profile_shortlist(path) for path in profile_dirs]
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_skill_field_shortlists",
        "entries": entries,
    }


def write_shortlist_outputs(profile_dirs: Iterable[Path], json_path: Path, markdown_path: Path) -> None:
    registry = build_shortlist_registry(profile_dirs)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(shortlist_markdown(registry), encoding="utf-8")


def shortlist_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# Priority DU Skill-Field Shortlists",
        "",
        "Discovery-only shortlist of exact four-layer fingerprints for skill-scoped fields. These are review aids, not approved mappings.",
    ]
    for entry in registry.get("entries", []):
        lines.extend(["", f"## {entry['source_file_name']}", ""])
        for field in SKILL_FIELDS:
            candidates = entry.get("skill_field_shortlists", {}).get(field, [])
            if not candidates:
                lines.append(f"- `{field}`: no shortlist candidate")
                continue
            lines.append(f"- `{field}`:")
            for candidate in candidates:
                fp = candidate["fingerprint"]
                lines.append(
                    "  - score {score}: {field_code} | {wbs_stage} | {task_name} | {display_header}".format(
                        score=candidate["score"],
                        field_code=fp["field_code"],
                        wbs_stage=fp["wbs_stage"],
                        task_name=fp["task_name"],
                        display_header=fp["display_header"],
                    )
                )
                lines.append(f"    reason: {candidate['reason']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = Path("output/du-20260706-profile")
    priority_names = [
        "A-P202202168750_D002-TX_Mini_Project-TX_Mini_PR_PO_View-20260703160246",
        "A-P202211283695_D002-MW_EOS_Swap-MW_EOS_Swap_Rollout-20260703160307",
        "A-P202202168750_D002-2023_TX_Rollout-TX_Rollout_PR_PO_View-20260703160446",
        "A-P202202168750_D002-Jendela_TX_Migration-Migration_Rollout_TX_-20260703160246",
        "A-P202211283695_D002-ZTE_TX_MINI-ZTE_TX_MINI_v1-20260703160312",
        "A-P202202168750_D002-2023_Celcomdigi_BAU-2023_Celcomdigi_BAU__TX_-20260703160239",
        "A-P202202168750_D002-2024_Celcomdigi_BAU-2024_BAU_Rollout_TX_-20260703160253",
        "A-P202202168750_D002-Celcomdigi_USP-Celcomdigi_USP_TX_-20260703160234",
        "A-P202202168750_D002-CD_consolidation_2023-CD_2023_Decom_Site-20260703160415",
        "A-P202202168750_D002-CD_consolidation_2023-CD_consolidation_2023_Rollout-20260703160351",
    ]
    profile_dirs = [root / name for name in priority_names]
    write_shortlist_outputs(
        profile_dirs,
        Path("config/registries/mw_du_priority_skill_field_shortlists.yaml"),
        Path("docs/MW_DU_Priority_Skill_Field_Shortlists.md"),
    )
    print("Wrote priority skill-field shortlists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
