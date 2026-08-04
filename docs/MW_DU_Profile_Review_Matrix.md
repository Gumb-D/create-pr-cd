# MW DU Profile Review Matrix

Discovery-only cross-profile review matrix for the current DRAFT profiles.

- Profile count: `10`
- Batched review items: `14`

## Batch Review Queue

- Batch priority `01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:01, cd_consolidation_2023_rollout_pr_v1:01
  hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
  hint: Review donor export Celcomdigi USP with similarity 0.850 before deciding derived, manual, or blocking treatment.
- Batch priority `02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:02, cd_consolidation_2023_rollout_pr_v1:02
  hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
  hint: Review donor export Celcomdigi USP with similarity 0.850 before deciding derived, manual, or blocking treatment.
- Batch priority `03` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
  profiles (7): celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, tx_rollout_2023_pr_v1, zte_tx_mini_pr_v1
  priority ids: celcomdigi_bau_2023_pr_v1:01, celcomdigi_bau_2024_pr_v1:01, celcomdigi_usp_pr_v1:02, jendela_tx_migration_pr_v1:02, mw_eos_swap_pr_v1:02, tx_rollout_2023_pr_v1:01, zte_tx_mini_pr_v1:02
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `04` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
  profiles (5): cd_consolidation_2023_decom_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, zte_tx_mini_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:05, celcomdigi_usp_pr_v1:01, jendela_tx_migration_pr_v1:01, mw_eos_swap_pr_v1:01, zte_tx_mini_pr_v1:01
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `05` `CONFIRM_COMPETING_CANDIDATE` `region`: Choose one exact four-layer source for `region` from the competing shortlist candidates.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:03, cd_consolidation_2023_rollout_pr_v1:03
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `06` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:04, cd_consolidation_2023_rollout_pr_v1:04
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `07` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:06, cd_consolidation_2023_rollout_pr_v1:05
  hint: Use the unresolved review packet to compare the currently selected source against alternates.
- Batch priority `08` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
  profiles (9): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1, celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, tx_rollout_2023_pr_v1, zte_tx_mini_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:07, cd_consolidation_2023_rollout_pr_v1:06, celcomdigi_bau_2023_pr_v1:04, celcomdigi_bau_2024_pr_v1:04, celcomdigi_usp_pr_v1:05, jendela_tx_migration_pr_v1:05, mw_eos_swap_pr_v1:05, tx_rollout_2023_pr_v1:02, zte_tx_mini_pr_v1:05
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
  profiles (4): cd_consolidation_2023_rollout_pr_v1, celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, tx_rollout_2023_pr_v1
  priority ids: cd_consolidation_2023_rollout_pr_v1:07, celcomdigi_bau_2023_pr_v1:05, celcomdigi_bau_2024_pr_v1:05, tx_rollout_2023_pr_v1:03
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `12` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:08, cd_consolidation_2023_rollout_pr_v1:08
  hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
- Batch priority `13` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
  profiles (2): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:09, cd_consolidation_2023_rollout_pr_v1:09
  hint: Current observed header hash: b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16
  hint: Current observed header hash: d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1
- Batch priority `14` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
  profiles (10): cd_consolidation_2023_decom_pr_v1, cd_consolidation_2023_rollout_pr_v1, celcomdigi_bau_2023_pr_v1, celcomdigi_bau_2024_pr_v1, celcomdigi_usp_pr_v1, jendela_tx_migration_pr_v1, mw_eos_swap_pr_v1, tx_mini_pr_v1, tx_rollout_2023_pr_v1, zte_tx_mini_pr_v1
  priority ids: cd_consolidation_2023_decom_pr_v1:10, cd_consolidation_2023_rollout_pr_v1:10, celcomdigi_bau_2023_pr_v1:06, celcomdigi_bau_2024_pr_v1:06, celcomdigi_usp_pr_v1:06, jendela_tx_migration_pr_v1:06, mw_eos_swap_pr_v1:06, tx_mini_pr_v1:01, tx_rollout_2023_pr_v1:04, zte_tx_mini_pr_v1:06
  hint: Use the transition review as the final stop/go check before any status change.

## Profile Summary

### cd_consolidation_2023_decom_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-decom-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Action count: `10`
- Action type counts:
  - `RESOLVE_MISSING_REQUIRED_FIELD`: `2`
  - `CONFIRM_COMPETING_CANDIDATE`: `4`
  - `VERIFY_SINGLE_CANDIDATE`: `2`
  - `APPROVE_HEADER_HASH`: `1`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### cd_consolidation_2023_rollout_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-rollout-v1`
- Observed header hash: `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`
- Action count: `10`
- Action type counts:
  - `RESOLVE_MISSING_REQUIRED_FIELD`: `2`
  - `CONFIRM_COMPETING_CANDIDATE`: `3`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
  - `APPROVE_HEADER_HASH`: `1`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1`
- Observed header hash: `b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `4`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-2024-celcomdigi-bau-v2`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `4`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-celcomdigi-usp-v2`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.3.0`
- Mapping version: `approved-2026-08-04-jendela-tx-migration-v2`
- Observed header hash: `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-mw-eos-swap-v2`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221`
- Action count: `1`
- Action type counts:
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.1.0`
- Mapping version: `approved-2026-07-10-2023-tx-rollout-v2`
- Observed header hash: `8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320`
- Action count: `4`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `1`
  - `VERIFY_SINGLE_CANDIDATE`: `2`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`

### zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile version: `0.2.0`
- Mapping version: `approved-2026-07-15-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Action count: `6`
- Action type counts:
  - `CONFIRM_COMPETING_CANDIDATE`: `2`
  - `VERIFY_SINGLE_CANDIDATE`: `3`
  - `HOLD_LIFECYCLE_PROMOTION`: `1`
