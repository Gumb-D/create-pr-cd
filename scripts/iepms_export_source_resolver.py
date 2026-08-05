#!/usr/bin/env python3
"""Resolve iEPMS export sources and DU profile routes by Project + DU Model."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


IEPMS_FILENAME_PATTERN = re.compile(
    r"^A-(?P<project_code>[^-]+)-(?P<body>.+)-(?P<timestamp>\d{14})\.xlsx$",
    re.IGNORECASE,
)
LATEST_FILENAME_TIMESTAMP = "LATEST_FILENAME_TIMESTAMP"


class SourceResolutionError(ValueError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _normalize(value: object) -> str:
    return " ".join(str(value or "").split()).casefold()


def load_identity_registry(path: Path) -> dict[str, Any]:
    candidate = Path(path)
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SourceResolutionError(
            "DU_PROFILE_REGISTRY_INVALID",
            f"DU Profile identity registry is invalid: {candidate}",
            {"path": str(candidate), "error": str(error)},
        ) from error
    if not isinstance(payload, dict):
        raise SourceResolutionError(
            "DU_PROFILE_REGISTRY_INVALID",
            "DU Profile identity registry must contain a JSON object.",
            {"path": str(candidate)},
        )
    return payload


def _registered_projects(registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    projects = registry.get("projects", [])
    if not isinstance(projects, list):
        raise SourceResolutionError(
            "DU_PROFILE_REGISTRY_INVALID",
            "registry.projects must be a list.",
        )
    result: list[dict[str, Any]] = []
    seen_codes: dict[str, str] = {}
    for raw in projects:
        if not isinstance(raw, dict):
            raise SourceResolutionError(
                "DU_PROFILE_REGISTRY_INVALID",
                "Every registry project must be an object.",
            )
        project_key = str(raw.get("project_key", "")).strip()
        project_name = str(raw.get("project_name", "")).strip()
        codes = raw.get("iepms_project_codes", [])
        if not project_key or not project_name or not isinstance(codes, list) or not codes:
            raise SourceResolutionError(
                "DU_PROFILE_REGISTRY_INVALID",
                "Every registry project requires project_key, project_name, and iepms_project_codes.",
                {"project": raw},
            )
        normalized_codes: list[str] = []
        for value in codes:
            code = str(value).strip()
            if not code:
                raise SourceResolutionError(
                    "DU_PROFILE_REGISTRY_INVALID",
                    "iEPMS project codes must not be blank.",
                    {"project_key": project_key},
                )
            key = code.casefold()
            previous = seen_codes.get(key)
            if previous and previous != project_key:
                raise SourceResolutionError(
                    "DU_PROFILE_REGISTRY_INVALID",
                    "An iEPMS Project Code cannot map to multiple Project Keys.",
                    {"project_code": code, "project_keys": sorted({previous, project_key})},
                )
            seen_codes[key] = project_key
            normalized_codes.append(code)
        result.append(
            {
                "project_key": project_key,
                "project_name": project_name,
                "iepms_project_codes": normalized_codes,
            }
        )
    return result


def resolve_profile_route(
    registry: Mapping[str, Any],
    *,
    project_key: str,
    du_model_name: str,
) -> dict[str, Any]:
    profiles = registry.get("profiles", [])
    if not isinstance(profiles, list):
        raise SourceResolutionError(
            "DU_PROFILE_REGISTRY_INVALID",
            "registry.profiles must be a list.",
        )
    normalized_project = _normalize(project_key)
    normalized_model = _normalize(du_model_name)
    matches = [
        dict(entry)
        for entry in profiles
        if isinstance(entry, dict)
        and _normalize(entry.get("project_key")) == normalized_project
        and _normalize(entry.get("du_model_name")) == normalized_model
    ]
    if not matches:
        raise SourceResolutionError(
            "DU_PROFILE_NOT_FOUND",
            f"No DU Profile is registered for Project {project_key} and DU Model {du_model_name}.",
            {"project_key": project_key, "du_model_name": du_model_name},
        )
    if len(matches) != 1:
        raise SourceResolutionError(
            "DU_PROFILE_IDENTITY_AMBIGUOUS",
            "More than one DU Profile is registered for the same Project + DU Model identity.",
            {
                "project_key": project_key,
                "du_model_name": du_model_name,
                "profile_ids": sorted(str(entry.get("profile_id", "")) for entry in matches),
            },
        )
    return matches[0]


def parse_iepms_export_filename(
    path: Path,
    registry: Mapping[str, Any],
) -> dict[str, str]:
    candidate = Path(path)
    match = IEPMS_FILENAME_PATTERN.match(candidate.name)
    if not match:
        raise SourceResolutionError(
            "IEPMS_FILENAME_INVALID",
            f"The file name is not a supported iEPMS export name: {candidate.name}",
            {"source_path": str(candidate)},
        )

    project_code = match.group("project_code")
    project = next(
        (
            item
            for item in _registered_projects(registry)
            if project_code.casefold()
            in {value.casefold() for value in item["iepms_project_codes"]}
        ),
        None,
    )
    if project is None:
        raise SourceResolutionError(
            "PROJECT_CODE_UNREGISTERED",
            f"The iEPMS Project Code is not registered: {project_code}",
            {"project_code": project_code, "source_path": str(candidate)},
        )

    body = match.group("body")
    model_names = sorted(
        {
            str(entry.get("du_model_name", "")).strip()
            for entry in registry.get("profiles", [])
            if isinstance(entry, dict)
            and _normalize(entry.get("project_key")) == _normalize(project["project_key"])
            and str(entry.get("du_model_name", "")).strip()
        },
        key=len,
        reverse=True,
    )
    du_model_name = next(
        (
            model
            for model in model_names
            if body.casefold().startswith(f"{model}-".casefold())
        ),
        None,
    )
    if du_model_name is None:
        raise SourceResolutionError(
            "DU_MODEL_UNREGISTERED",
            "The iEPMS export DU Model is not registered for the detected Project.",
            {
                "project_code": project_code,
                "project_key": project["project_key"],
                "source_path": str(candidate),
                "registered_du_models": model_names,
            },
        )
    view_name = body[len(du_model_name) + 1 :].strip()
    if not view_name:
        raise SourceResolutionError(
            "IEPMS_FILENAME_INVALID",
            "The iEPMS export filename does not contain a View Name.",
            {"source_path": str(candidate)},
        )

    return {
        "project_code": project_code,
        "project_key": str(project["project_key"]),
        "project_name": str(project["project_name"]),
        "du_model_name": du_model_name,
        "view_name": view_name,
        "export_timestamp": match.group("timestamp"),
        "source_path": str(candidate.resolve()),
    }


def discover_latest_source_exports(
    source_roots: Iterable[Path],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    roots = [Path(root).expanduser().resolve() for root in source_roots]
    for root in roots:
        if not root.is_dir():
            errors.append(
                {
                    "code": "SOURCE_ROOT_NOT_FOUND",
                    "message": f"Source root is not available: {root}",
                    "source_root": str(root),
                }
            )
            continue
        for source in sorted(root.rglob("*.xlsx"), key=lambda value: str(value).casefold()):
            if not source.name.casefold().startswith("a-"):
                continue
            try:
                identity = parse_iepms_export_filename(source, registry)
                route = resolve_profile_route(
                    registry,
                    project_key=identity["project_key"],
                    du_model_name=identity["du_model_name"],
                )
            except SourceResolutionError as error:
                error_row = {
                    "code": error.code,
                    "message": str(error),
                    "source_path": str(source.resolve()),
                    **error.details,
                }
                errors.append(error_row)
                rows.append({"status": "ERROR", **error_row})
                continue
            candidate = {
                **identity,
                "profile_id": str(route.get("profile_id", "")),
                "profile_status": str(route.get("profile_status", "")),
            }
            grouped[candidate["profile_id"]].append(candidate)

    selections: dict[str, dict[str, Any]] = {}
    for profile_id, candidates in sorted(grouped.items()):
        ordered = sorted(
            candidates,
            key=lambda item: (item["export_timestamp"], item["source_path"]),
            reverse=True,
        )
        latest_timestamp = ordered[0]["export_timestamp"]
        latest = [item for item in ordered if item["export_timestamp"] == latest_timestamp]
        if len(latest) != 1:
            error = {
                "code": "SOURCE_EXPORT_TIMESTAMP_AMBIGUOUS",
                "message": "More than one export has the latest filename timestamp.",
                "profile_id": profile_id,
                "export_timestamp": latest_timestamp,
                "source_paths": sorted(item["source_path"] for item in latest),
            }
            errors.append(error)
            rows.append({"status": "ERROR", **error})
            for item in ordered:
                rows.append({"status": "NOT_SELECTED_AMBIGUOUS", **item})
            continue

        selected = dict(latest[0])
        selected.update(
            {
                "candidate_count": len(ordered),
                "selection_policy": LATEST_FILENAME_TIMESTAMP,
            }
        )
        selections[profile_id] = selected
        for item in ordered:
            rows.append(
                {
                    "status": "SELECTED" if item["source_path"] == selected["source_path"] else "IGNORED_OLDER",
                    **item,
                }
            )

    return {
        "selection_policy": LATEST_FILENAME_TIMESTAMP,
        "source_roots": [str(root) for root in roots],
        "selections": selections,
        "errors": sorted(errors, key=lambda row: (str(row.get("profile_id", "")), str(row.get("code", "")), str(row.get("source_path", "")))),
        "rows": sorted(rows, key=lambda row: (str(row.get("profile_id", "")), str(row.get("export_timestamp", "")), str(row.get("source_path", "")))),
    }
