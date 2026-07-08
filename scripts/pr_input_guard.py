from __future__ import annotations

from typing import Any, Mapping

from canonical_site_validator import (
    ALLOW_ECC_OUTPUT,
    PR_INPUT_QUARANTINED,
    PR_INPUT_READY,
    QUARANTINE_NO_ECC,
    apply_validation_result,
    validate_canonical_site_record,
)


def block_raw_source(*_: Any, **__: Any) -> dict:
    return {
        "classification": PR_INPUT_QUARANTINED,
        "allow_output": False,
        "blocking_reasons": ["RAW_SOURCE_BLOCKED"],
        "output_decision": QUARANTINE_NO_ECC,
    }


def _same_model(record: Mapping[str, Any], profile: Mapping[str, Any]) -> bool:
    identity = record.get("identity", {})
    allowed = profile.get("identity", {})
    for key, allowed_key in (("du_model_name", "accepted_du_models"), ("du_model_id", "accepted_du_model_ids"), ("view_id", "accepted_view_ids")):
        values = {str(value) for value in allowed.get(allowed_key, [])}
        if values and str(identity.get(key, "")) not in values:
            return False
    return True


def _output_decision(classification: str, profile: Mapping[str, Any] | None) -> str:
    if classification == PR_INPUT_READY and profile is not None and profile.get("status") == "PRODUCTION":
        return ALLOW_ECC_OUTPUT
    return QUARANTINE_NO_ECC


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
                if not isinstance(item, Mapping):
                    continue
                if item.get("mapping_status") == "UNVERIFIED":
                    unsafe.append(f"UNVERIFIED_SOURCE_MAPPING:{field}")
                normalization_status = item.get("normalization_status")
                if normalization_status == "UNVERIFIED":
                    unsafe.append(f"UNVERIFIED_NORMALIZATION:{field}")
                elif normalization_status == "REVIEW_REQUIRED":
                    unsafe.append(f"SOW_NORMALIZATION_REVIEW_REQUIRED:{field}")
                elif normalization_status == "APPROVED_NO_OUTPUT":
                    # Intentional business skip (e.g. Cancel / Drop): valid
                    # record, but it must never produce ECC output.
                    unsafe.append(f"SOW_NO_PR_TRIGGER:{field}")
        result = {"classification": PR_INPUT_QUARANTINED, "blocking_reasons": unsafe, "warnings": []} if unsafe else validate_canonical_site_record(record, scope)
    output_decision = _output_decision(str(result["classification"]), profile)
    result = {**result, "output_decision": output_decision}
    updated = apply_validation_result(record, result)
    allow_output = output_decision == ALLOW_ECC_OUTPUT
    return {
        "record": updated,
        "classification": result["classification"],
        "allow_output": allow_output,
        "output_decision": output_decision,
        "blocking_reasons": list(result.get("blocking_reasons", [])),
        "warnings": list(result.get("warnings", [])),
    }
