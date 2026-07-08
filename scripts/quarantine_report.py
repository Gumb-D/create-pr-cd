"""Structured quarantine-report helpers for blocked canonical PR input records.

The report stays intentionally narrow: it includes only the audit fields and the
skill-relevant canonical fields needed to review why a site was blocked.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from canonical_site_validator import ALLOW_ECC_OUTPUT, FIELD_PATHS, PR_INPUT_READY, QUARANTINE_NO_ECC

SKILL_RELATED_FIELDS = (
    "site_code",
    "site_name",
    "du_key",
    "region",
    "tx_sow_raw",
    "subcontractor_ti",
    "subcontractor_planning",
    "existing_tss_pr_status",
    "existing_ti_pr_status",
    "antenna_size_ne",
    "antenna_size_fe",
)


def _get_path(record: Mapping[str, Any], canonical_field: str) -> Any:
    path = FIELD_PATHS.get(canonical_field)
    if not path:
        return None
    section = record.get(path[0], {})
    return section.get(path[1]) if isinstance(section, Mapping) else None


def _field_review(record: Mapping[str, Any], canonical_field: str) -> Dict[str, Any]:
    evidence_fields = record.get("source_evidence", {}).get("fields", {})
    evidence = evidence_fields.get(canonical_field, {}) if isinstance(evidence_fields, Mapping) else {}
    item = {
        "canonical_field": canonical_field,
        "value": _get_path(record, canonical_field),
        "source_header_fingerprint": evidence.get("source_header_fingerprint"),
        "source_value": evidence.get("source_value"),
        "transformation": evidence.get("transformation", "none"),
    }
    if "mapping_status" in evidence:
        item["mapping_status"] = evidence.get("mapping_status")
    if "normalization_status" in evidence:
        item["normalization_status"] = evidence.get("normalization_status")
    return item


def build_quarantine_entry(
    record: Mapping[str, Any],
    *,
    scope: str,
    profile_status: str | None = None,
    output_decision: str | None = None,
) -> Dict[str, Any]:
    """Create one explicit review packet entry for a gated canonical record."""
    validation = record.get("validation", {})
    identity = record.get("identity", {})
    classification = validation.get("pr_input_classification", "")
    allow_output = classification == PR_INPUT_READY and profile_status == "PRODUCTION"
    inferred_output_decision = ALLOW_ECC_OUTPUT if allow_output else QUARANTINE_NO_ECC
    return {
        "scope": str(scope).upper(),
        "source_export_identity": {
            "project_key": identity.get("project_key", ""),
            "project_id": identity.get("project_id", ""),
            "du_model_name": identity.get("du_model_name", ""),
            "du_model_id": identity.get("du_model_id", ""),
            "view_id": identity.get("view_id", ""),
            "source_file_name": identity.get("source_file_name", ""),
            "source_file_hash": identity.get("source_file_hash", ""),
            "header_hash": identity.get("header_hash", ""),
            "source_row_number": identity.get("source_row_number"),
        },
        "du_profile": {
            "profile_id": validation.get("profile_id", ""),
            "profile_version": validation.get("profile_version", ""),
            "mapping_version": validation.get("mapping_version", ""),
            "profile_status": profile_status or "UNKNOWN",
        },
        "validation_audit": {
            "pr_input_classification": classification,
            "blocking_reasons": list(validation.get("blocking_reasons", [])),
            "warnings": list(validation.get("warnings", [])),
            "allow_output": allow_output,
            "output_decision": output_decision or validation.get("output_decision", inferred_output_decision),
        },
        "skill_field_review": [_field_review(record, field) for field in SKILL_RELATED_FIELDS],
    }


def build_quarantine_report(entries: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    entry_list = [dict(entry) for entry in entries]
    counts: Dict[str, int] = {}
    for entry in entry_list:
        decision = str(entry.get("validation_audit", {}).get("output_decision", "UNKNOWN"))
        counts[decision] = counts.get(decision, 0) + 1
    report = {
        "report_type": "canonical_pr_input_quarantine_review",
        "entry_count": len(entry_list),
        "decision_counts": counts,
        "entries": entry_list,
    }
    validate_quarantine_report(report)
    return report


def validate_quarantine_report(report: Mapping[str, Any]) -> None:
    entries = [entry for entry in report.get("entries", []) if isinstance(entry, Mapping)]
    counts: Dict[str, int] = {}
    for entry in entries:
        audit = entry.get("validation_audit", {})
        decision = str(audit.get("output_decision", "UNKNOWN"))
        allow_output = bool(audit.get("allow_output", False))
        if allow_output != (decision == ALLOW_ECC_OUTPUT):
            raise ValueError(
                f"allow_output mismatch for {entry.get('scope', 'UNKNOWN')}: {allow_output} != {decision}"
            )
        reviewed_fields = [
            str(field.get("canonical_field"))
            for field in entry.get("skill_field_review", [])
            if isinstance(field, Mapping)
        ]
        if reviewed_fields != list(SKILL_RELATED_FIELDS):
            raise ValueError(
                f"skill_field_review mismatch for {entry.get('scope', 'UNKNOWN')}: {reviewed_fields} != {list(SKILL_RELATED_FIELDS)}"
            )
        counts[decision] = counts.get(decision, 0) + 1

    if int(report.get("entry_count", -1)) != len(entries):
        raise ValueError(f"entry_count mismatch: {report.get('entry_count')} != {len(entries)}")

    reported_counts = report.get("decision_counts", {})
    for decision in set(counts) | {str(key) for key in reported_counts.keys()}:
        expected = counts.get(decision, 0)
        actual = int(reported_counts.get(decision, 0))
        if actual != expected:
            raise ValueError(f"decision_counts mismatch for {decision}: {actual} != {expected}")


def quarantine_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Canonical PR Input Quarantine Review",
        "",
        "Structured review packet for blocked or review-only canonical PR input records.",
        "",
    ]
    counts = report.get("decision_counts", {})
    if isinstance(counts, Mapping) and counts:
        lines.append("## Decision Summary")
        lines.append("")
        for decision, count in counts.items():
            lines.append(f"- `{decision}`: {count}")
        lines.append("")
    for entry in report.get("entries", []):
        identity = entry.get("source_export_identity", {})
        profile = entry.get("du_profile", {})
        audit = entry.get("validation_audit", {})
        lines.append(
            f"## {identity.get('source_file_name', 'unknown-source')} "
            f"({entry.get('scope', 'UNKNOWN')})"
        )
        lines.append("")
        lines.append(f"- DU model: `{identity.get('du_model_name', '')}`")
        lines.append(
            f"- Profile: `{profile.get('profile_id', '')}` `{profile.get('profile_version', '')}` "
            f"(mapping `{profile.get('mapping_version', '')}`)"
        )
        lines.append(f"- Classification: `{audit.get('pr_input_classification', '')}`")
        lines.append(f"- Output decision: `{audit.get('output_decision', '')}`")
        reasons = audit.get("blocking_reasons", [])
        if reasons:
            lines.append("- Blocking reasons:")
            for reason in reasons:
                lines.append(f"  - `{reason}`")
        warnings = audit.get("warnings", [])
        if warnings:
            lines.append("- Warnings:")
            for warning in warnings:
                lines.append(f"  - `{warning}`")
        lines.append("- Skill-field review:")
        for field in entry.get("skill_field_review", []):
            lines.append(
                f"  - `{field['canonical_field']}` = `{field.get('value', '')}` "
                f"(mapping={field.get('mapping_status', 'n/a')}, "
                f"normalization={field.get('normalization_status', 'n/a')})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
