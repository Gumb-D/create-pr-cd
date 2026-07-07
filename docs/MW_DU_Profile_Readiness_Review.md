# MW DU Profile Readiness Review

Discovery-only summary of why the current priority DU profiles remain blocked from release.

## tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221`
- Approved header hashes: `1`
- Overall blockers: `PROFILE_NOT_PRODUCTION, COMPETING_SHORTLIST_CANDIDATES`
- Competing candidate fields: `subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-06-mw-eos-swap-v1`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `site_code, site_name, subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-06-2023-tx-rollout-v1`
- Observed header hash: `8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS`
- Competing candidate fields: `existing_ti_pr_status, existing_tss_pr_status, subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-jendela-tx-migration-v1`
- Observed header hash: `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `site_name, subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-06-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `site_code, site_name, subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-2023-celcomdigi-bau-v1`
- Observed header hash: `77fa728c7a4105d9062378a999228cf24575e56e82ee97bce3ab9be630d7b313`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `subcontractor_planning, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-2024-celcomdigi-bau-v1`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-celcomdigi-usp-v1`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `site_code, site_name, subcontractor_planning, subcontractor_ti, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## cd_consolidation_2023_decom_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-decom-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `region, site_code, site_name, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.

## cd_consolidation_2023_rollout_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-rollout-v1`
- Observed header hash: `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`
- Approved header hashes: `0`
- Overall blockers: `PROFILE_NOT_PRODUCTION, NO_APPROVED_HEADER_HASH, REQUIRED_FIELDS_NOT_APPROVED, MISSING_REQUIRED_FIELDS, COMPETING_SHORTLIST_CANDIDATES, UNVERIFIED_SINGLE_CANDIDATE_FIELDS, CROSS_MODEL_BRIDGE_ONLY_FIELDS`
- Missing required fields: `existing_ti_pr_status, existing_tss_pr_status`
- Competing candidate fields: `region, site_code, tx_sow_raw`
- Cross-model bridge-only fields: `existing_ti_pr_status, existing_tss_pr_status`
- Release prerequisites:
  - Approve the DU model identity and four-layer source mappings.
  - Approve at least one header hash for the profile version.
  - Resolve missing required fields or keep the profile blocked.
  - Remove DRAFT-only and UNVERIFIED mapping conditions before runtime enablement.
  - Complete regression verification and UAT before any lifecycle promotion.
