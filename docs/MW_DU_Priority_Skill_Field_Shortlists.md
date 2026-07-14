# Priority DU Skill-Field Shortlists

Discovery-only shortlist of exact four-layer fingerprints for skill-scoped fields. These are review aids, not approved mappings.

## A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx

- `site_id`:
  - score 100: site|fix00012|4188808420049567786|2477626672974883536 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 100: docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 100: docata|ZDCSZ0657770 | Installation | Wireless RAN | SubCon - TSS Team
    reason: Exact TSS team field.
  - score 55: docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 100: docata|ZDCSZ0657771 | Installation | Wireless RAN | SubCon - TI Team
    reason: Exact TI team field.
  - score 55: docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 100: docata|ZDCSZ01027586 | Network Planning | Microwave | Subcon - Planning
    reason: Exact Planning subcontractor field.
  - score 55: docata|ZDCSZ01027605 | Network Planning | Microwave | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202211283695_D002-MW EOS Swap-MW EOS Swap Rollout-20260703160307.xlsx

- `site_id`:
  - score 100: site|fix00012|5440935430300168497|7476572371505372260 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
  - score 70: docata|ZDCSZ01027674 | Planner | Microwave | FE Site ID
    reason: Alternate site ID style field.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
  - score 70: docata|ZDCSZ01092967 | Network Planning | Microwave | FE Site Name
    reason: Alternate site-name style field.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 85: docata|ZDCSZ01100642 | Network Planning | Microwave | Microwave Tx SOW-1
    reason: Direct Microwave Tx SOW variant.
  - score 45: docata|ZDCSZ01079156 | Network Planning | Microwave | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ01093667 | Planner | Microwave | MW Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ01093668 | Planner | Microwave | MW Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ00970153 | Rollout | Microwave | Subcon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ00959244 | Commercial | Microwave | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ00970184 | Rollout | Microwave | Subcon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ00959243 | Commercial | Microwave | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 100: docata|ZDCSZ01087327 | Network Planning | Microwave | Subcon - Planning
    reason: Exact Planning subcontractor field.
  - score 55: docata|ZDCSZ01087326 | Network Planning | Microwave | Subcon - PR Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx

- `site_id`:
  - score 100: site|fix00012|1027190858144623081|8530399820526021092 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 80: docata|ZDCSZ0656921 | Network Planning | Microwave | Plan TX SOW (HLD)
    reason: Likely direct SOW planning field.
  - score 80: docata|ZDCSZ0690241 | Network Planning | Microwave | Post MOCN TX SOW (LLD)
    reason: Likely direct SOW planning field.
  - score 80: docata|ZDCSZ640870 | Network Planning | Microwave | TX SOW (LLD)
    reason: Likely direct SOW planning field.
- `antenna_size_ne`: no shortlist candidate
- `antenna_size_fe`: no shortlist candidate
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Subcon Info | SubCon - TSS | SubCon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Subcon Info | SubCon - TI | SubCon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 100: docata|ZDCSZ01027586 | Network Planning | Microwave | Subcon - Planning
    reason: Exact Planning subcontractor field.
  - score 55: docata|ZDCSZ01027605 | Network Planning | Microwave | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`:
  - score 100: docata|ZDCSZ00904401 | Acceptance | Microwave | PR TSS Status
    reason: Exact TSS PR status field.
  - score 65: docata|ZDCSZ00904399 | Acceptance | Microwave | PR TSS rectification status
    reason: TSS rectification status field.
- `existing_ti_pr`:
  - score 100: docata|ZDCSZ00904402 | Acceptance | Microwave | PR TI Status
    reason: Exact TI PR status field.
  - score 65: docata|ZDCSZ00904400 | Acceptance | Microwave | PR TI rectification status
    reason: TI rectification status field.

## A-P202202168750_D002-Jendela TX Migration-Migration Rollout (TX)-20260703160246.xlsx

- `site_id`:
  - score 100: site|fix00012|4972593269368006257|4026888666764910245 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
  - score 70: docata|ZDCSZ647216 | Installation | Wireless RAN | FE Site Name
    reason: Alternate site-name style field.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 100: docata|ZDCSZ00815532 | Planner | Microwave | Tx SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ642123 | Planner | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ00969578 | Planner | Microwave | Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ00969579 | Planner | Microwave | Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | RPM | SubCon - TSS | SubCon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ641766 | PR Team | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | RPM | Wireless RAN | SubCon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ641765 | PR team | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 85: docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning
    reason: Direct Planning subcontractor variant.
  - score 55: docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx

- `site_id`:
  - score 100: site|fix00012|8638668101234290847|2279585426760368522 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
  - score 70: docata|ZDCSZ01027674 | Network Planning | Microwave | FE Site ID
    reason: Alternate site ID style field.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
  - score 70: docata|ZDCSZ01092967 | Network Planning | Microwave | FE Site Name
    reason: Alternate site-name style field.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 85: docata|ZDCSZ01079155 | Network Planning | Microwave | Microwave Tx SOW
    reason: Direct Microwave Tx SOW variant.
  - score 45: docata|ZDCSZ01079156 | Network Planning | Microwave | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ01093667 | Network Planning | Microwave | MW Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ01093668 | Network Planning | Microwave | MW Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ00970153 | Network Planning | Microwave | Subcon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ00959244 | Acceptance | Microwave | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ00970184 | Network Planning | Microwave | Subcon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ00959243 | Acceptance | Microwave | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 100: docata|ZDCSZ01087327 | Network Planning | Microwave | Subcon - Planning
    reason: Exact Planning subcontractor field.
  - score 55: docata|ZDCSZ01087326 | Network Planning | Microwave | Subcon - PR Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx

- `site_id`:
  - score 100: site|fix00012|8296022438223590261|3882899459299681347 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 100: docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Subcon Info | SubCon - TSS | SubCon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Subcon Info | SubCon - TI | SubCon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 85: docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning
    reason: Direct Planning subcontractor variant.
  - score 55: docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx

- `site_id`:
  - score 100: site|fix00012|7278317398457076992|1090541706000906451 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 100: docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ00969578 | Network Planning | Microwave | MW Config Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ00969579 | Network Planning | Microwave | MW Config Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Installation | Wireless RAN | SubCon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 85: docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning
    reason: Direct Planning subcontractor variant.
  - score 55: docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-Celcomdigi USP-Celcomdigi USP (TX)-20260703160234.xlsx

- `site_id`:
  - score 100: site|fix00012|3765504705612341090|703232142435130905 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
  - score 70: docata|ZDCSZ00885478 | Installation | Wireless RAN | MCMC Site ID
    reason: Alternate site ID style field.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
  - score 70: docata|ZDCSZ647216 | Installation | Wireless RAN | FE Site Name
    reason: Alternate site-name style field.
  - score 70: docata|ZDCSZ00823578 | Installation | Wireless RAN | MCMC Site Name
    reason: Alternate site-name style field.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
- `tx_sow`:
  - score 100: docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ00767754 | Network Planning | Microwave | Post MOCN TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
  - score 45: docata|ZDCSZ642123 | TX Solution | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`:
  - score 100: docata|ZDCSZ00969578 | Network Planning | Microwave | Antenna Size NE
    reason: Direct NE antenna size field.
- `antenna_size_fe`:
  - score 100: docata|ZDCSZ00969579 | Network Planning | Microwave | Antenna Size FE
    reason: Direct FE antenna size field.
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Installation | Wireless RAN | SubCon - TSS
    reason: Direct TSS subcontractor field.
  - score 55: docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS
    reason: PR-oriented TSS field; likely duplicate-prevention or downstream support.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI
    reason: Direct TI subcontractor field.
  - score 55: docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI
    reason: PR-oriented TI field; likely duplicate-prevention or downstream support.
- `subcon_planning`:
  - score 85: docata|ZDCSZ01036640 | Installation | Wireless RAN | Subcon Planning
    reason: Direct Planning subcontractor variant.
  - score 55: docata|ZDCSZ01036639 | Installation | Wireless RAN | Subcon PR - Planning
    reason: PR-oriented Planning field.
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx

- `site_id`:
  - score 100: site|fix00012|8359047522524182050|702960351133798763 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
  - score 70: docata|ZDCSZ0654995 | DiGi Site ID | DiGi Site ID | DiGi Site ID
    reason: Alternate site ID style field.
  - score 70: docata|ZDCSZ643256 | FE Info | FE Site ID | FE Site ID
    reason: Alternate site ID style field.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
  - score 70: docata|ZDCSZ647216 | Installation | FE Site Name | FE Site Name
    reason: Alternate site-name style field.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
  - score 40: docata|ZDCSZ00895041 | Installation | Wireless RAN | Sub Region
    reason: Sub-region field; likely secondary.
- `tx_sow`:
  - score 100: docata|ZDCSZ640870 | TX | TX Final SOW (LLD) | TX SOW
    reason: Direct Tx SOW field.
  - score 80: docata|ZDCSZ0656921 | TX | TX Plan SOW (HLD) | Plan TX SOW
    reason: Likely direct SOW planning field.
  - score 45: docata|ZDCSZ642123 | TX | TX SOW Details | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`: no shortlist candidate
- `antenna_size_fe`: no shortlist candidate
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Subcon | SubCon - TSS | SubCon - TSS
    reason: Direct TSS subcontractor field.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Subcon | SubCon - TI | SubCon - TI
    reason: Direct TI subcontractor field.
- `subcon_planning`: no shortlist candidate
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate

## A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx

- `site_id`:
  - score 100: site|fix00012|8359047522524182050|8359047522524230651 | Site Basic Info | Site Basic Info | customer site code
    reason: Exact skill field match for Site ID.
  - score 70: docata|ZDCSZ0654995 | Installation | Wireless RAN | DiGi Site ID
    reason: Alternate site ID style field.
- `site_name`:
  - score 100: site|fix00015 | Site Basic Info | Site Basic Info | customer site name
    reason: Exact skill field match for Site Name.
- `du_code`:
  - score 100: du|du_code | Du | Du | du code
    reason: Exact skill field match for DU Code.
- `region`:
  - score 100: site|region_name | Site Basic Info | Site Basic Info | region
    reason: Direct Site Basic Info region field.
  - score 40: docata|ZDCSZ00895041 | Installation | Wireless RAN | Sub Region
    reason: Sub-region field; likely secondary.
- `tx_sow`:
  - score 100: docata|ZDCSZ640870 | Installation | Wireless RAN | TX SOW
    reason: Direct Tx SOW field.
  - score 45: docata|ZDCSZ642123 | Installation | Wireless RAN | TX SOW Details
    reason: SOW details field; likely evidence, not primary trigger.
- `antenna_size_ne`: no shortlist candidate
- `antenna_size_fe`: no shortlist candidate
- `subcon_tss_team`:
  - score 85: docata|ZDCSZ640307 | Installation | Wireless RAN | SubCon - TSS
    reason: Direct TSS subcontractor field.
- `subcon_ti_team`:
  - score 85: docata|ZDCSZ640242 | Installation | Wireless RAN | SubCon - TI
    reason: Direct TI subcontractor field.
- `subcon_planning`: no shortlist candidate
- `tx_integrated_actual_end_date`: no shortlist candidate
- `existing_tss_pr`: no shortlist candidate
- `existing_ti_pr`: no shortlist candidate
