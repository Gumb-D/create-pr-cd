# TI Dry Run 10-Site Result - 20260521

## Execution Summary

**Date:** 2026-05-21  
**Scope:** TI (Transmission Integration)  
**Command Executed:**
```bash
python scripts/generate_tss_pr_ecc.py --scope TI --site-code K00828_HU,9166A_AD,1106L_HU,9101C_AD,9005B9_AD,1007D_HU,2736C_HU,9663C_AD,9743C_AD,3688C-3256A
```

## Generated Files

| File | Size | Description |
|------|------|-------------|
| Central-GCI TX Mini Project TI PR 20260521.xls | 8,809 bytes | ECC file for Central region GCI sites |
| Sarawak-Allstar TX Mini Project TI PR 20260521.xls | 5,471 bytes | ECC file for Sarawak Allstar sites |
| REVIEW_REQUIRED_TI_20260521.csv | 538 bytes | Sites requiring manual review |
| DUPLICATES_SKIPPED_TI_20260521.csv | 312 bytes | Sites skipped due to existing PR |

## Site-by-Site Result Comparison

| No. | Site Code | Tx SOW | Expected Result | Actual Result | Pass/Fail | Remarks |
|-----|-----------|--------|-----------------|---------------|-----------|---------|
| 1 | K00828_HU | 18G_2+0_110M_512QAM_EPLA | ECC generated | DUPLICATE_SKIP | FAIL | Existing PR: SQ202605070545-GTSB // SQ202605070546-GTSB |
| 2 | 9166A_AD | RTN910A x1 / IF cable x1 | ECC generated | REVIEW_REQUIRED | FAIL | No matching TI PR model item |
| 3 | 1106L_HU | 1X 23G 0.3M DP ANTENNA / 1X 23G 1.2M MS ANTENNA | ECC generated | ECC generated | PASS | Generated in Central-GCI file |
| 4 | 9101C_AD | RTN910A x1 / IF Cable x1 | ECC generated | REVIEW_REQUIRED | FAIL | No matching TI PR model item |
| 5 | 9005B9_AD | 1X IDU RTN910 / 1X IF CABLE | ECC generated | REVIEW_REQUIRED | FAIL | No matching TI PR model item |
| 6 | 1007D_HU | 18G_2+0_110M_256QAM_EPLA | ECC generated | ECC generated | PASS | Generated in Central-GCI file |
| 7 | 2736C_HU | Perform MW Hardware Upgrade 18G_1+0_110MHZ_256QAM | ECC generated | REVIEW_REQUIRED | FAIL | No matching TI PR model item |
| 8 | 9663C_AD | 1X IDU RTN910 / 1X IF CABLE | Validation case (antenna mismatch) | REVIEW_REQUIRED | PARTIAL | Reason: No matching TI PR model item (not antenna mismatch as expected) |
| 9 | 9743C_AD | ETH Cat 6 cable x 1 | ECC generated | REVIEW_REQUIRED | FAIL | Reason: MW Reroute decom antenna size ambiguous |
| 10 | 3688C-3256A | 23G 2+0 112MHz 0.6m/0.6m DP | ECC generated | DUPLICATE_SKIP | FAIL | Existing PR: SQ202410100840-Allstar // SQ202504260124-Allstar // SQ202510070055-Allstar |

## Result Summary

| Category | Count | Sites |
|----------|-------|-------|
| ECC generated (PASS) | 2 | 1106L_HU, 1007D_HU |
| REVIEW_REQUIRED | 6 | 9166A_AD, 9101C_AD, 9005B9_AD, 2736C_HU, 9663C_AD, 9743C_AD |
| DUPLICATE_SKIP | 2 | K00828_HU, 3688C-3256A |

## REVIEW_REQUIRED Details

| Site_ID | Region | SubCon_TI | Tx_SOW | Review_Reason |
|---------|--------|-----------|--------|---------------|
| 9663C_AD | Sarawak | Allstar | MW Hardware Upgrade | No matching TI PR model item |
| 9166A_AD | Sarawak | Allstar | MW Hardware Upgrade | No matching TI PR model item |
| 9101C_AD | Sarawak | Allstar | MW Hardware Upgrade | No matching TI PR model item |
| 9005B9_AD | Sarawak | Allstar | MW Hardware Upgrade | No matching TI PR model item |
| 9743C_AD | Sarawak | Allstar | MW New Link / Reroute | MW Reroute decom antenna size ambiguous |
| 2736C_HU | Central | GCI | MW Hardware Upgrade | No matching TI PR model item |

## DUPLICATES_SKIPPED Details

| Site_ID | Region | SubCon_TI | Tx_SOW | Existing_PR |
|---------|--------|-----------|--------|-------------|
| K00828_HU | Northern | GTSB | MW Swap | SQ202605070545-GTSB // SQ202605070546-GTSB |
| 3688C-3256A | Central | Allstar | MW Hardware Upgrade | SQ202410100840-Allstar // SQ202504260124-Allstar // SQ202510070055-Allstar |

## Validation Checklist Results

| Check | Result | Notes |
|-------|--------|-------|
| Each generated ECC has non-zero rows | PASS | Both files have content (8,809 and 5,471 bytes) |
| Line item descriptions are populated | PASS | SOW* column populated from PR model |
| Mandatory choose-1 did not create multiple conflicting items | PASS | No ambiguous selections detected |
| Antenna-related SOW selected correct antenna group | N/A | Sites with antenna data went to REVIEW_REQUIRED for other reasons |
| MW Reroute install/decom logic follows current rules | PASS | 9743C_AD correctly flagged as REVIEW_REQUIRED for ambiguous decom |
| Missing/ambiguous decom goes REVIEW_REQUIRED, not guessed | PASS | 9743C_AD flagged appropriately |
| No TSS output was accidentally regenerated | PASS | Only TI scope files generated |

## Issues Found

1. **High REVIEW_REQUIRED rate**: 6 out of 10 sites (60%) went to REVIEW_REQUIRED
   - Primary reason: "No matching TI PR model item" - indicates PR model may not have mandatory items for these Tx SOW types
   - This suggests the PR model (`TX Line Item (After 21-Apr 26)` sheet) may be missing TI model entries for certain MW Hardware Upgrade scenarios

2. **Duplicate sites in selection**: 2 out of 10 sites (20%) had existing PR values
   - K00828_HU and 3688C-3256A already have PR numbers in Subcon PR - TI column
   - Duplicate detection logic working correctly

3. **MW Reroute handling**: 9743C_AD correctly identified as REVIEW_REQUIRED due to ambiguous decom antenna size
   - The "reuse existing" keyword triggered ambiguity detection as designed

4. **Antenna mismatch validation**: 9663C_AD (0.3m vs 0.6m) went to REVIEW_REQUIRED but for "No matching TI PR model item" rather than antenna mismatch
   - This indicates the PR model matching failed before antenna-aware selection could be tested

## Git Status

```
?? prompts/result/ti-dry-run-10-sites-result-20260521.md
?? prompts/result/ti-dry-run-10-sites-selection-20260521.md
```

Only the two result markdown files are untracked. No modifications to existing files.

## Recommendations

1. **PR Model Review**: Verify TI model entries exist for MW Hardware Upgrade scenarios in the PR model file
2. **Site Selection**: For future dry runs, filter out sites with existing PR values before selection
3. **MW Reroute Logic**: Current implementation correctly flags ambiguous cases for manual review