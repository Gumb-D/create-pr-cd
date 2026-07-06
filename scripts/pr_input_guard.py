from __future__ import annotations

from typing import Any, Mapping

from canonical_site_validator import PR_INPUT_QUARANTINED, PR_INPUT_READY, apply_validation_result, validate_canonical_site_record


def block_raw_source(*_: Any, **__: Any) -> dict:
    return {"classification": PR_INPUT_QUARANTINED, "allow_output": False, "blocking_reasons": ["RAW_SOURCE_BLOCKED"]}


def _same_model(record: Mapping[str, Any], profile: Mapping[str, Any]) -> bool:
    identity = record.get("identity", {})
    allowed = profile.get("identity", {})
    for key, allowed_key in (("du_model_name", "accepted_du_models"), ("du_model_id", "accepted_du_model_ids"), ("view_id", "accepted_view_ids")):
        values = {str(value) for value in allowed.get(allowed_key, [])}
        if values and str(identity.get(key, "")) not in values:
            return False
    return True


def evaluate_record(record: Mapping[str, Any], profile: Mapping[str, Any] | None, *, scope: str, dry_run: bool = False) -> dict:
    if profile is None:
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": ["UNKNOWN_DU_PROFILE"], "warnings": []}
    elif profile.get("status") != "PRODUCTION":
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": ["DU_PROFILE_NOT_PRODUCTION"], "warnings": ["Dry-run only"] if dry_run else []}
    elif not _same_model(record, profile):
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": ["UNKNOWN_DU_MODEL_OR_VIEW"], "warnings": []}
    elif str(record.get("identity", {}).get("header_hash", "")) not in {str(value) for value in profile.get("export_structure", {}).get("approved_header_hashes", [])}:
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": ["HEADER_HASH_REVALIDATION_REQUIRED"], "warnings": ["Dry-run only"] if dry_run else []}
    else:
        evidence = record.get("source_evidence", {}).get("fields", {})
        unsafe = []
        if isinstance(evidence, Mapping):
            for field, item in evidence.items():
                if isinstance(item, Mapping) and item.get("mapping_status") == "UNVERIFIED":
                    unsafe.append(f"UNVERIFIED_SOURCE_MAPPING:{field}")
                if isinstance(item, Mapping) and item.get("normalization_status") == "UNVERIFIED":
                    unsafe.append(f"UNVERIFIED_NORMALIZATION:{field}")
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": unsafe, "warnings": []} if unsafe else validate_canonical_site_record(record, scope)
    updated = apply_validation_result(record, result)
    return {"record": updated, "classification": result["classification"], "allow_output": result["classification"] == PR_INPUT_READY and profile is not None and profile.get("status") == "PRODUCTION", "blocking_reasons": list(result.get("blocking_reasons", [])), "warnings": list(result.get("warnings", []))}
