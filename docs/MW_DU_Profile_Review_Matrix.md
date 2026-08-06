# MW DU Profile Review Matrix

Discovery-only cross-profile review matrix for the current DRAFT profiles.

- Profile count: `9`
- Batched review items: `14`

## Batch Review Queue

- Batch priority `01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:01
  hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
- Batch priority `02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:02
  hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
- Batch priority `03` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
  profiles (7): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, tx_rollout_2023_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:01, celcomdigi_bau_2024_pr_v1:01, celcomdigi_usp_pr_v1:02, jendela_tx_migration_pr_v1:02, mw_eos_swap_pr_v1:02, tx_rollout_2023_pr_v1:01, zte_tx_mini_pr_v1:02
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `04` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
  profiles (5): celcomdigi_cd_consolidation_2023_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:05, celcomdigi_usp_pr_v1:01, jendela_tx_migration_pr_v1:01, mw_eos_swap_pr_v1:01, zte_tx_mini_pr_v1:01
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `05` `CONFIRM_COMPETING_CANDIDATE` `region`: Choose one exact four-layer source for `region` from the competing shortlist candidates.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:03
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `06` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:04
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `07` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:06
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `08` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
  profiles (8): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_cd_consolidation_2023_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, tx_rollout_2023_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:04, celcomdigi_bau_2024_pr_v1:04, celcomdigi_cd_consolidation_2023_pr_v1:07, celcomdigi_usp_pr_v1:05, jendela_tx_migration_pr_v1:05, mw_eos_swap_pr_v1:05, tx_rollout_2023_pr_v1:02, zte_tx_mini_pr_v1:05
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `09` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
  profiles (6): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:02, celcomdigi_bau_2024_pr_v1:02, celcomdigi_usp_pr_v1:03, jendela_tx_migration_pr_v1:03, mw_eos_swap_pr_v1:03, zte_tx_mini_pr_v1:03
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `10` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
  profiles (6): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:03, celcomdigi_bau_2024_pr_v1:03, celcomdigi_usp_pr_v1:04, jendela_tx_migration_pr_v1:04, mw_eos_swap_pr_v1:04, zte_tx_mini_pr_v1:04
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `11` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
  profiles (3): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, tx_rollout_2023_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:05, celcomdigi_bau_2024_pr_v1:05, tx_rollout_2023_pr_v1:03
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `12` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:08
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `13` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:09
  hint: Current observed header hash: b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16
- Batch priority `14` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until required mappings, header-hash approval, and regression evidence are complete.
  profiles (1): celcomdigi_cd_consolidation_2023_pr_v1
  priority ids: celcomdigi_cd_consolidation_2023_pr_v1:10
  hint: Use the transition review as the final stop/go check before any status change.

## Profile Summary

### celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1`
- Observed header hash: `b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `4`

### celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-2024-celcomdigi-bau-v2`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `4`

### celcomdigi_cd_consolidation_2023_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-08-05-cd-consolidation-2023-family-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Action count: `10`
- Action type counts:
  - `RESOLVE_MISSING_REQUIRED_FIELD`: `2`
  - `CONFIRM_COMPETING_CANDIDATE`: `4`
  - `VERIFY_SINGLE_CANDIDATE`: `2`
  - `APPROVE_HEADER_HASH`: `1`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-celcomdigi-usp-v2`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`

### jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.4.0`
- Mapping version: `approved-2026-08-04-jendela-tx-migration-v3`
- Observed header hash: `f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`

### mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-mw-eos-swap-v2`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`

### tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `830864906f3e69041995bec10b0a5840d5f8c6fa5defa2cfaef30b868b91a921`
- Action count: `0`
- Action type counts:

### tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.1.1`
- Mapping version: `approved-2026-07-10-2023-tx-rollout-v2`
- Observed header hash: `e61b834994eeef30e7d8249f87616cb04d60598eea323feea50178fc4292c162`
- Action count: `3`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `2`

### zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `PRODUCTION_READY`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-15-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Action count: `5`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
