# MW DU Unresolved Skill-Field Review

Discovery-only manual-review packet for priority DRAFT profiles. This does not approve any field mapping, header hash, or profile lifecycle transition.

## tx_mini_pr_v1 (TX Mini Project)

- Source file: `A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx`
- Observed header hash: `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221`
- Missing required fields: None
- Competing candidate fields: None
- Single-candidate but unverified fields: None
- Resolved by approved mapping (alternates rejected): subcontractor_planning, tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00012|4188808420049567786|2477626672974883536 | Site Basic Info | Site Basic Info | customer site code`

### `site_name`

- Skill field: `site_name`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`

### `du_key`

- Skill field: `du_code`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ0657771 | Installation | Wireless RAN | SubCon - TI Team`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ01027586 | Network Planning | Microwave | Subcon - Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01027605 | Network Planning | Microwave | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI`


## mw_eos_swap_pr_v1 (MW EOS Swap)

- Source file: `A-P202211283695_D002-MW EOS Swap-MW EOS Swap Rollout-20260703160307.xlsx`
- Observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Missing required fields: None
- Competing candidate fields: site_name, subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key
- Resolved by approved mapping (alternates rejected): site_code, tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `site|fix00012|5440935430300168497|7476572371505372260 | Site Basic Info | Site Basic Info | customer site code`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ01027674 | Planner | Microwave | FE Site ID`
    reason: Alternate site ID style field.

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ01092967 | Network Planning | Microwave | FE Site Name`
    reason: Alternate site-name style field.

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ01100642 | Network Planning | Microwave | Microwave Tx SOW-1`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ01079156 | Network Planning | Microwave | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00970184 | Rollout | Microwave | Subcon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01087327 | Network Planning | Microwave | Subcon - Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01087326 | Network Planning | Microwave | Subcon - PR Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ01093667 | Planner | Microwave | MW Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ01093668 | Planner | Microwave | MW Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00959244 | Commercial | Microwave | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00959243 | Commercial | Microwave | Subcon PR - TI`


## tx_rollout_2023_pr_v1 (2023 TX Rollout)

- Source file: `A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx`
- Observed header hash: `8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320`
- Missing required fields: None
- Competing candidate fields: subcontractor_planning
- Single-candidate but unverified fields: du_key, site_name
- Resolved by approved mapping (alternates rejected): existing_ti_pr_status, existing_tss_pr_status, tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00012|1027190858144623081|8530399820526021092 | Site Basic Info | Site Basic Info | customer site code`

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ0690241 | Network Planning | Microwave | Post MOCN TX SOW (LLD)`
- Alternate shortlist candidates:
  - score 80: `docata|ZDCSZ0656921 | Network Planning | Microwave | Plan TX SOW (HLD)`
    reason: Likely direct SOW planning field.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ640242 | Subcon Info | SubCon - TI | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01027586 | Network Planning | Microwave | Subcon - Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01027605 | Network Planning | Microwave | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS`
- Alternate shortlist candidates:
  - score 100: `docata|ZDCSZ00904401 | Acceptance | Microwave | PR TSS Status`
    reason: Exact TSS PR status field.
  - score 65: `docata|ZDCSZ00904399 | Acceptance | Microwave | PR TSS rectification status`
    reason: TSS rectification status field.

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI`
- Alternate shortlist candidates:
  - score 100: `docata|ZDCSZ00904402 | Acceptance | Microwave | PR TI Status`
    reason: Exact TI PR status field.
  - score 65: `docata|ZDCSZ00904400 | Acceptance | Microwave | PR TI rectification status`
    reason: TI rectification status field.


## jendela_tx_migration_pr_v1 (Jendela TX Migration)

- Source file: `A-P202202168750_D002-Jendela TX Migration-Migration Rollout (TX)-20260703160246.xlsx`
- Observed header hash: `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3`
- Missing required fields: None
- Competing candidate fields: site_name, subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key
- Resolved by approved mapping (alternates rejected): tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00012|4972593269368006257|4026888666764910245 | Site Basic Info | Site Basic Info | customer site code`

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ647216 | Installation | Wireless RAN | FE Site Name`
    reason: Alternate site-name style field.

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ00815532 | Planner | Microwave | Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ642123 | Planner | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ640242 | RPM | Wireless RAN | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969578 | Planner | Microwave | Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969579 | Planner | Microwave | Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641766 | PR Team | Wireless RAN | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641765 | PR team | Wireless RAN | Subcon PR - TI`


## zte_tx_mini_pr_v1 (ZTE TX MINI)

- Source file: `A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx`
- Observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Missing required fields: None
- Competing candidate fields: site_name, subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key
- Resolved by approved mapping (alternates rejected): site_code, tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `site|fix00012|8638668101234290847|2279585426760368522 | Site Basic Info | Site Basic Info | customer site code`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ01027674 | Network Planning | Microwave | FE Site ID`
    reason: Alternate site ID style field.

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ01092967 | Network Planning | Microwave | FE Site Name`
    reason: Alternate site-name style field.

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ01079155 | Network Planning | Microwave | Microwave Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ01079156 | Network Planning | Microwave | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00970184 | Network Planning | Microwave | Subcon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01087327 | Network Planning | Microwave | Subcon - Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01087326 | Network Planning | Microwave | Subcon - PR Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ01093667 | Network Planning | Microwave | MW Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ01093668 | Network Planning | Microwave | MW Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00959244 | Acceptance | Microwave | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ00959243 | Acceptance | Microwave | Subcon PR - TI`


## celcomdigi_bau_2023_pr_v1 (2023 Celcomdigi BAU)

- Source file: `A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx`
- Observed header hash: `b99438cd67273e01bba5e641a494f001295125e598abe090d3d215fedd7e2454`
- Missing required fields: None
- Competing candidate fields: subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key, site_name
- Resolved by approved mapping (alternates rejected): tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00012|8296022438223590261|3882899459299681347 | Site Basic Info | Site Basic Info | customer site code`

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ640242 | Subcon Info | SubCon - TI | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI`


## celcomdigi_bau_2024_pr_v1 (2024 Celcomdigi BAU)

- Source file: `A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx`
- Observed header hash: `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86`
- Missing required fields: None
- Competing candidate fields: subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key, site_name
- Resolved by approved mapping (alternates rejected): tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|fix00012|7278317398457076992|1090541706000906451 | Site Basic Info | Site Basic Info | customer site code`

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI`


## celcomdigi_usp_pr_v1 (Celcomdigi USP)

- Source file: `A-P202202168750_D002-Celcomdigi USP-Celcomdigi USP (TX)-20260703160234.xlsx`
- Observed header hash: `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf`
- Missing required fields: None
- Competing candidate fields: site_name, subcontractor_planning
- Single-candidate but unverified fields: antenna_size_fe, antenna_size_ne, du_key
- Resolved by approved mapping (alternates rejected): site_code, tx_sow_raw

### `site_code`

- Skill field: `site_id`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `site|fix00012|3765504705612341090|703232142435130905 | Site Basic Info | Site Basic Info | customer site code`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ00885478 | Installation | Wireless RAN | MCMC Site ID`
    reason: Alternate site ID style field.

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ647216 | Installation | Wireless RAN | FE Site Name`
    reason: Alternate site-name style field.
  - score 70: `docata|ZDCSZ00823578 | Installation | Wireless RAN | MCMC Site Name`
    reason: Alternate site-name style field.

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `RESOLVED_BY_APPROVED_MAPPING`
- Reason: Profile-selected source is human-approved; the remaining shortlist alternates were rejected by that recorded decision.
- Selected source: `docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ00767754 | Network Planning | Microwave | Post MOCN TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.
  - score 45: `docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning`
- Alternate shortlist candidates:
  - score 55: `docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning`
    reason: PR-oriented Planning field.

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969578 | Network Planning | Microwave | Antenna Size NE`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ00969579 | Network Planning | Microwave | Antenna Size FE`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `READY_IF_APPROVAL_EVIDENCE_EXISTS`
- Reason: Profile-selected source matches the shortlist and is already approved.
- Selected source: `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI`


## cd_consolidation_2023_decom_pr_v1 (CD consolidation 2023)

- Source file: `A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx`
- Observed header hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Missing required fields: existing_ti_pr_status, existing_tss_pr_status
- Competing candidate fields: region, site_code, site_name, tx_sow_raw
- Single-candidate but unverified fields: du_key, subcontractor_ti
- Resolved by approved mapping (alternates rejected): None

### `site_code`

- Skill field: `site_id`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00012|8359047522524182050|702960351133798763 | Site Basic Info | Site Basic Info | customer site code`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ0654995 | DiGi Site ID | DiGi Site ID | DiGi Site ID`
    reason: Alternate site ID style field.
  - score 70: `docata|ZDCSZ643256 | FE Info | FE Site ID | FE Site ID`
    reason: Alternate site ID style field.

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ647216 | Installation | FE Site Name | FE Site Name`
    reason: Alternate site-name style field.

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`
- Alternate shortlist candidates:
  - score 40: `docata|ZDCSZ00895041 | Installation | Wireless RAN | Sub Region`
    reason: Sub-region field; likely secondary.

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ640870 | TX | TX Final SOW (LLD) | TX SOW`
- Alternate shortlist candidates:
  - score 80: `docata|ZDCSZ0656921 | TX | TX Plan SOW (HLD) | Plan TX SOW`
    reason: Likely direct SOW planning field.
  - score 45: `docata|ZDCSZ642123 | TX | TX SOW Details | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ640242 | Subcon | SubCon - TI | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `REVIEW_REQUIRED_MISSING_CANDIDATE`
- Reason: Required profile field has no selected source candidate and no shortlist candidate.
- Selected source: `None`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `REVIEW_REQUIRED_MISSING_CANDIDATE`
- Reason: Required profile field has no selected source candidate and no shortlist candidate.
- Selected source: `None`


## cd_consolidation_2023_rollout_pr_v1 (CD consolidation 2023)

- Source file: `A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx`
- Observed header hash: `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`
- Missing required fields: existing_ti_pr_status, existing_tss_pr_status
- Competing candidate fields: region, site_code, tx_sow_raw
- Single-candidate but unverified fields: du_key, site_name, subcontractor_ti
- Resolved by approved mapping (alternates rejected): None

### `site_code`

- Skill field: `site_id`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|fix00012|8359047522524182050|8359047522524230651 | Site Basic Info | Site Basic Info | customer site code`
- Alternate shortlist candidates:
  - score 70: `docata|ZDCSZ0654995 | Installation | Wireless RAN | DiGi Site ID`
    reason: Alternate site ID style field.

### `site_name`

- Skill field: `site_name`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `site|fix00015 | Site Basic Info | Site Basic Info | customer site name`

### `du_key`

- Skill field: `du_code`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `du|du_code | Du | Du | du code`

### `region`

- Skill field: `region`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `site|region_name | Site Basic Info | Site Basic Info | region`
- Alternate shortlist candidates:
  - score 40: `docata|ZDCSZ00895041 | Installation | Wireless RAN | Sub Region`
    reason: Sub-region field; likely secondary.

### `tx_sow_raw`

- Skill field: `tx_sow`
- Review status: `REVIEW_REQUIRED_COMPETING_CANDIDATES`
- Reason: Profile-selected source has alternate shortlist candidates that still require four-layer confirmation.
- Selected source: `docata|ZDCSZ640870 | Installation | Wireless RAN | TX SOW`
- Alternate shortlist candidates:
  - score 45: `docata|ZDCSZ642123 | Installation | Wireless RAN | TX SOW Details`
    reason: SOW details field; likely evidence, not primary trigger.

### `subcontractor_ti`

- Skill field: `subcon_ti_team`
- Review status: `REVIEW_REQUIRED_UNVERIFIED_SINGLE_CANDIDATE`
- Reason: Only one shortlist-aligned source candidate exists, but it remains unverified in the DRAFT profile.
- Selected source: `docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI`

### `subcontractor_planning`

- Skill field: `subcon_planning`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `antenna_size_ne`

- Skill field: `antenna_size_ne`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `antenna_size_fe`

- Skill field: `antenna_size_fe`
- Review status: `NO_REVIEW_REQUIRED`
- Reason: Profile field is outside the current unresolved-skill review scope.
- Selected source: `None`

### `existing_tss_pr_status`

- Skill field: `existing_tss_pr`
- Review status: `REVIEW_REQUIRED_MISSING_CANDIDATE`
- Reason: Required profile field has no selected source candidate and no shortlist candidate.
- Selected source: `None`

### `existing_ti_pr_status`

- Skill field: `existing_ti_pr`
- Review status: `REVIEW_REQUIRED_MISSING_CANDIDATE`
- Reason: Required profile field has no selected source candidate and no shortlist candidate.
- Selected source: `None`

