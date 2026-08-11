# MW DU Profile Action Queue

Prioritized governance action queue for the current DU Profiles.

## celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1`
- Observed header hash: `b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454`
- Action queue:
  - `celcomdigi_bau_2023_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2023_pr_v1:02` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-10-2024-celcomdigi-bau-v2`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Action queue:
  - `celcomdigi_bau_2024_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2024_pr_v1:02` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## celcomdigi_cd_consolidation_2023_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-08-05-cd-consolidation-2023-family-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Action queue:
  - `celcomdigi_cd_consolidation_2023_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_cd_consolidation_2023_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export TX Mini Project with similarity 0.850 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_cd_consolidation_2023_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `region`: Choose one exact four-layer source for `region` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_cd_consolidation_2023_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_cd_consolidation_2023_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_cd_consolidation_2023_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_cd_consolidation_2023_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_cd_consolidation_2023_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_cd_consolidation_2023_pr_v1:09` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16
  - `celcomdigi_cd_consolidation_2023_pr_v1:10` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until required mappings, header-hash approval, and regression evidence are complete.
    hint: Use the transition review as the final stop/go check before any status change.

## celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-10-celcomdigi-usp-v2`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Action queue:
  - `celcomdigi_usp_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:02` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-08-11-jendela-tx-migration-v4`
- Observed header hash: `f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056`
- Action queue:
  - `jendela_tx_migration_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:02` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-10-mw-eos-swap-v2`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Action queue:
  - `mw_eos_swap_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:02` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `830864906f3e69041995bec10b0a5840d5f8c6fa5defa2cfaef30b868b91a921`
- Action queue:
  - `NONE`: No required blocker or optional follow-up action is currently recorded.

## tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-10-2023-tx-rollout-v2`
- Observed header hash: `e61b834994eeef30e7d8249f87616cb04d60598eea323feea50178fc4292c162`
- Action queue:
  - `tx_rollout_2023_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:02` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `tx_rollout_2023_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.

## zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `PRODUCTION_READY`
- Profile status: `PRODUCTION`
- Mapping version: `approved-2026-07-15-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Action queue:
  - `zte_tx_mini_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:02` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:03` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:04` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
