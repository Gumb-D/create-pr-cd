# TI Dry Run ECC Output Validity Review - 20260521

## Overview

This document analyzes the validity of generated TI ECC output files from the dry run executed on 2026-05-21.

**Analysis Date:** 2026-05-22  
**Scope:** Generated ECC files and focus sites (1106L_HU, 1007D_HU, 9743C_AD)

---

## Generated ECC Files Analysis

### Central-GCI TX Mini Project TI PR 20260522.xlsx

| Metric | Value |
|--------|-------|
| Total Rows | 46 |
| Unique Sites | 4 (3804A_HU, 1106L_HU, 1007D_HU, 1401B_AD) |

**Site Breakdown:**

| Site Code | Row Count | Remarks | Classification |
|-----------|-----------|---------|----------------|
| 1007D_HU | 43 | REVIEW_REQUIRED (all rows) | INVALID_ECC |
| 1106L_HU | 1 | TI antenna sizes differ - using larger size for matching | VALID_ECC |
| 1401B_AD | 1 | None | VALID_ECC (additional site) |
| 3804A_HU | 1 | None | VALID_ECC (additional site) |

### Sarawak-Allstar TX Mini Project TI PR 20260522.xlsx

| Metric | Value |
|--------|-------|
| Total Rows | 3 |
| Unique Sites | 3 (9157B_IPR, 9419B_IPR, 9743C_AD) |

**Site Breakdown:**

| Site Code | Row Count | Remarks | Classification |
|-----------|-----------|---------|----------------|
| 9743C_AD | 1 | REVIEW_REQUIRED | PARTIAL_ECC_WITH_REVIEW |
| 9157B_IPR | 1 | Missing TI antenna size - review required | NEEDS_MODEL_FIX |
| 9419B_IPR | 1 | Missing TI antenna size - review required | NEEDS_MODEL_FIX |

---

## Focus Sites Detailed Analysis

### 1. Site: 1007D_HU

| Field | Value |
|-------|-------|
| **Tx SOW** | 18G_2+0_110M_256QAM_EPLA |
| **Expected Result** | ECC generated |
| **Actual Result** | 43 rows generated, ALL with REVIEW_REQUIRED |
| **Classification** | INVALID_ECC |

**Root Cause:**
The 43 rows are all "29 choose 1" mandatory inland transportation options. This indicates that:
1. The site matched MW Swap category correctly
2. However, ALL 29 transportation options were included instead of selecting ONE based on region
3. All rows have `Remarks=REVIEW_REQUIRED`, suggesting the script flagged this as needing review

**Analysis of 43 rows:**
- Rows 1-29: Inland transportation "29 choose 1 (Mandatory)" options
- Rows 30-33: "4 choose 1 (Mandatory)" Swap MW Link antenna options
- Additional rows: Optional items

**Issue:** The "choose 1" selection logic did NOT filter to a single option. Instead, all options were included with REVIEW_REQUIRED flag.

**Verdict:** This is NOT valid ECC output. The file should not have been generated, or should contain only the selected items after choose-1 filtering.

---

### 2. Site: 1106L_HU

| Field | Value |
|-------|-------|
| **Tx SOW** | 1X 23G 0.3M DP ANTENNA / 1X 23G 1.2M MS ANTENNA |
| **MW Config Antenna NE** | 0.3 |
| **MW Config Antenna FE** | 1.2 |
| **Expected Result** | ECC generated |
| **Actual Result** | 1 row generated |
| **Classification** | VALID_ECC |

**Generated Row Details:**
- PBOM: 350001095406
- SOW: Swap - MW Link (0.9/1.2m, 2 antenna) for C&D Project
- Quantity: 1
- Remarks: "TI antenna sizes differ - using larger size for matching"

**Analysis:**
- Antenna-aware matching worked correctly
- System chose larger size (1.2m) and matched to 0.9/1.2m category
- Single row generated as expected
- Remark correctly notes the antenna size mismatch handling

**Verdict:** VALID_ECC - This is correct behavior.

---

### 3. Site: 9743C_AD

| Field | Value |
|-------|-------|
| **Tx SOW** | ETH Cat 6 cable x 1 |
| **Tx SOW Details** | Existing link 9743C change FE routing due to site burned |
| **Expected Result** | ECC generated |
| **Actual Result** | 1 row in ECC + 1 entry in REVIEW_REQUIRED |
| **Classification** | PARTIAL_ECC_WITH_REVIEW |

**Generated ECC Row:**
- PBOM: 350001095409
- SOW: New - MW Link (0.3/0.6m, 2 antenna) for C&D Project
- Quantity: 1
- Remarks: REVIEW_REQUIRED

**REVIEW_REQUIRED Entry:**
- Reason: "MW Reroute decom antenna size ambiguous"

**Analysis:**
- The site was classified as MW Reroute (due to "change FE routing" context)
- Install item was matched successfully (New - MW Link)
- Decom item was NOT matched due to ambiguous "reuse existing" wording
- The ECC file was generated WITH the install item
- REVIEW_REQUIRED was also created for the ambiguous decom

**Verdict:** PARTIAL_ECC_WITH_REVIEW - The system correctly:
1. Generated ECC for the install portion
2. Flagged the decom ambiguity for manual review
3. Did NOT guess the decom item (correct safety behavior)

---

## Site Classification Summary

| Site Code | Classification | Reason |
|-----------|---------------|--------|
| 1106L_HU | VALID_ECC | Correct antenna-aware matching, single row |
| 1007D_HU | INVALID_ECC | 43 rows with REVIEW_REQUIRED - choose-1 logic failed |
| 9743C_AD | PARTIAL_ECC_WITH_REVIEW | Install generated, decom flagged for review (correct) |
| 1401B_AD | VALID_ECC | Additional site, valid output |
| 3804A_HU | VALID_ECC | Additional site, valid output |
| 9157B_IPR | NEEDS_MODEL_FIX | Missing TI antenna size |
| 9419B_IPR | NEEDS_MODEL_FIX | Missing TI antenna size |

---

## Key Findings

### 1. Why 1007D_HU Generated 43 Rows

**Answer:** The 43 rows represent ALL "choose 1" mandatory options being included instead of filtered to a single selection.

- 29 rows: Inland transportation options ("29 choose 1")
- 4 rows: MW Link antenna options ("4 choose 1")
- ~10 rows: Optional items

**This is a CHOOSE-1 LOGIC GAP**, not a data issue. The script's `filter_choose_group_items` function identified the groups but did NOT filter to a single item - it included ALL options with REVIEW_REQUIRED flag.

**Whether 1007D_HU rows are valid PR items:** NO. These are not valid PR items because:
1. All rows have `Remarks=REVIEW_REQUIRED`
2. Choose-1 logic should have selected ONE option per group
3. The output should have been flagged as REVIEW_REQUIRED without generating an ECC file

### 2. Whether 1106L_HU ECC Output is Valid

**Answer:** YES. The 1106L_HU output is valid:
- Single row generated
- Correct antenna category selected (0.9/1.2m for 0.3m/1.2m input)
- Appropriate remark added about antenna size difference
- No choose-1 ambiguity (MW Swap with clear antenna match)

### 3. Whether 9743C_AD Should Be PARTIAL

**Answer:** YES. 9743C_AD is correctly classified as PARTIAL_ECC_WITH_REVIEW:
- ECC generated for install portion (correct)
- REVIEW_REQUIRED for ambiguous decom (correct)
- This is the EXPECTED behavior for MW Reroute with unclear decom scope

---

## TI Creation Success Assessment

### Can TI Creation Be Accepted as Successful?

**PARTIALLY SUCCESSFUL** with caveats:

| Aspect | Status | Notes |
|--------|--------|-------|
| Antenna-aware matching | PASS | 1106L_HU correctly handled |
| MW Reroute safety block | PASS | 9743C_AD correctly flagged |
| Choose-1 logic | FAIL | 1007D_HU included all options |
| Duplicate prevention | PASS | Working correctly |
| REVIEW_REQUIRED framework | PASS | Items correctly flagged |

### Specific Model/Data Gaps

1. **PR Model Gap:** "MW Hardware Upgrade" category missing from TI Model section
   - Affects: 9166A_AD, 9101C_AD, 9005B9_AD, 2736C_HU, 9663C_AD
   
2. **Choose-1 Logic Gap:** Script includes ALL options instead of filtering
   - Affects: 1007D_HU and potentially other sites with choose-1 groups

3. **Antenna Data Gap:** Some sites missing TI antenna size data
   - Affects: 9157B_IPR, 9419B_IPR

### Whether Any Script Change Is Needed

**YES - Script change needed for choose-1 logic:**

The current implementation includes ALL "choose 1" options with REVIEW_REQUIRED flag instead of:
1. Selecting ONE option based on matching criteria
2. Only flagging as REVIEW_REQUIRED if ambiguous/no match

**Recommended fix:** Modify `filter_choose_group_items` to:
- Return single best match when possible
- Only return multiple items (and set REVIEW_REQUIRED) when truly ambiguous

**NO script change needed for:**
- Antenna-aware matching (working correctly)
- MW Reroute handling (working correctly)
- Duplicate prevention (working correctly)

---

## Git Status

```
 M scripts/generate_tss_pr_ecc.py
?? prompts/result/ti-dry-run-10-sites-result-20260521.md
?? prompts/result/ti-dry-run-10-sites-selection-20260521.md
?? prompts/result/ti-dry-run-ecc-output-validity-review-20260521.md
?? prompts/result/ti-dry-run-review-required-root-cause-20260521.md
?? scripts/analyze_ecc_output.py
```

Note: `scripts/generate_tss_pr_ecc.py` shows as modified (from earlier analysis script edit). The result markdown files and analysis script are untracked. No input files, ECC template, or README/skill files were modified.

---

## Recommendations

1. **Fix Choose-1 Logic:** Update `filter_choose_group_items` to select single best match instead of including all options

2. **Add MW Hardware Upgrade to TI Model:** Business decision needed on whether to add this category or map to existing "Swap ODU"

3. **Improve Antenna Data Quality:** Ensure sites have complete MW Config Antenna Size NE/FE data

4. **Keep Current REVIEW_REQUIRED Behavior:** The safety block for ambiguous cases is working as designed