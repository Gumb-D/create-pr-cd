# Changelog

## 2025-06-24 - MW Reroute/New Link Quantity Conflict Fix

### Changes Made

#### Code Changes
- **File**: `scripts/generate_tss_pr_ecc.py`
- **Section**: TSS model matching logic (around line 1146)
- **Improvement**: Added quantity conflict resolution for MW New Link / Reroute SOW items

#### What was fixed:
1. **Eliminated duplicate PBOM entries** - Previously, PBOMs 350000589343 and 350000589344 could appear multiple times with different quantities (1 hop and 1.5 hop) in the same output, causing data inconsistency.

2. **Implemented correct LOS Survey selection**:
   - **MW Reroute** (with "dismantle" in TX Upgrade Scope):
     - Site ID contains `_LOS` → select 350000062776
     - Site ID does NOT contain `_LOS` → select 350000062773
   - **MW New Link** (without "dismantle"):
     - Always select 350000062773 (regardless of _LOS)

3. **Enforced consistent quantities**:
   - For MW Reroute: 350000589343/344 must have quantity **1.5 hop** only
   - For MW New Link: 350000589343/344 must have quantity **1 hop** only

#### Documentation Updates
- **File**: `SKILL.md`
- **Section**: 8.1 TSS Model Matching
- Added explicit "Quantity Conflict Resolution for MW New Link / Reroute" step explaining how duplicate PR model entries are filtered to prevent quantity conflicts.

### Testing
- Created `test_fix.py` to validate all four scenarios:
  - MW New Link with/without _LOS
  - MW Reroute with/without _LOS
- All tests pass: no duplicate PBOMs, correct quantities, correct LOS selection.

###Important Note
The SOW value is `MW New Link / Reroute` (not `MW NEW LINK` or `MW REROUTE` alone).
The code checks for this exact pattern, then uses the `TX Upgrade Scope` field to determine:
- If "dismantle" is present → MW Reroute logic
- If "dismantle" is absent → MW New Link logic

### Impact
- **TSS Scope**: Output now contains consistent, non-conflicting quantities for MW New Link / Reroute projects.
- **Backwards Compatibility**: The change only affects how items are filtered from the PR model; it does not change the PR model structure itself.
- **No breaking changes** to CLI interface or other scopes (TI, Planning, etc.).
