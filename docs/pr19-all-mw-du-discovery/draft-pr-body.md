## Summary

- adds the all-MW-DU discovery and AI mapping recommendation matrix workflow for Issue #19 as a discovery-only review deliverable
- generates sanitized metadata-only matrix outputs and a committed review summary without committing raw customer exports
- records the autonomous mission state, verification trail, and final report for bounded-step recovery and auditability

## Changed Files

- `docs/MW_DU_All_DU_Discovery_Mapping_Review.md`
- `docs/pr19-all-mw-du-discovery/COMPLETED`
- `docs/pr19-all-mw-du-discovery/autonomous-run-state.json`
- `docs/pr19-all-mw-du-discovery/autonomous-run-state.md`
- `docs/pr19-all-mw-du-discovery/decision-log.md`
- `docs/pr19-all-mw-du-discovery/draft-pr-body.md`
- `docs/pr19-all-mw-du-discovery/execution-plan.md`
- `docs/pr19-all-mw-du-discovery/final-report.md`
- `docs/pr19-all-mw-du-discovery/mapping-review-schema.json`
- `docs/pr19-all-mw-du-discovery/verification-log.md`
- `scripts/build_all_du_mapping_recommendation_matrix.py`
- `scripts/build_du_discovery_registry.py`
- `scripts/refresh_mw_du_discovery_packet.py`
- `tests/test_all_du_mapping_recommendation_matrix.py`
- `tests/test_du_discovery_registry.py`
- `tests/test_refresh_mw_du_discovery_packet.py`

## What Is Local-Only

- `output/local_du_reference_inventory.json`
- `output/local_du_reference_inventory.md`
- `output/all_du_mapping_recommendation_matrix.json`
- `output/all_du_mapping_recommendation_matrix.md`
- any additional ignored local profiler artifacts under `output/` and `Info/reference/`

## Raw Data Safety Confirmation

- no files under `Info/reference/**` are committed
- no raw Excel, CSV, or customer-export rows are committed
- committed docs remain sanitized and metadata-only
- no mapping approval, profile lifecycle promotion, or ECC enablement is included in this PR

## DU Grouping Summary

- `same_or_highly_similar_to_tx_mini`
  - DU models: `2023 TX Rollout`, `TX Mini Project`
  - shared blockers: `existing_ti_pr_status`, `existing_tss_pr_status`, `subcontractor_planning`, `subcontractor_ti`, `tx_sow_raw`
- `missing_pr_critical_fields_quarantine_candidate`
  - DU models: `2023 Celcomdigi BAU`, `2024 Celcomdigi BAU`, `Celcomdigi USP`, `Jendela TX Migration`, `MW EOS Swap`, `ZTE TX MINI`
  - shared blockers: `existing_ti_pr_status`, `existing_tss_pr_status`, `site_code`, `site_name`, `subcontractor_planning`, `subcontractor_ti`, `tx_sow_raw`
- `duplicate_or_competing_export_variants`
  - DU model: `CD consolidation 2023`
  - shared blockers: `existing_ti_pr_status`, `existing_tss_pr_status`, `region`, `site_code`, `site_name`, `tx_sow_raw`

## Key Blockers / Human Review Needed

- current matrix recommendation counts: `HIGH_CONFIDENCE_MATCH=8`, `MEDIUM_CONFIDENCE_REVIEW=3`, `AMBIGUOUS=87`, `MISSING=20`
- PR-status fields across non-TX-Mini exports still need human validation
- several `tx_sow_raw`, `site_code`, `site_name`, and subcontractor candidates remain ambiguous or missing
- duplicate or competing `CD consolidation 2023` export variants still need reviewer direction

## Validation Results

- `python -m py_compile scripts/build_all_du_mapping_recommendation_matrix.py scripts/refresh_mw_du_discovery_packet.py`
- `python -m py_compile scripts/discover_local_du_references.py scripts/build_all_du_mapping_recommendation_matrix.py scripts/refresh_mw_du_discovery_packet.py`
- `python -m py_compile scripts/discover_local_du_references.py scripts/build_all_du_mapping_recommendation_matrix.py scripts/build_du_discovery_registry.py scripts/refresh_mw_du_discovery_packet.py`
- `python -m unittest tests.test_all_du_mapping_recommendation_matrix tests.test_refresh_mw_du_discovery_packet`
  - result: `Ran 2 tests OK`
- `python -m unittest tests.test_discover_local_du_references tests.test_all_du_mapping_recommendation_matrix tests.test_refresh_mw_du_discovery_packet`
  - result: `Ran 5 tests OK`
- `python -m unittest tests.test_refresh_mw_du_discovery_packet tests.test_du_discovery_registry tests.test_du_export_coverage_review tests.test_missing_field_bridge_review tests.test_profile_readiness_review tests.test_profile_action_queue tests.test_profile_review_matrix tests.test_profile_traceability_audit tests.test_discovery_packet_consistency tests.test_profile_status_consistency tests.test_profile_transition_review tests.test_profile_deprecation_review tests.test_profile_rollback_readiness`
  - result: `Ran 68 tests OK`
- `python -m unittest tests.test_discover_local_du_references tests.test_all_du_mapping_recommendation_matrix tests.test_refresh_mw_du_discovery_packet tests.test_du_discovery_registry`
  - result: `Ran 18 tests OK`
- `python scripts/build_all_du_mapping_recommendation_matrix.py`
  - result: generated `10` export summaries and `180` rows
- `python scripts/refresh_mw_du_discovery_packet.py`
  - result: success after local-profiler-root fallback fix
- `git diff --check origin/main..HEAD`
  - result: clean
- `git check-ignore -v Info/reference/du-20260706-profile/`
  - result: ignored by `Info/reference/**`
- `git check-ignore -v "Info/reference/du_exports/A-P202211283695_D002-MW EOS Swap-MW EOS Swap Rollout-20260703160307.xlsx"`
  - result: ignored by `Info/reference/**`

## Explicit Safety Statement

- no mapping approval
- no profile promotion
- no ECC enablement
