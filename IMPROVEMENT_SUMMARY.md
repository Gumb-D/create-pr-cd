# MW Reroute/New Link Quantity Conflict Fix - Summary

## 📋 Overview

This improvement resolves a critical data consistency issue in the `create-pr-cd` skill where **duplicate PR model entries with conflicting quantities** caused incorrect ECC output for MW New Link / Reroute projects.

---

## 🎯 Problem Identified

### Root Cause
The PR model (`Info/input/pr_model.xlsx`) contains duplicate mandatory line items for the **"MW New Link / Reroute"** SOW:

| PBOM Code | Quantity | Status |
|-----------|----------|--------|
| 350000062773 | 1 | LOS Survey Option A |
| 350000062776 | 1 | LOS Survey Option B |
| 350000589343 | **1** | ❌ Conflict - appears twice |
| 350000589343 | **1.5** | ✅ Correct for Reroute |
| 350000589344 | **1** | ❌ Conflict - appears twice |
| 350000589344 | **1.5** | ✅ Correct for Reroute |

### Impact
When generating TSS PR ECC files, the original code matched **all mandatory items** based on SOW string similarity, causing:
- Same PBOM (e.g., 350000589343) to appear **multiple times** in output
- Different quantities for the same item (both 1.0 and 1.5 hop)
- Data inconsistency that violates PR/ECC business rules

---

## ✅ Solution Implemented

### Key Logic
Added **quantity filtering** and **LOS survey selection** in TSS model matching:

```python
# Determine if MW Reroute or New Link
if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
    upgrade_scope = str(row.get('TX Upgrade Scope', '')).strip().lower()
    is_mw_reroute = 'dismantle' in upgrade_scope

# Apply rules during matching
if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
    # 1. LOS Survey: select ONE based on site ID pattern
    if pbom in ['350000062773', '350000062776']:
        if is_mw_reroute:
            # Reroute: 350000062776 for _LOS sites, else 350000062773
            if pbom == '350000062776' and '_LOS' not in site_id.upper(): continue
            if pbom == '350000062773' and '_LOS' in site_id.upper(): continue
        else:
            # New Link: always 350000062773
            if pbom != '350000062773': continue
    
    # 2. Other SOW items: enforce consistent quantity
    elif pbom in ['350000589343', '350000589344']:
        expected_qty = 1.5 if is_mw_reroute else 1.0
        if qty != expected_qty: continue
```

### Decision Rules

| Scenario | TX Upgrade Scope Contains | Site ID Pattern | LOS Survey PBOM | 350000589343 Quantity |
|----------|---------------------------|-----------------|-----------------|----------------------|
| **MW New Link** | No "dismantle" | Any | 350000062773 | **1.0 hop** |
| **MW Reroute** | Yes ("dismantle") | NOT contains `_LOS` | 350000062773 | **1.5 hop** |
| **MW Reroute + LOS** | Yes ("dismantle") | Contains `_LOS` | 350000062776 | **1.5 hop** |

---

## 📝 Files Modified

### Production Code
| File | Change Type | Description |
|------|-------------|-------------|
| `scripts/generate_tss_pr_ecc.py` | **Modified** | Added MW Reroute/New Link detection and quantity filtering logic in TSS matching section (around line 1146) |

### Documentation
| File | Change Type | Description |
|------|-------------|-------------|
| `SKILL.md` | **Updated** | Section 8.1 (TSS Model Matching) now includes step-by-step quantity conflict resolution rules |
| `CHANGELOG.md` | **Created** | New changelog tracking all improvements |

### Testing & Utilities
| File | Change Type | Description |
|------|-------------|-------------|
| `test_fix.py` | **Created** | Unit test script validating all 4 scenarios |
| All check scripts (`check_*.py`, `find_reroute_all.py`) | **Updated** | Added path resolution logic to support moving to `scripts/` folder |
| **File Structure** | **Reorganized** | Moved all utility scripts from root to `scripts/` folder for better organization |

---

## 🧪 Validation & Testing

### Unit Tests (`test_fix.py`)
All four scenarios validated successfully:

```
✓ Test 1: MW New Link (no LOS) → Quantity: 1.0, Survey: 350000062773
✓ Test 2: MW New Link (with LOS) → Quantity: 1.0, Survey: 350000062773
✓ Test 3: MW Reroute (no LOS) → Quantity: 1.5, Survey: 350000062773
✓ Test 4: MW Reroute (with LOS) → Quantity: 1.5, Survey: 350000062776
✓ Verification: No duplicate PBOM entries in any scenario
```

### Manual Verification Commands
```bash
# From project root
python3 scripts/test_fix.py

# From scripts directory
cd scripts
python3 check_mw_reroute.py
python3 check_tss_quantities.py
```

### Expected Results
- **No duplicate PBOM** entries per site
- Correct **LOS Survey** selection based on `_LOS` pattern
- Consistent **quantity enforcement** (1.0 for New Link, 1.5 for Reroute)

---

## 🚀 Deployment Instructions

### Step 1: Replace Skill Folder
1. Extract `create-pr-cd-refined.zip` to your local skill directory
2. Overwrite existing files or create new installation

### Step 2: Verify File Structure
```
create-pr-cd/
├─ Info/input/              (PR model, site data, template, mapping)
├─ scripts/                 (All Python scripts now here)
│  ├─ generate_tss_pr_ecc.py    ← Main generator
│  ├─ test_fix.py              ← Unit tests
│  └─ check_*.py              ← Utility scripts
├─ output/                  (Generated ECC files)
├─ SKILL.md
├─ CHANGELOG.md
└─ README.md
```

### Step 3: Run Regression Test
```bash
cd /path/to/create-pr-cd
python3 scripts/test_fix.py
```

Expected output:
```
=== Verification ===
New Link no LOS: OK - no duplicate PBOMs
New Link with LOS: OK - no duplicate PBOMs
Reroute no LOS: OK - no duplicate PBOMs
Reroute with LOS: OK - no duplicate PBOMs
```

### Step 4: Production Run
```bash
# Generate TSS PR for all eligible sites
python3 scripts/generate_tss_pr_ecc.py --scope TSS --all-sites

# Or for specific sites
python3 scripts/generate_tss_pr_ecc.py --scope TSS --site-code A01073_AD,B00256
```

---

## 📊 Impact Assessment

| Aspect | Impact |
|--------|--------|
| **Scope Affected** | TSS only (TI, Planning, Operation Backoffice unchanged) |
| **Breaking Changes** | None - only filters existing PR model entries |
| **Data Consistency** | ✅ Eliminated duplicate PBOM entries |
| **Business Rules** | ✅ Now compliant with MW Reroute/New Link SOW requirements |
| **Backwards Compatibility** | ✅ Existing workflows unchanged; only output data corrected |
| **Performance** | ✅ Negligible - added simple conditional checks |

---

## 🔍 Change Verification Checklist

- [x] Code compiles without syntax errors
- [x] Unit tests pass for all 4 scenarios
- [x] No duplicate PBOMs appear in test output
- [x] LOS Survey selection logic verified
- [x] Quantity enforcement working (1.0 vs 1.5)
- [x] Path resolution tested from both root and `scripts/` directories
- [x] Documentation updated (SKILL.md)
- [x] Changelog created for version tracking
- [x] All utility scripts moved to `scripts/` folder
- [x] Path-independent execution verified

---

## 📚 Technical Notes

### SOW Detection Pattern
The actual SOW value in the data is **"MW New Link / Reroute"** (not standalone "MW NEW LINK" or "MW REROUTE"). The code checks:
```python
if 'MW NEW LINK' in sow_upper and '/' in sow_upper and 'REROUTE' in sow_upper:
```
This ensures we only apply special rules to that specific SOW, not to other MW SOWs like "MW Swap" or "MW Hardware Upgrade".

### TX Upgrade Scope Interpretation
- Contains **"dismantle"** (case-insensitive) → **MW Reroute**
- Does **not** contain "dismantle" → **MW New Link**

This interpretation is documented in the business requirements and is now clearly explained in `SKILL.md`.

### Path Resolution for Utility Scripts
All scripts (including test and check utilities) now support:
- Running from project root: `python3 scripts/check_mw_reroute.py`
- Running from scripts directory: `cd scripts && python3 check_mw_reroute.py`

Implemented via:
```python
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) == 'scripts':
    project_root = os.path.dirname(script_dir)
else:
    project_root = script_dir
```

---

## 📞 Support & Questions

For questions about this implementation:
1. Review `SKILL.md` for business rule details
2. Check `CHANGELOG.md` for version history
3. Run `test_fix.py` to see the logic in action
4. Examine `generate_tss_pr_ecc.py` around line 1146 for the exact implementation

---

**Status**: ✅ **Ready for Production**  
**Test Coverage**: 100% of defined scenarios  
**Risk Level**: Low (defensive filtering only)  
**Recommended Action**: Deploy to production after successful regression test