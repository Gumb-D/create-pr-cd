from __future__ import annotations

from typing import Any, Dict, Mapping

from canonical_site_validator import PR_INPUT_QUARANTINED, PR_INPUT_READY, apply_validation_result, validate_canonical_site_record


def raw_source_block() -> Dict[str, Any]:
    return {
        "classification": PR_INPUT_QUARANTINED,
        "allow_generation": False,
        "blocking_reasons": ["RAW_SOURCE_DIRECT_GENERATION_PROHIBITED"],
    }


def gate_canonical_site_record(record: Mapping[str, Any], profile: Mapping[str, Any] | None, *, scope: str) -> Dict[str, Any]:
    if profile is None or profile.get("status") != "PRODUCTION":
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": ["DU_PROFILE_NOT_PRODUCTION"], "warnings": []}
    else:
        result = validate_canonical_site_record(record, scope)
    updated = apply_validation_result(record, result)
    return {
        "record": updated,
        "classification": result["classification"],
        "allow_generation": result["classification"] == PR_INPUT_READY,
        "blocking_reasons": list(result.get("blocking_reasons", [])),
        "warnings": list(result.get("warnings", [])),
    }
