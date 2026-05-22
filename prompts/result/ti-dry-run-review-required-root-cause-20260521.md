# TI Dry Run REVIEW_REQUIRED Root Cause Analysis - 20260521

## Overview

This document analyzes the root cause for each of the 6 REVIEW_REQUIRED sites from the TI dry run executed on 2026-05-21.

**Analysis Date:** 2026-05-21  
**Scope:** 6 REVIEW_REQUIRED sites only

---

## Site-by-Site Analysis

### 1. Site: 9166A_AD

| Field | Value |
|-------|-------|
| **Region** | Sarawak |
| **SubCon - TI Team** | Allstar |
| **Tx SOW** | RTN910A x1 / IF cable x1 |
| **Tx SOW Details** | MW Hardware Upgrade at Q00042. Site Impacted: 9166A |
| **NE SOW Details** | Reuse existing MW IDU, ODU and antenna. Config with 23G_1+0_112M |
| **FE SOW Details** | Install new RTN910A. Reuse existing 23G_0.6M antenna. Reuse existing ODU 23G. Lay new IF cable |
| **MW Config Antenna Size NE** | 0.6 |
| **MW Config Antenna Size FE** | 0.6 |
| **BOQ Configuration** | XMC |
| **REVIEW_REQUIRED Reason** | No matching TI PR model item |

**Nearest Matching PR Model Item:**
- PR Model has "MW Hardware Upgrade" entries (lines 28-31) but these are under TSS Model section, not TI Model section
- TI Model section (line 35+) does NOT have a "MW Hardware Upgrade" category
- Closest TI Model items are "Swap ODU (with site survey)" or "Swap ODU (w/o site survey)" which require antenna swap context

**Root Cause Classification:** PR model gap

**Recommended Action:** Add "MW Hardware Upgrade" category to TI Model section in PR model file, or map "MW Hardware Upgrade" Tx SOW to existing TI Model category (e.g., "Swap ODU")

**Script Change Required:** No

---

### 2. Site: 9101C_AD

| Field | Value |
|-------|-------|
| **Region** | Sarawak |
| **SubCon - TI Team** | Allstar |
| **Tx SOW** | RTN910A x1 / IF Cable x1 |
| **Tx SOW Details** | MW Hardware Upgrade at Q00042. Site Impacted: 9101C |
| **NE SOW Details** | Reuse existing MW IDU, ODU and antenna. Config with 23G_1+0_112M |
| **FE SOW Details** | Install new RTN910A. Reuse existing 23G_0.6M antenna. Reuse existing ODU 23G. Lay new IF cable |
| **MW Config Antenna Size NE** | 0.6 |
| **MW Config Antenna Size FE** | 0.6 |
| **BOQ Configuration** | XMC |
| **REVIEW_REQUIRED Reason** | No matching TI PR model item |

**Nearest Matching PR Model Item:**
- Same as 9166A_AD - "MW Hardware Upgrade" exists in TSS Model but NOT in TI Model section

**Root Cause Classification:** PR model gap

**Recommended Action:** Same as 9166A_AD

**Script Change Required:** No

---

### 3. Site: 9005B9_AD

| Field | Value |
|-------|-------|
| **Region** | Sarawak |
| **SubCon - TI Team** | Allstar |
| **Tx SOW** | 1X IDU RTN910 / 1X IF CABLE (SUITABLE LENGTH) |
| **Tx SOW Details** | MW HARDWARE UPGRADE TO CHANGE ROUTE FROM XD LINK 9005B9-9165A TO XC LINK 9005B9-Q00042 |
| **NE SOW Details** | Install new IDU RTN910A at Q00042. Reuse existing 23G 0.6M antenna. Reuse existing ODU 23G MAC 112MHZ SUB A |
| **FE SOW Details** | (FE is Q00042 - same as NE) |
| **MW Config Antenna Size NE** | 0.6 |
| **MW Config Antenna Size FE** | 0.6 |
| **BOQ Configuration** | XMC3 |
| **REVIEW_REQUIRED Reason** | No matching TI PR model item |

**Nearest Matching PR Model Item:**
- Same issue - "MW Hardware Upgrade" not defined in TI Model section

**Root Cause Classification:** PR model gap

**Recommended Action:** Same as 9166A_AD

**Script Change Required:** No

---

### 4. Site: 2736C_HU

| Field | Value |
|-------|-------|
| **Region** | Central (Selangor) |
| **SubCon - TI Team** | GCI |
| **Tx SOW** | Perform MW Hardware Upgrade 18G_1+0_110MHZ_256QAM |
| **Tx SOW Details** | Perform MW Hardware Upgrade 18G_1+0_110MHZ_256QAM. Site Impacted: 2736C |
| **NE SOW Details** | Re-use existing 18G_SP_0.6M(MAC) x1. Decom existing ODU XMC-3 and replace with new XMC_3E |
| **FE SOW Details** | Re-use existing 18G_SP_0.6M(MAC) x1. Decom existing ODU XMC-3 and replace with new XMC_3E |
| **MW Config Antenna Size NE** | Re-use existing 18G_SP_0.6M(MAC) x1 |
| **MW Config Antenna Size FE** | Re-use existing 18G_SP_0.6M(MAC) x1 |
| **BOQ Configuration** | XMC_3E |
| **REVIEW_REQUIRED Reason** | No matching TI PR model item |

**Nearest Matching PR Model Item:**
- Same issue - "MW Hardware Upgrade" not defined in TI Model section
- Note: This site has clear antenna size (0.6m) and clear ODU upgrade (XMC-3 to XMC_3E)

**Root Cause Classification:** PR model gap

**Recommended Action:** Same as 9166A_AD

**Script Change Required:** No

---

### 5. Site: 9663C_AD

| Field | Value |
|-------|-------|
| **Region** | Sarawak |
| **SubCon - TI Team** | Allstar |
| **Tx SOW** | 1X IDU RTN910 / 1X IF CABLE (SUITABLE LENGTH) |
| **Tx SOW Details** | MW HARDWARE UPGRADE TO CHANGE ROUTE FROM XD LINK 9663C-9165A TO XC LINK 9663C-Q00042 |
| **NE SOW Details** | Install new IDU RTN910A at Q00042. Reuse existing 23G 0.6M antenna. Reuse existing ODU 23G MAC 112MHZ SUB A |
| **FE SOW Details** | (FE is Q00042 - same as NE) |
| **MW Config Antenna Size NE** | 0.3 |
| **MW Config Antenna Size FE** | 0.6 |
| **BOQ Configuration** | XMC3 |
| **REVIEW_REQUIRED Reason** | No matching TI PR model item |

**Nearest Matching PR Model Item:**
- Same issue - "MW Hardware Upgrade" not defined in TI Model section
- Antenna sizes differ (0.3m vs 0.6m) but this is secondary since PR model matching failed first

**Root Cause Classification:** PR model gap

**Recommended Action:** Same as 9166A_AD

**Script Change Required:** No

---

### 6. Site: 9743C_AD

| Field | Value |
|-------|-------|
| **Region** | Sarawak |
| **SubCon - TI Team** | Allstar |
| **Tx SOW** | ETH Cat 6 cable x 1 |
| **Tx SOW Details** | Existing link 9743C change FE routing due to site burned |
| **NE SOW Details** | Reuse existing MW equipment (IDU, ODU and ant). Remain MW config 15G_2+0_28M |
| **FE SOW Details** | Reuse existing 9663C_RTN02 to RTN910A |
| **MW Config Antenna Size NE** | 0.6 |
| **MW Config Antenna Size FE** | 0.6 |
| **BOQ Configuration** | XMC |
| **REVIEW_REQUIRED Reason** | MW Reroute decom antenna size ambiguous |

**Nearest Matching PR Model Item:**
- This site IS classified as MW Reroute (Tx SOW Details mentions "change FE routing")
- TI Model has "MW Reroute" entries (lines 194-266)
- Matching reached MW Reroute logic but flagged for ambiguous decom antenna size

**Root Cause Classification:** Expected MW Reroute safety block

**Analysis:**
- The TX SOW Details states "Reuse existing MW equipment" and "Remain MW config"
- The word "reuse" triggers the "reuse existing" ambiguity detection in the script
- This is CORRECT behavior - the script should flag this for manual review because:
  - It's unclear if decom is actually needed when equipment is being reused
  - The site was burned, so equipment status may be uncertain

**Recommended Action:** Manual business review required to clarify:
- Is decom actually needed for this reroute?
- Is the existing equipment functional after the fire incident?

**Script Change Required:** No - this is working as designed

---

## Root Cause Summary Table

| Site Code | Tx SOW | Root Cause Classification | Script Change Required |
|-----------|--------|---------------------------|----------------------|
| 9166A_AD | RTN910A x1 / IF cable x1 | PR model gap | No |
| 9101C_AD | RTN910A x1 / IF Cable x1 | PR model gap | No |
| 9005B9_AD | 1X IDU RTN910 / 1X IF CABLE | PR model gap | No |
| 2736C_HU | MW Hardware Upgrade 18G_1+0 | PR model gap | No |
| 9663C_AD | 1X IDU RTN910 / 1X IF CABLE | PR model gap | No |
| 9743C_AD | ETH Cat 6 cable x 1 | Expected MW Reroute safety block | No |

## Root Cause Summary by Category

| Category | Count | Sites |
|----------|-------|-------|
| PR model gap | 5 | 9166A_AD, 9101C_AD, 9005B9_AD, 2736C_HU, 9663C_AD |
| Parser gap | 0 | None |
| Business rule/manual review | 0 | None |
| Expected MW Reroute safety block | 1 | 9743C_AD |

## Key Finding

**5 out of 6 REVIEW_REQUIRED sites (83%) are due to PR model gap:**

The PR model file (`Info/input/pr_model.xlsx`, sheet `TX Line Item (After 21-Apr 26)`) has:
- "MW Hardware Upgrade" defined in TSS Model section (lines 28-31)
- NO "MW Hardware Upgrade" category in TI Model section (line 35+)

The TI Model section currently includes:
- MW BBU/IDU Patching
- Swap ODU (with site survey)
- IPRAN Port Upgrade/Re-Engineering
- MW IDU Relocation
- MW Parallel Link
- MW Reroute
- MW New Link
- MW Swap
- Swap ODU (w/o site survey)
- Swap IDU (w/o site survey)
- MW Decom

**Missing:** "MW Hardware Upgrade" as a distinct TI Model category.

## Whether Any Script Change Is Truly Required

**No script changes required.**

All 6 REVIEW_REQUIRED classifications are correct behavior:
- 5 sites correctly identified as having no matching TI PR model item
- 1 site (9743C_AD) correctly flagged for MW Reroute decom ambiguity

The fix required is in the **PR model data**, not the script logic.

## Git Status

```
?? prompts/result/ti-dry-run-10-sites-result-20260521.md
?? prompts/result/ti-dry-run-10-sites-selection-20260521.md
?? prompts/result/ti-dry-run-review-required-root-cause-20260521.md
```

Only the three result markdown files are untracked. No modifications to existing scripts, input files, or ECC template.

---

## Recommendations

1. **Business Decision Required:** Determine if "MW Hardware Upgrade" should be added as a TI Model category in the PR model file, OR if such sites should be mapped to an existing TI Model category (e.g., "Swap ODU").

2. **Data Quality:** Review the PR model completeness for TI scope to ensure all common Tx SOW types have corresponding TI Model entries.

3. **No Script Changes:** The current script logic is functioning correctly - it properly identifies unmatched sites and flags them for review.