# TI Dry Run 10-Site Selection - 20260521

## Overview

This document records the 10 sites selected for TI (Transmission Integration) PR ECC dry run verification.

**Date:** 2026-05-21  
**Purpose:** Verify TI PR generation with diverse Tx SOW types, antenna configurations, and subcontractors.

## Selection Criteria

Sites were selected based on:
- SubCon - TI Team has value
- Subcon PR - TI is blank (no existing PR)
- Tx SOW has value
- Diverse Tx SOW categories (MW Swap, MW Hardware Upgrade, MW Reroute)
- Different antenna size configurations
- Multiple regions and subcontractors

## Selected Sites

| No. | Site Code | Region | SubCon - TI Team | Subcon PR - TI | Tx SOW | MW Config Antenna Size NE | MW Config Antenna Size FE | BOQ Configuration | Reason Selected | Expected Result |
|-----|-----------|--------|------------------|----------------|--------|--------------------------|--------------------------|-------------------|-----------------|-----------------|
| 1 | K00828_HU | Northern (Kedah) | GTSB | (blank) | 18G_2+0_110M_512QAM_EPLA | 18G_1.2M(MAC)+OMT x1 | 18G_1.2M(MAC)+OMT x1 | XMC_3E | MW Swap with clear antenna size (1.2m), complete NE/FE details | ECC generated |
| 2 | 9166A_AD | Sarawak | Allstar | (blank) | RTN910A x1 / IF cable x1 | 0.6 | 0.6 | XMC | MW Hardware Upgrade, matching antenna sizes (0.6m) | ECC generated |
| 3 | 1106L_HU | Central (Selangor) | GCI | (blank) | 1X 23G 0.3M DP ANTENNA / 1X 23G 1.2M MS ANTENNA / 1x ODU 23G XMC3 SUB A HI / 1x ODU 23G XMC3 SUB A LO / 1x ODU 23G XMC3 SUB B HI / 1x ODU 23G XMC3 SUB B LO | 0.3 | 1.2 | XMC3 | MW Swap with different NE/FE antenna sizes (0.3m vs 1.2m) - tests larger size selection | ECC generated |
| 4 | 9101C_AD | Sarawak | Allstar | (blank) | RTN910A x1 / IF Cable x1 | 0.6 | 0.6 | XMC | MW Hardware Upgrade, matching antenna sizes (0.6m) | ECC generated |
| 5 | 9005B9_AD | Sarawak | Allstar | (blank) | 1X IDU RTN910 / 1X IF CABLE (SUITABLE LENGTH) | 0.6 | 0.6 | XMC3 | MW Hardware Upgrade with route change, clear antenna size | ECC generated |
| 6 | 1007D_HU | Central (Selangor) | GCI | (blank) | 18G_2+0_110M_256QAM_EPLA | 18G_0.6M(MDD) x1 | 18G_0.6M(MDD) x1 | XMC_5D Pro | MW Swap with specific XMC_5D Pro BOQ, matching antenna sizes | ECC generated |
| 7 | 2736C_HU | Central (Selangor) | GCI | (blank) | Perform MW Hardware Upgrade 18G_1+0_110MHZ_256QAM | Re-use existing 18G_SP_0.6M(MAC) x1 | Re-use existing 18G_SP_0.6M(MAC) x1 | XMC_3E | MW Hardware Upgrade with reuse existing antenna, clear 0.6m size | ECC generated |
| 8 | 9663C_AD | Sarawak | Allstar | (blank) | 1X IDU RTN910 / 1X IF CABLE (SUITABLE LENGTH) | 0.3 | 0.6 | XMC3 | Validation case for antenna-aware selection (0.3m vs 0.6m mismatch) | Validation case |
| 9 | 9743C_AD | Sarawak | Allstar | (blank) | ETH Cat 6 cable x 1 | 0.6 | 0.6 | XMC | MW New Link / Reroute due to site burned - has MW context in TX SOW Details | ECC generated |
| 10 | 3688C-3256A | Central (Selangor) | Allstar | (blank) | 23G 2+0 112MHz 0.6m/0.6m DP | (from BOQ: 0.6m class) | (from BOQ: 0.6m class) | ISM8 card | MW Hardware Upgrade from 1+0 to 2+0 | ECC generated |

## Tx SOW Category Coverage

| Tx SOW Category (exact wording pattern) | Count | Sites |
|-----------------------------------------|-------|-------|
| MW Swap | 3 | K00828_HU, 1106L_HU, 1007D_HU |
| MW Hardware Upgrade | 5 | 9166A_AD, 9101C_AD, 9005B9_AD, 2736C_HU, 3688C-3256A |
| MW New Link / Reroute | 1 | 9743C_AD |
| Antenna/ODU specification | 1 | 9663C_AD |

## Region Coverage

| Region | Count | Sites |
|--------|-------|-------|
| Northern (Kedah) | 1 | K00828_HU |
| Central (Selangor) | 3 | 1106L_HU, 1007D_HU, 2736C_HU, 3688C-3256A |
| Sarawak | 6 | 9166A_AD, 9101C_AD, 9005B9_AD, 9663C_AD, 9743C_AD |

## Subcontractor Coverage

| Subcontractor | Count | Sites |
|---------------|-------|-------|
| GTSB | 1 | K00828_HU |
| GCI | 3 | 1106L_HU, 1007D_HU, 2736C_HU |
| Allstar | 6 | 9166A_AD, 9101C_AD, 9005B9_AD, 9663C_AD, 9743C_AD, 3688C-3256A |

## Antenna Size Diversity

| Antenna Configuration | Count | Sites |
|----------------------|-------|-------|
| 0.3m / 0.6m (mismatch) | 1 | 9663C_AD |
| 0.3m / 1.2m (mismatch) | 1 | 1106L_HU |
| 0.6m / 0.6m (matching) | 5 | 9166A_AD, 9101C_AD, 9005B9_AD, 9743C_AD, 3688C-3256A |
| 1.2m / 1.2m (matching) | 1 | K00828_HU |
| BOQ-derived | 2 | 1007D_HU (0.6m MDD), 2736C_HU (0.6m SP) |

## Execution Command

```bash
python scripts/generate_tss_pr_ecc.py --scope TI --site-code K00828_HU,9166A_AD,1106L_HU,9101C_AD,9005B9_AD,1007D_HU,2736C_HU,9663C_AD,9743C_AD,3688C-3256A
```

## Validation Checklist

After execution, verify:
- [ ] Each generated ECC has non-zero rows
- [ ] Line item descriptions are populated
- [ ] Mandatory choose-1 did not create multiple conflicting items
- [ ] Antenna-related SOW selected correct antenna group
- [ ] MW Reroute install/decom logic follows current rules
- [ ] Missing/ambiguous decom goes REVIEW_REQUIRED, not guessed
- [ ] No TSS output was accidentally regenerated