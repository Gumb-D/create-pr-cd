"""Fail-closed PR input gate for canonical records and raw iEPMS exports."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from canonical_site_validator import (
    PR_INPUT_QUARANTINED,
    PR_INPUT_READY,
    apply_validation_result,
    validate_canonical_site_record,
)


def _identity_matches_profile(record: Mapping[str, Any], profile: Mapping[str, Any]) -> bool:
    identity = record.get("identity", {})
    profile_identity = profile.get("identity", {})
    checks = (
        ("du_model_name", "accepted_du_models"),
        ("du_model_id", "accepted_du_model_ids"),
        ("view_id", "accepted_view_ids"),
    )
    for record_key, profile_key in checks:
        accepted = profile_identity.get(profile_key, [])
        value = str(identity.get(record_key, ""))
        if accepted and value not in {str(item) for item in accepted}:
            return False
    return True


def gate_raw_iepms_export(*_: Any, **__: Any) -> Dict[str, Any]:
    """Explicitly deny direct raw-export-to-ECC execution in the foundation release."""
    return {
        "classification": PR_INPUT_QUARANTINED,
        "allow_ecc_generation": False,
        "blocking_reasons": ["RAW_IEPMS_EXPORT_DIRECT_ECC_PROHIBITED"],
        "allowed_next_actions": ["PROFILE_EXPORT", "VALIDATE_DU_PROFILE", "BUILD_CANONICAL_RECORD"],
    }


def gate_canonical_site_record(
    record: Mapping[str, Any],
    profile: Mapping[str, Any] | None,
    *,
    scope: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Apply lifecycle, DU identity, header hash, and canonical contract controls."""
    if profile is None:
        result = {
            "classification": PR_INPUT_QUARANTED,
            "blocking_reasons": ["UNKNOWN_DU_PROFILE"],
            "warnings": [],
        }
    elif profile.get("status") != "PRODUCTION":
        result = {
            "classification": PR_INPUT_QUARANTINED,
            "blocking_reasons": ["DU_PROFILE_NOT_PRODUCTION"],
            "warnings": ["Dry-run/profiling is allowed; ECC generation remains prohibited."] if dry_run else [],
        }
    elif not _identity_matches_profile(record, profile):
        result = {
            "classification": PR_INPUT_QUARANTINED,
            "blocking_reasons": ["UNKNOWN_DU_MODEL_OR_VIEW"],
            "warnings": [],
        }
    else:
        observed_hash = str(record.get("identity", {}).get("header_hash", ""))
        approved_hashes = {str(value) for value in profile.get("export_structure", {}).get("approved_header_hashes", [])}
        if observed_hash not in approved_hashes:
            result = {
                "classification": PR_INPUT_QUARANTINED,
                "blocking_reasons": ["HEADER_HASH_REVALIDATION_REQUIRED"],
                "warnings": ["Dry-run only; revalidate the DU profile before production use."] if dry_run else [],
            }
        else:
            evidence_fields = record.get("source_evidence", {}).get("fields", {})
            unverified = []
            if isinstance(evidence_fields, Mapping):
                for field, evidence in evidence_fields.items():
                    if not isinstance(evidence, Mapping):
                        continue
                    if evidence.get("mapping_status") == "UNVERIFIED":
                        unverified.append(f"UNVERIFIED_SOURCE_MAPPING:{field}")
                    if evidence.get("normalization_status") == "UNVERIFIED":
                        unverified.append(f"UNVERIFIED_NORMALIZATION:{field}")
            if unverified:
                result = {
                    "classification": PR_INPUT_QUARANTINED,
                    "blocking_reasons": unverified,
                    "warnings": [],
                }
            else:
                result = validate_canonical_site_record(record, scope)

    updated = apply_validation_result(record, result)
    classification = result["classification"]
    # PR_INPUT_READY_WITH_REVIEW has no automatic ECC in this foundation;
    # a future shared-rule review workflow must explicitly promote it.
    allow_ecc = classification == PR_INPUT_READY and profile is not None and profile.get("status") == "PRODUCTION"
    return {
        "record": updated,
        "classification": classification,
        "allow_ecc_generation": allow_ecc,
        "blocking_reasons": list(result.get("blocking_reasons", [])),
        "warnings": list(result.get("warnings", [])),
    }
