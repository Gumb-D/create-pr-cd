#!/usr/bin/env python3
"""Read-only profiler for original four-header iEPMS exports.

This module deliberately has no dependency on the ECC generator. It inventories
source headers, calculates a deterministic export header hash, and produces only
UNVERIFIED mapping suggestions. It never generates PR or ECC output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

HEADER_ROW_COUNT = 4
SCHEMA_VERSION = "1.0"

# This is discovery-only matching. Suggested candidates are always marked
# UNVERIFIED and must not be consumed by a production DU profile.
CANONICAL_FIELD_KEYWORDS: Dict[str, Sequence[Sequence[str]]] = {
    "site_code": (("customer", "site", "code"), ("site", "code"), ("site", "id")),
    "site_name": (("customer", "site", "name"), ("site", "name")),
    "du_key": (("du", "code"), ("du", "key")),
    "tx_sow_raw": (("tx", "sow"), ("scope", "of", "work")),
    "tx_upgrade_scope_raw": (("tx", "upgrade", "scope"),),
    "region": (("region",),),
    "state": (("province", "state"), ("state",)),
    "subcontractor_ti": (("subcon", "ti"), ("subcontractor", "ti")),
    "subcontractor_planning": (("subcon", "planning"), ("subcontractor", "planning")),
    "existing_tss_pr_status": (("tss", "pr"),),
    "existing_ti_pr_status": (("ti", "pr"),),
    "latitude": (("latitude",),),
    "longitude": (("longitude",),),
    "antenna_size_ne": (("antenna", "size", "ne"),),
    "antenna_size_fe": (("antenna", "size", "fe"),),
    "boq_configuration": (("boq", "configuration"),),
    "tx_sow_details": (("tx", "sow", "details"),),
    "ne_sow_details": (("ne", "sow", "details"),),
    "fe_sow_details": (("fe", "sow", "details"),),
}

# Required in every future production profile. Conditional technical fields are
# evaluated only after the selected shared PR rule indicates that they are needed.
PR_CRITICAL_FIELDS = (
    "site_code",
    "tx_sow_raw",
    "region",
    "subcontractor_ti",
    "existing_tss_pr_status",
    "existing_ti_pr_status",
)


def normalize_header_value(value: Any) -> str:
    """Normalize only for deterministic comparison; retain raw values separately."""
    if value is None:
        return ""
    return " ".join(str(value).replace("\u00a0", " ").split())


def make_header_fingerprint(header_values: Sequence[Any]) -> Dict[str, str]:
    if len(header_values) != HEADER_ROW_COUNT:
        raise ValueError(f"A header fingerprint requires {HEADER_ROW_COUNT} values.")
    normalized = [normalize_header_value(value) for value in header_values]
    return {
        "field_code": normalized[0],
        "wbs_stage": normalized[1],
        "task_name": normalized[2],
        "display_header": normalized[3],
    }


def fingerprint_key(fingerprint: Mapping[str, Any]) -> str:
    """Stable textual identity used only for comparison/provenance, never index lookup."""
    required = ("field_code", "wbs_stage", "task_name", "display_header")
    canonical = {key: normalize_header_value(fingerprint.get(key, "")) for key in required}
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _columns_from_header_rows(sheet_name: str, header_rows: Sequence[Sequence[Any]]) -> List[Dict[str, Any]]:
    max_columns = max((len(row) for row in header_rows), default=0)
    columns: List[Dict[str, Any]] = []
    for index in range(max_columns):
        raw_values = [row[index] if index < len(row) else None for row in header_rows]
        if not any(normalize_header_value(value) for value in raw_values):
            continue
        fingerprint = make_header_fingerprint(raw_values)
        columns.append(
            {
                "source_position": {"excel_column": get_column_letter(index + 1), "one_based_index": index + 1},
                "raw_header_values": [_safe_json_value(value) for value in raw_values],
                "normalized_header_values": [normalize_header_value(value) for value in raw_values],
                "fingerprint": fingerprint,
                "fingerprint_key": fingerprint_key(fingerprint),
            }
        )
    return columns


def _read_xlsx_inventory(path: Path) -> List[Dict[str, Any]]:
    workbook = load_workbook(path, read_only=True, data_only=False)
    sheets: List[Dict[str, Any]] = []
    for worksheet in workbook.worksheets:
        rows = []
        for row in worksheet.iter_rows(min_row=1, max_row=HEADER_ROW_COUNT, values_only=True):
            rows.append(list(row))
        while len(rows) < HEADER_ROW_COUNT:
            rows.append([])
        sheets.append(
            {
                "sheet_name": worksheet.title,
                "header_row_count": HEADER_ROW_COUNT,
                "columns": _columns_from_header_rows(worksheet.title, rows),
            }
        )
    workbook.close()
    return sheets


def _read_csv_inventory(path: Path) -> List[Dict[str, Any]]:
    try:
        text_handle = path.open("r", encoding="utf-8-sig", newline="")
        rows = []
        with text_handle as handle:
            reader = csv.reader(handle)
            for _ in range(HEADER_ROW_COUNT):
                try:
                    rows.append(next(reader))
                except StopIteration:
                    break
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as handle:
            reader = csv.reader(handle)
            rows = []
            for _ in range(HEADER_ROW_COUNT):
                try:
                    rows.append(next(reader))
                except StopIteration:
                    break
    while len(rows) < HEADER_ROW_COUNT:
        rows.append([])
    return [
        {
            "sheet_name": "CSV",
            "header_row_count": HEADER_ROW_COUNT,
            "columns": _columns_from_header_rows("CSV", rows),
        }
    ]


def build_header_inventory(input_path: Path) -> Dict[str, Any]:
    """Read candidate sheets and preserve the first four header rows in the inventory."""
    input_path = Path(input_path)
    suffix = input_path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        sheets = _read_xlsx_inventory(input_path)
    elif suffix == ".csv":
        sheets = _read_csv_inventory(input_path)
    else:
        raise ValueError("Only .xlsx, .xlsm, and .csv exports are supported by the profiler.")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "file_name": input_path.name,
            "source_file_hash": sha256_file(input_path),
            "format": suffix.lstrip("."),
            "header_row_count": HEADER_ROW_COUNT,
        },
        "sheets": sheets,
    }


def calculate_header_hash(inventory: Mapping[str, Any]) -> str:
    """Hash the complete normalized four-layer inventory in source sheet/column order."""
    hash_payload = {
        "schema_version": inventory.get("schema_version", SCHEMA_VERSION),
        "header_row_count": HEADER_ROW_COUNT,
        "sheets": [
            {
                "sheet_name": sheet["sheet_name"],
                "columns": [column["fingerprint"] for column in sheet.get("columns", [])],
            }
            for sheet in inventory.get("sheets", [])
        ],
    }
    canonical = json.dumps(hash_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _header_search_text(column: Mapping[str, Any]) -> str:
    return " ".join(column.get("normalized_header_values", [])).lower()


def _candidate_matches(text: str, keyword_sets: Iterable[Sequence[str]]) -> List[List[str]]:
    return [list(keywords) for keywords in keyword_sets if all(keyword in text for keyword in keywords)]


def identify_canonical_field_candidates(inventory: Mapping[str, Any]) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    for canonical_field, keyword_sets in CANONICAL_FIELD_KEYWORDS.items():
        candidates = []
        for sheet in inventory.get("sheets", []):
            for column in sheet.get("columns", []):
                matches = _candidate_matches(_header_search_text(column), keyword_sets)
                if matches:
                    candidates.append(
                        {
                            "sheet_name": sheet["sheet_name"],
                            "fingerprint": column["fingerprint"],
                            "fingerprint_key": column["fingerprint_key"],
                            "evidence": {
                                "matched_keyword_sets": matches,
                                "normalized_header_values": column["normalized_header_values"],
                            },
                            "mapping_status": "UNVERIFIED",
                        }
                    )
        if not candidates:
            status = "MISSING"
        elif len(candidates) == 1:
            status = "UNVERIFIED"
        else:
            status = "AMBIGUOUS"
        fields[canonical_field] = {"status": status, "candidates": candidates}
    return {
        "schema_version": SCHEMA_VERSION,
        "discovery_only": True,
        "fields": fields,
    }


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "unidentified_du_model"


def build_draft_du_profile(
    inventory: Mapping[str, Any],
    candidates: Mapping[str, Any],
    *,
    project_key: str | None = None,
    du_model_name: str | None = None,
    du_model_id: str | None = None,
    view_id: str | None = None,
) -> Dict[str, Any]:
    """Create a non-runnable DRAFT profile. All suggestions remain UNVERIFIED."""
    field_mapping: Dict[str, Any] = {}
    candidate_fields = candidates.get("fields", {})
    for canonical_field in CANONICAL_FIELD_KEYWORDS:
        suggested = candidate_fields.get(canonical_field, {})
        field_mapping[canonical_field] = {
            "required": canonical_field in PR_CRITICAL_FIELDS,
            "source_candidates": [
                {
                    "fingerprint": candidate["fingerprint"],
                    "mapping_status": "UNVERIFIED",
                }
                for candidate in suggested.get("candidates", [])
            ],
            "transforms": ["trim"],
        }

    profile_name = du_model_name or "unidentified_du_model"
    return {
        "profile_id": f"draft_{_slug(profile_name)}_v1",
        "profile_version": "0.1.0",
        "status": "DRAFT",
        "identity": {
            "project_key": project_key or "UNVERIFIED",
            "accepted_du_models": [du_model_name] if du_model_name else [],
            "accepted_du_model_ids": [str(du_model_id)] if du_model_id else [],
            "accepted_view_ids": [str(view_id)] if view_id else [],
        },
        "export_structure": {
            "sheet_selector": None,
            "header_rows": [0, 1, 2, 3],
            "header_hash_policy": "strict",
            "observed_header_hash": calculate_header_hash(inventory),
            "approved_header_hashes": [],
        },
        "field_mapping": field_mapping,
        "validation": {
            "reject_unknown_headers": True,
            "reject_ambiguous_source_mapping": True,
            "require_evidence_for_every_canonical_field": True,
            "profile_notes": [
                "Generated by read-only profiler.",
                "No source candidate is approved.",
                "DRAFT profiles must never be used for production ECC generation.",
            ],
        },
    }


def header_inventory_markdown(inventory: Mapping[str, Any], header_hash: str) -> str:
    lines = [
        "# iEPMS Four-Header Inventory",
        "",
        f"- Source file: `{inventory['source']['file_name']}`",
        f"- Source file SHA-256: `{inventory['source']['source_file_hash']}`",
        f"- Header hash: `{header_hash}`",
        f"- Header rows preserved: `{HEADER_ROW_COUNT}`",
        "",
        "This is a read-only profiler output. Column position is informational only; production profiles must match by four-layer fingerprint.",
    ]
    for sheet in inventory.get("sheets", []):
        lines.extend(["", f"## Sheet: {sheet['sheet_name']}", "", "| Position | Field ID / Code | WBS Stage | Task Name | Display Header |", "|---|---|---|---|---|"])
        for column in sheet.get("columns", []):
            fp = column["fingerprint"]
            lines.append(
                "| {position} | {field} | {wbs} | {task} | {display} |".format(
                    position=column["source_position"]["excel_column"],
                    field=fp["field_code"].replace("|", "\\|"),
                    wbs=fp["wbs_stage"].replace("|", "\\|"),
                    task=fp["task_name"].replace("|", "\\|"),
                    display=fp["display_header"].replace("|", "\\|"),
                )
            )
    return "\n".join(lines) + "\n"


def missing_pr_critical_fields_markdown(candidates: Mapping[str, Any]) -> str:
    lines = [
        "# PR-Critical Source Field Assessment",
        "",
        "All profiler matches are UNVERIFIED. This file is not a production approval.",
        "",
        "| Canonical field | Discovery status | Required handling |",
        "|---|---|---|",
    ]
    for field in PR_CRITICAL_FIELDS:
        status = candidates["fields"][field]["status"]
        if status == "UNVERIFIED":
            action = "Business validation required before profile promotion."
        elif status == "AMBIGUOUS":
            action = "Quarantine: select one approved four-layer fingerprint."
        else:
            action = "Incomplete: identify a source field before PR generation."
        lines.append(f"| `{field}` | `{status}` | {action} |")

    lines.extend(
        [
            "",
            "## Conditional PR fields",
            "",
            "Coordinates and antenna fields become mandatory only when the selected shared PR rule requires them. Their mappings still require profile evidence before use.",
        ]
    )
    for field in ("latitude", "longitude", "antenna_size_ne", "antenna_size_fe", "tx_upgrade_scope_raw"):
        status = candidates["fields"][field]["status"]
        lines.append(f"- `{field}`: `{status}`")
    return "\n".join(lines) + "\n"


def write_profiler_outputs(
    output_dir: Path,
    inventory: Mapping[str, Any],
    candidates: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> Dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    header_hash = calculate_header_hash(inventory)
    outputs = {
        "header_inventory_json": output_dir / "header_inventory.json",
        "header_inventory_markdown": output_dir / "header_inventory.md",
        "header_hash": output_dir / "header_hash.txt",
        "canonical_field_candidates": output_dir / "canonical_field_candidates.json",
        "missing_pr_critical_fields": output_dir / "missing_pr_critical_fields.md",
        "draft_du_profile": output_dir / "draft_du_profile.yaml",
    }
    outputs["header_inventory_json"].write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outputs["header_inventory_markdown"].write_text(header_inventory_markdown(inventory, header_hash), encoding="utf-8")
    outputs["header_hash"].write_text(header_hash + "\n", encoding="utf-8")
    outputs["canonical_field_candidates"].write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outputs["missing_pr_critical_fields"].write_text(missing_pr_critical_fields_markdown(candidates), encoding="utf-8")
    # JSON is valid YAML. Keeping the skeleton JSON-compatible avoids adding a
    # parser dependency before profile promotion requires richer YAML syntax.
    outputs["draft_du_profile"].write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return outputs


def profile_export(
    input_path: Path,
    output_dir: Path,
    *,
    project_key: str | None = None,
    du_model_name: str | None = None,
    du_model_id: str | None = None,
    view_id: str | None = None,
) -> Dict[str, Any]:
    inventory = build_header_inventory(Path(input_path))
    candidates = identify_canonical_field_candidates(inventory)
    profile = build_draft_du_profile(
        inventory,
        candidates,
        project_key=project_key,
        du_model_name=du_model_name,
        du_model_id=du_model_id,
        view_id=view_id,
    )
    outputs = write_profiler_outputs(Path(output_dir), inventory, candidates, profile)
    return {"inventory": inventory, "candidates": candidates, "profile": profile, "outputs": outputs}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only profiler for original four-header iEPMS exports.")
    parser.add_argument("--input", required=True, help="Original iEPMS .xlsx/.xlsm/.csv export")
    parser.add_argument("--output", required=True, help="Directory for profiler artifacts")
    parser.add_argument("--project-key")
    parser.add_argument("--du-model-name")
    parser.add_argument("--du-model-id")
    parser.add_argument("--view-id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = profile_export(
        Path(args.input),
        Path(args.output),
        project_key=args.project_key,
        du_model_name=args.du_model_name,
        du_model_id=args.du_model_id,
        view_id=args.view_id,
    )
    print("Profiler completed. No ECC generation was attempted.")
    print(f"Header hash: {calculate_header_hash(result['inventory'])}")
    for name, output in result["outputs"].items():
        print(f"{name}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
