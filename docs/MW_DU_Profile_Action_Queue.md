# MW DU Profile Action Queue

Discovery-only prioritized manual action queue for the current DRAFT profiles.

## tx_mini_pr_v1 (TX Mini Project)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `BUSINESS_VALIDATED`
- Mapping version: `approved-2026-07-07-tx-mini-v1`
- Observed header hash: `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221`
- Action queue:
  - `tx_mini_pr_v1:01` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## mw_eos_swap_pr_v1 (MW EOS Swap)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-06-mw-eos-swap-v1`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Action queue:
  - `mw_eos_swap_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.086 before deciding derived, manual, or blocking treatment.
  - `mw_eos_swap_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.086 before deciding derived, manual, or blocking treatment.
  - `mw_eos_swap_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:07` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `mw_eos_swap_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `mw_eos_swap_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: 46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a
  - `mw_eos_swap_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-06-2023-tx-rollout-v1`
- Observed header hash: `8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320`
- Action queue:
  - `tx_rollout_2023_pr_v1:01` `CONFIRM_COMPETING_CANDIDATE` `existing_ti_pr_status`: Choose one exact four-layer source for `existing_ti_pr_status` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:02` `CONFIRM_COMPETING_CANDIDATE` `existing_tss_pr_status`: Choose one exact four-layer source for `existing_tss_pr_status` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `tx_rollout_2023_pr_v1:06` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `tx_rollout_2023_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `tx_rollout_2023_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `site_code`: Verify the current single shortlist-aligned source for `site_code`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `tx_rollout_2023_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `tx_rollout_2023_pr_v1:10` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: 8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320
  - `tx_rollout_2023_pr_v1:11` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-jendela-tx-migration-v1`
- Observed header hash: `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3`
- Action queue:
  - `jendela_tx_migration_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `jendela_tx_migration_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `jendela_tx_migration_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `jendela_tx_migration_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `site_code`: Verify the current single shortlist-aligned source for `site_code`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `jendela_tx_migration_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: 904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3
  - `jendela_tx_migration_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## zte_tx_mini_pr_v1 (ZTE TX MINI)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-06-zte-tx-mini-v1`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Action queue:
  - `zte_tx_mini_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.088 before deciding derived, manual, or blocking treatment.
  - `zte_tx_mini_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.088 before deciding derived, manual, or blocking treatment.
  - `zte_tx_mini_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:07` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `zte_tx_mini_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `zte_tx_mini_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810
  - `zte_tx_mini_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-2023-celcomdigi-bau-v1`
- Observed header hash: `77fa728c7a4105d9062378a999228cf24575e56e82ee97bce3ab9be630d7b313`
- Action queue:
  - `celcomdigi_bau_2023_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_bau_2023_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_bau_2023_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2023_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2023_pr_v1:05` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:06` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `site_code`: Verify the current single shortlist-aligned source for `site_code`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2023_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: 77fa728c7a4105d9062378a999228cf24575e56e82ee97bce3ab9be630d7b313
  - `celcomdigi_bau_2023_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-2024-celcomdigi-bau-v1`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Action queue:
  - `celcomdigi_bau_2024_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_bau_2024_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_bau_2024_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2024_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2024_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_bau_2024_pr_v1:06` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `site_code`: Verify the current single shortlist-aligned source for `site_code`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_bau_2024_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86
  - `celcomdigi_bau_2024_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-celcomdigi-usp-v1`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Action queue:
  - `celcomdigi_usp_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_usp_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `celcomdigi_usp_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_planning`: Choose one exact four-layer source for `subcontractor_planning` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `subcontractor_ti`: Choose one exact four-layer source for `subcontractor_ti` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:07` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `celcomdigi_usp_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `antenna_size_fe`: Verify the current single shortlist-aligned source for `antenna_size_fe`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:09` `VERIFY_SINGLE_CANDIDATE` `antenna_size_ne`: Verify the current single shortlist-aligned source for `antenna_size_ne`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:10` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:11` `VERIFY_SINGLE_CANDIDATE` `region`: Verify the current single shortlist-aligned source for `region`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `celcomdigi_usp_pr_v1:12` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: 79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf
  - `celcomdigi_usp_pr_v1:13` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## cd_consolidation_2023_decom_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-decom-v1`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Action queue:
  - `cd_consolidation_2023_decom_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `cd_consolidation_2023_decom_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `cd_consolidation_2023_decom_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `region`: Choose one exact four-layer source for `region` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_decom_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_decom_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `site_name`: Choose one exact four-layer source for `site_name` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_decom_pr_v1:06` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_decom_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `cd_consolidation_2023_decom_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `cd_consolidation_2023_decom_pr_v1:09` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16
  - `cd_consolidation_2023_decom_pr_v1:10` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.

## cd_consolidation_2023_rollout_pr_v1 (CD consolidation 2023)

- Readiness status: `DISCOVERY_ONLY_BLOCKED`
- Profile status: `DRAFT`
- Mapping version: `discovery-2026-07-07-cd-consolidation-2023-rollout-v1`
- Observed header hash: `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`
- Action queue:
  - `cd_consolidation_2023_rollout_pr_v1:01` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_ti_pr_status`: Resolve required field `existing_ti_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `cd_consolidation_2023_rollout_pr_v1:02` `RESOLVE_MISSING_REQUIRED_FIELD` `existing_tss_pr_status`: Resolve required field `existing_tss_pr_status` before any lifecycle promotion.
    hint: Review donor export 2023 TX Rollout with similarity 0.000 before deciding derived, manual, or blocking treatment.
  - `cd_consolidation_2023_rollout_pr_v1:03` `CONFIRM_COMPETING_CANDIDATE` `region`: Choose one exact four-layer source for `region` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_rollout_pr_v1:04` `CONFIRM_COMPETING_CANDIDATE` `site_code`: Choose one exact four-layer source for `site_code` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_rollout_pr_v1:05` `CONFIRM_COMPETING_CANDIDATE` `tx_sow_raw`: Choose one exact four-layer source for `tx_sow_raw` from the competing shortlist candidates.
    hint: Use the unresolved review packet to compare the currently selected source against alternates.
  - `cd_consolidation_2023_rollout_pr_v1:06` `VERIFY_SINGLE_CANDIDATE` `du_key`: Verify the current single shortlist-aligned source for `du_key`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `cd_consolidation_2023_rollout_pr_v1:07` `VERIFY_SINGLE_CANDIDATE` `site_name`: Verify the current single shortlist-aligned source for `site_name`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `cd_consolidation_2023_rollout_pr_v1:08` `VERIFY_SINGLE_CANDIDATE` `subcontractor_ti`: Verify the current single shortlist-aligned source for `subcontractor_ti`.
    hint: Confirm the four-layer fingerprint and business meaning before changing mapping_status.
  - `cd_consolidation_2023_rollout_pr_v1:09` `APPROVE_HEADER_HASH`: Approve at least one header hash for this profile version after the field review is complete.
    hint: Current observed header hash: d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1
  - `cd_consolidation_2023_rollout_pr_v1:10` `HOLD_LIFECYCLE_PROMOTION`: Keep the profile blocked from lifecycle promotion until mapping review, header-hash approval, regression, and UAT evidence exist.
    hint: Use the transition review as the final stop/go check before any status change.
