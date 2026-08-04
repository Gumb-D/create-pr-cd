"""Build a discovery-only DU model registry from profiler outputs.

This script turns read-only profiler artifacts into repo-tracked inventory
metadata. It does not approve profiles, mappings, or header hashes for
production use.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


SITE_CODE_PATTERN = re.compile(r"^site\|fix00012\|(?P<du_model_id>\d+)\|(?P<view_id>\d+)$")
FILENAME_PATTERN = re.compile(
    r"^(?P<project_ref>A-[^-]+)-(?P<du_model_name>[^-]+)-(?P<view_label>.+)-(?P<timestamp>\d{14})\.xlsx$"
)


@dataclass(frozen=True)
class ParsedSourceName:
    project_ref: str
    du_model_name: str
    view_label: str
    timestamp: str


def parse_source_filename(file_name: str) -> ParsedSourceName:
    match = FILENAME_PATTERN.match(file_name)
    if not match:
        raise ValueError(f"Unsupported DU export file name format: {file_name}")
    return ParsedSourceName(
        project_ref=match.group("project_ref"),
        du_model_name=match.group("du_model_name"),
        view_label=match.group("view_label"),
        timestamp=match.group("timestamp"),
    )


def infer_project_key(du_model_name: str) -> str:
    if du_model_name in {"MW EOS Swap", "ZTE TX MINI"}:
        return "CelcomDigi_MW"
    return "Malaysia_CelcomDigi_Project"


def extract_du_identity(header_inventory: Mapping[str, Any]) -> Dict[str, str]:
    for sheet in header_inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            fingerprint = column.get("fingerprint", {})
            field_code = str(fingerprint.get("field_code", ""))
            match = SITE_CODE_PATTERN.match(field_code)
            if match:
                return {
                    "du_model_id": match.group("du_model_id"),
                    "view_id": match.group("view_id"),
                }
    raise ValueError("Could not extract DU model/view identity from site code fingerprint.")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_profiler_root() -> Path:
    for candidate in (Path("output/du-20260706-profile"), Path("Info/reference/du-20260706-profile")):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No DU profiler artifact root found under output/ or Info/reference/.")


@lru_cache(maxsize=1)
def _known_profiles() -> Dict[tuple[str, str, str], Dict[str, str]]:
    profile_dir = Path(__file__).resolve().parent.parent / "config" / "du_profiles"
    profiles: Dict[tuple[str, str, str], Dict[str, str]] = {}
    if not profile_dir.exists():
        return profiles
    for path in profile_dir.glob("*.yaml"):
        profile = _load_json(path)
        identity = profile.get("identity", {})
        for du_model_name in identity.get("accepted_du_models", []):
            for du_model_id in identity.get("accepted_du_model_ids", []):
                for view_id in identity.get("accepted_view_ids", []):
                    profiles[(str(du_model_name), str(du_model_id), str(view_id))] = {
                        "profile_id": str(profile.get("profile_id", "")),
                        "profile_status": str(profile.get("status", "")),
                        "profile_version": str(profile.get("profile_version", "")),
                        "mapping_version": str(profile.get("mapping_version", "")),
                    }
    return profiles


def _skill_field_presence(header_inventory: Mapping[str, Any]) -> Dict[str, bool]:
    targets = {
        "site_id": ("customer site code",),
        "site_name": ("customer site name",),
        "du_code": ("du code",),
        "region": ("region",),
        "tx_sow": ("tx sow",),
        "tx_before_migration": ("tx before migration",),
        "final_backhaul": ("final backhaul",),
        "antenna_size_ne": ("antenna size ne",),
        "antenna_size_fe": ("antenna size fe",),
        "subcon_tss_team": ("subcon - tss",),
        "subcon_ti_team": ("subcon - ti",),
        "subcon_planning": ("subcon - planning", "subcon planning"),
        "existing_tss_pr": ("pr tss status",),
        "existing_ti_pr": ("pr ti status",),
    }
    direct_pr_display_headers = {
        "existing_tss_pr": {
            "pr tss status",
            "subcon pr - tss",
        },
        "existing_ti_pr": {
            "pr ti status",
            "subcon pr - ti",
        },
    }
    texts: List[str] = []
    display_headers: List[str] = []
    for sheet in header_inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            fp = column.get("fingerprint", {})
            texts.append(
                " | ".join(
                    str(fp.get(key, ""))
                    for key in ("field_code", "wbs_stage", "task_name", "display_header")
                ).lower()
            )
            display_headers.append(str(fp.get("display_header", "")).strip().lower())
    result: Dict[str, bool] = {}
    for field, options in targets.items():
        if field in direct_pr_display_headers:
            result[field] = any(display in direct_pr_display_headers[field] for display in display_headers)
            continue
        result[field] = any(any(option in text for option in options) for text in texts)
    return result


def build_discovery_entry(profile_dir: Path) -> Dict[str, Any]:
    inventory = _load_json(profile_dir / "header_inventory.json")
    parsed_name = parse_source_filename(str(inventory["source"]["file_name"]))
    identity = extract_du_identity(inventory)
    header_hash = (profile_dir / "header_hash.txt").read_text(encoding="utf-8").strip()
    field_presence = _skill_field_presence(inventory)
    known_profile = _known_profiles().get((parsed_name.du_model_name, identity["du_model_id"], identity["view_id"]))
    profile_id = known_profile["profile_id"] if known_profile else None
    profile_status = known_profile["profile_status"] if known_profile else None
    profile_version = known_profile["profile_version"] if known_profile else None
    mapping_version = known_profile["mapping_version"] if known_profile else None
    return {
        "project_key": infer_project_key(parsed_name.du_model_name),
        "project_reference": parsed_name.project_ref,
        "du_model_name": parsed_name.du_model_name,
        "du_model_id": identity["du_model_id"],
        "view_label": parsed_name.view_label,
        "view_id": identity["view_id"],
        "source_file_name": inventory["source"]["file_name"],
        "source_file_hash": inventory["source"]["source_file_hash"],
        "observed_header_hash": header_hash,
        "sheet_names": [sheet.get("sheet_name", "") for sheet in inventory.get("sheets", [])],
        "profile_id": profile_id,
        "profile_status": profile_status,
        "profile_version": profile_version,
        "mapping_version": mapping_version,
        "pr_input_status": "PR_INPUT_QUARANTINED",
        "discovery_status": "KEYWORD_DISCOVERY_REVIEWED",
        "skill_field_presence": field_presence,
        "notes": [
            "Discovery-only metadata derived from local profiler artifacts.",
            "No header hash, field mapping, or profile in this entry is approved for production use.",
        ],
    }


def build_discovery_registry(profile_root: Path) -> Dict[str, Any]:
    entries = [
        build_discovery_entry(path)
        for path in sorted(profile_root.iterdir())
        # Only profiler artifact directories qualify; review packages and other
        # local working folders under the same root are not DU export profiles.
        if path.is_dir() and (path / "header_inventory.json").exists()
    ]
    return {
        "schema_version": "1.0",
        "registry_type": "discovery_only",
        "generated_from": str(profile_root),
        "entries": entries,
    }


def write_registry_outputs(profile_root: Path, registry_path: Path, markdown_path: Path) -> None:
    registry = build_discovery_registry(profile_root)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(discovery_inventory_markdown(registry), encoding="utf-8")


def discovery_inventory_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# MW DU Discovery Inventory",
        "",
        "This inventory is discovery-only metadata derived from profiler artifacts. It does not approve any DU profile, field mapping, or header hash for production use.",
        "",
        "| Project Key | DU Model | DU Model ID | View Label | View ID | Header Hash | Profile ID | PR Input Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for entry in registry.get("entries", []):
        lines.append(
            "| {project_key} | {du_model_name} | `{du_model_id}` | {view_label} | `{view_id}` | `{observed_header_hash}` | {profile_id} | {pr_input_status} |".format(
                project_key=entry["project_key"],
                du_model_name=entry["du_model_name"],
                du_model_id=entry["du_model_id"],
                view_label=entry["view_label"],
                view_id=entry["view_id"],
                observed_header_hash=entry["observed_header_hash"],
                profile_id=entry["profile_id"] or "`None`",
                pr_input_status=entry["pr_input_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `PR_INPUT_QUARANTINED` here means discovery-only; it is not a production approval state.",
            "- `Profile ID` is populated only where the repository already contains a corresponding profile file.",
            "- The observed header hashes came from local profiler runs against external source files and remain subject to sanitization and business approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    profile_root = find_profiler_root()
    registry_path = Path("config/registries/mw_du_model_discovery_registry.yaml")
    markdown_path = Path("docs/MW_DU_Discovery_Inventory.md")
    write_registry_outputs(profile_root, registry_path, markdown_path)
    print(f"Wrote discovery registry: {registry_path}")
    print(f"Wrote discovery inventory: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
