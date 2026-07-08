# MW DU Canonical PR Output Traceability Report

This document defines the runtime traceability review format for guarded canonical PR input records.

The report is intended to answer one narrow question:

- does this guarded canonical record carry enough profile and source-export identity to make its output decision traceable?

The report is reporting-only. It does not approve a profile, does not enable ECC output, and does not bypass the fail-closed guard.

## Report Shape

```yaml
report_type: canonical_pr_output_traceability_review
entry_count: 1
traceability_counts:
  TRACEABLE: 1
entries:
  - scope: TI
    traceability_status: TRACEABLE
    traceability_gaps: []
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
      mapping_version: approved-mapping-v1
      profile_status: PRODUCTION
    validation_audit:
      pr_input_classification: PR_INPUT_READY
      blocking_reasons: []
      warnings: []
      output_decision: ALLOW_ECC_OUTPUT
```

## Fail-Closed Rule

If any of these fields are missing, the report must mark the entry `TRACEABILITY_REVIEW_REQUIRED`:

- `profile_id`
- `profile_version`
- `mapping_version`
- `header_hash`
- `source_file_hash`
- `output_decision`

The current builder records those gaps explicitly so missing audit evidence cannot look complete.

The current implementation also validates the report shape itself:

- `entry_count` must match the number of entries
- `traceability_counts` must match the statuses derived from the entries
- each entry's `traceability_status` must agree with whether `traceability_gaps` is empty

## Current Implementation

- Builder module: [canonical_output_traceability_report.py](/C:/dev/create-pr-cd/scripts/canonical_output_traceability_report.py)
- Supporting guard contract: [pr_input_guard.py](/C:/dev/create-pr-cd/scripts/pr_input_guard.py)
- Canonical record contract: [canonical_site_validator.py](/C:/dev/create-pr-cd/scripts/canonical_site_validator.py)
- Tests: [test_canonical_output_traceability_report.py](/C:/dev/create-pr-cd/tests/test_canonical_output_traceability_report.py)

The current implementation works on guarded canonical records only. It strengthens runtime auditability without changing `scripts/generate_tss_pr_ecc.py` or promoting any DRAFT DU profile.
