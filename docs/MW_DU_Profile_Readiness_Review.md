# MW DU Profile Readiness Review

Lifecycle-readiness summary for the governed DU Profiles.

## celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1`
- Observed header hash: `b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-2024-celcomdigi-bau-v2`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## celcomdigi_cd_consolidation_2023_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-08-05-cd-consolidation-2023-family-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Optional/required competing candidate fields: `region, site_code, site_name, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-celcomdigi-usp-v2`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `site_name, subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.5.0`
- Mapping version: `approved-2026-08-11-jendela-tx-migration-v4`
- Observed header hash: `f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `site_name, subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-mw-eos-swap-v2`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `site_name, subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `830864906f3e69041995bec10b0a5840d5f8c6fa5defa2cfaef30b868b91a921`
- Approved header hashes: `3`
- Overall blockers: ``
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.1.1`
- Mapping version: `approved-2026-07-10-2023-tx-rollout-v2`
- Observed header hash: `e61b834994eeef30e7d8249f87616cb04d60598eea323feea50178fc4292c162`
- Approved header hashes: `2`
- Overall blockers: ``
- Optional/required competing candidate fields: `subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.

## zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-15-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Approved header hashes: `1`
- Overall blockers: ``
- Optional/required competing candidate fields: `site_name, subcontractor_planning`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED required-field conditions before runtime enablement.
  - Complete regression verification before lifecycle promotion.
