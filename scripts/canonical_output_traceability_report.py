"""Runtime traceability review helpers for guarded canonical PR input records."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping


TRACEABLE = "TRACEABLE"
TRACEABILITY_REVIEW_REQUIRED = "TRACEABILITY_REVIEW_REQUIRED"


def _missing_string(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _expected_traceability_gaps(entry: Mapping[str, Any]) -> list[str]:
    identity = entry.get("source_export_identity", {})
    profile = entry.get("du_profile", {})
    audit = entry.get("validation_audit", {})
    required_checks = (
        ("MISSING_PROFILE_ID", profile.get("profile_id")),
        ("MISSING_PROFILE_VERSION", profile.get("profile_version")),
        ("MISSING_MAPPING_VERSION", profile.get("mapping_version")),
        ("MISSING_HEADER_HASH", identity.get("header_hash")),
        ("MISSING_SOURCE_FILE_HASH", identity.get("source_file_hash")),
        ("MISSING_OUTPUT_DECISION", audit.get("output_decision")),
    )
    return [gap_code for gap_code, value in required_checks if _missing_string(value)]


def build_output_traceability_entry(
    record: Mapping[str, Any],
    *,
    scope: str,
    profile_status: str | None = None,
) -> Dict[str, Any]:
    identity = record.get("identity", {})
    validation = record.get("validation", {})
    traceability_gaps = []

    required_checks = (
        ("MISSING_PROFILE_ID", validation.get("profile_id")),
        ("MISSING_PROFILE_VERSION", validation.get("profile_version")),
        ("MISSING_MAPPING_VERSION", validation.get("mapping_version")),
        ("MISSING_HEADER_HASH", identity.get("header_hash")),
        ("MISSING_SOURCE_FILE_HASH", identity.get("source_file_hash")),
        ("MISSING_OUTPUT_DECISION", validation.get("output_decision")),
    )
    for gap_code, value in required_checks:
        if _missing_string(value):
            traceability_gaps.append(gap_code)

    traceability_status = TRACEABLE if not traceability_gaps else TRACEABILITY_REVIEW_REQUIRED
    return {
        "scope": str(scope).upper(),
        "traceability_status": traceability_status,
        "traceability_gaps": traceability_gaps,
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
            "pr_input_classification": validation.get("pr_input_classification", ""),
            "blocking_reasons": list(validation.get("blocking_reasons", [])),
            "warnings": list(validation.get("warnings", [])),
            "output_decision": validation.get("output_decision", ""),
        },
    }


def build_output_traceability_report(entries: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    entry_list = [dict(entry) for entry in entries]
    counts: Dict[str, int] = {}
    for entry in entry_list:
        status = str(entry.get("traceability_status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    report = {
        "report_type": "canonical_pr_output_traceability_review",
        "entry_count": len(entry_list),
        "traceability_counts": counts,
        "entries": entry_list,
    }
    validate_output_traceability_report(report)
    return report


def validate_output_traceability_report(report: Mapping[str, Any]) -> None:
    entries = [entry for entry in report.get("entries", []) if isinstance(entry, Mapping)]
    counts: Dict[str, int] = {}
    for entry in entries:
        actual_gaps = [str(gap) for gap in entry.get("traceability_gaps", [])]
        expected_gaps = _expected_traceability_gaps(entry)
        if sorted(actual_gaps) != sorted(expected_gaps):
            raise ValueError(
                f"traceability_gaps mismatch for {entry.get('scope', 'UNKNOWN')}: {sorted(actual_gaps)} != {sorted(expected_gaps)}"
            )
        expected_status = TRACEABLE if not expected_gaps else TRACEABILITY_REVIEW_REQUIRED
        actual_status = str(entry.get("traceability_status", ""))
        if actual_status != expected_status:
            raise ValueError(
                f"traceability_status mismatch for {entry.get('scope', 'UNKNOWN')}: {actual_status} != {expected_status}"
            )
        counts[actual_status] = counts.get(actual_status, 0) + 1

    if int(report.get("entry_count", -1)) != len(entries):
        raise ValueError(f"entry_count mismatch: {report.get('entry_count')} != {len(entries)}")

    reported_counts = report.get("traceability_counts", {})
    for status in set(counts) | {str(key) for key in reported_counts.keys()}:
        expected = counts.get(status, 0)
        actual = int(reported_counts.get(status, 0))
        if actual != expected:
            raise ValueError(f"traceability_counts mismatch for {status}: {actual} != {expected}")


def output_traceability_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Canonical PR Output Traceability Review",
        "",
        "Structured runtime traceability review for guarded canonical PR input records.",
        "",
    ]
    counts = report.get("traceability_counts", {})
    if isinstance(counts, Mapping) and counts:
        lines.append("## Traceability Summary")
        lines.append("")
        for status, count in counts.items():
            lines.append(f"- `{status}`: {count}")
        lines.append("")
    for entry in report.get("entries", []):
        identity = entry.get("source_export_identity", {})
        profile = entry.get("du_profile", {})
        audit = entry.get("validation_audit", {})
        lines.append(f"## {identity.get('source_file_name', 'unknown-source')} ({entry.get('scope', 'UNKNOWN')})")
        lines.append("")
        lines.append(f"- Traceability status: `{entry.get('traceability_status', '')}`")
        lines.append(
            f"- Profile: `{profile.get('profile_id', '')}` `{profile.get('profile_version', '')}` "
            f"(mapping `{profile.get('mapping_version', '')}`)"
        )
        lines.append(f"- Header hash: `{identity.get('header_hash', '')}`")
        lines.append(f"- Output decision: `{audit.get('output_decision', '')}`")
        lines.append(f"- Classification: `{audit.get('pr_input_classification', '')}`")
        gaps = entry.get("traceability_gaps", [])
        if gaps:
            lines.append(f"- Traceability gaps: `{', '.join(gaps)}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
