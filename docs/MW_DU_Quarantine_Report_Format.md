# MW DU Canonical PR Input Quarantine Report Format

This document defines the review packet format for canonical PR input records that are blocked from ECC generation.

The format is intentionally limited to:

- source export identity
- DU profile identity
- mapping version
- validation classification, blocking reasons, warnings, and output decision
- skill-relevant field review only

It does not approve any mapping, header hash, or DU profile transition.

## Report Shape

```yaml
report_type: canonical_pr_input_quarantine_review
entry_count: 1
decision_counts:
  QUARANTINE_NO_ECC: 1
entries:
  - scope: TI
    source_export_identity:
      project_key: CelcomDigi_MW
      project_id: <iepms-project-id>
      du_model_name: MW EOS Swap
      du_model_id: <iepms-du-model-id>
      view_id: <iepms-view-id>
      source_file_name: <export-file-name>
      source_file_hash: <sha256>
      header_hash: <sha256>
      source_row_number: 7
    du_profile:
      profile_id: mw_eos_swap_pr_v1
      profile_version: "1.0.0"
      mapping_version: discovery-2026-07-06-mw-eos-swap-v1
      profile_status: DRAFT
    validation_audit:
      pr_input_classification: PR_INPUT_QUARANTINED
      blocking_reasons:
        - DU_PROFILE_NOT_PRODUCTION
      warnings:
        - Dry-run only
      allow_output: false
      output_decision: QUARANTINE_NO_ECC
    skill_field_review:
      - canonical_field: site_code
        value: A0001
        source_header_fingerprint: <four-layer fingerprint>
        source_value: A0001
        transformation: trim
        mapping_status: UNVERIFIED
```

## Included Skill Fields

The current review packet is limited to the fields that are directly relevant to the `create-pr-cd` skill:

- `site_code`
- `site_name`
- `du_key`
- `region`
- `tx_sow_raw`
- `subcontractor_ti`
- `subcontractor_planning`
- `existing_tss_pr_status`
- `existing_ti_pr_status`
- `antenna_size_ne`
- `antenna_size_fe`

These fields reflect the current scope triggers, duplicate-prevention checks, subcontractor selection, and TI antenna review needs already defined in [SKILL.md](/C:/dev/create-pr-cd/SKILL.md).

## Current Implementation

- Builder module: [quarantine_report.py](/C:/dev/create-pr-cd/scripts/quarantine_report.py)
- Guard module: [pr_input_guard.py](/C:/dev/create-pr-cd/scripts/pr_input_guard.py)
- Tests: [test_quarantine_report.py](/C:/dev/create-pr-cd/tests/test_quarantine_report.py)
- Guard tests: [test_canonical_site_validator.py](/C:/dev/create-pr-cd/tests/test_canonical_site_validator.py)

The guard now stamps the final runtime `output_decision` onto the canonical record's `validation` block before any downstream output step can inspect it. The builder then reports that same decision instead of inventing a separate result.

The current implementation also validates the report shape itself:

- `entry_count` must match the number of entries
- `decision_counts` must match the decisions derived from the entries
- each entry's `allow_output` flag must agree with its `output_decision`

The builder remains reporting-only. It does not change `scripts/generate_tss_pr_ecc.py`, does not enable any DRAFT profile, and does not bypass the existing fail-closed guard.
