# Changelog

## 2025-06-24 - MW Reroute/New Link Quantity Conflict Fix (Revised)

### Changes Made

#### Code Changes
- **File**: `scripts/generate_tss_pr_ecc.py`
- **Section**: TSS model matching logic (around line 1155)
- **Improvement**: Added quantity conflict resolution for MW New Link / Reroute SOW items using model-driven Remarks-based filtering.

#### What was fixed:

1. **Eliminated duplicate PBOM entries** - Previously, PBOMs 350000589343 and 350000589344 could appear multiple times with different quantities (1 hop and 1.5 hop) in the same output, causing data inconsistency.

2. **Implemented model-driven filtering**:
   - PR model `Remarks` column is now the primary filter:
     - Remarks "Reroute" → only selected for MW Reroute projects
     - Remarks "New Link" → only selected for MW New Link projects
   - This prevents hardcoding PBOM codes and adapts to future PR model updates.

3. **Correct LOS Survey selection** (exception to Remarks filtering):
   - **MW Reroute** (with "dismantle" in TX Upgrade Scope):
     - Site ID contains `_LOS` → select 350000062776
     - Site ID does NOT contain `_LOS` → select 350000062773
   - **MW New Link** (without "dismantle"):
     - Always select 350000062773 (regardless of _LOS)
   - Note: LOS Survey items typically have empty Remarks, hence the special handling.

4. **Enforced consistent quantities** (defense in depth):
   - For MW Reroute: 350000589343/344 must have quantity **1.5 hop** only
   - For MW New Link: 350000589343/344 must have quantity **1 hop** only
   - Quantity check acts as verification, not primary filter.

5. **TI flow regression prevention**:
   - Restored `is_mw_reroute_row()` to check `Tx SOW` (not `TX Upgrade Scope`).
   - This ensures TI MW Reroute routing is based on SOW string, not on the TSS-only "dismantle" classification.
   - Prevents regression where non-reroute TI SOWs containing "dismantle" might be misrouted.

#### Documentation Updates
- **File**: `SKILL.md`
- **Section**: 8.1 TSS Model Matching
- Rewrote the entire matching procedure to emphasize model-driven Remarks filtering and clarify that TX Upgrade Scope is only used for TSS MW New Link / Reroute classification.
- Added explicit note: "Do not rely on hardcoded PBOM checks alone."

#### Testing
- Completely revised `test_fix.py` to include:
  - **TI control tests** (4 tests):
    - Non-reroute SOW with dismantle → should NOT be MW Reroute
    - MW Reroute without dismantle → should still be MW Reroute
    - Case insensitive matching
    - Empty SOW handling
  - **TSS scenario tests** (4 tests):
    - MW New Link (no LOS) → 350000062773, qty 1.0
    - MW New Link (with LOS) → 350000062773, qty 1.0
    - MW Reroute (no LOS) → 350000062773, qty 1.5
    - MW Reroute (with LOS) → 350000062776, qty 1.5
- All tests pass; no duplicate PBOMs; correct selection and quantities.

### Important Notes

1. **TSS vs TI separation**:
   - The `dismantle`-based classification of MW Reroute vs New Link is **only** used within the TSS MW New Link / Reroute matching branch.
   - TI flow uses `is_mw_reroute_row()` which checks the `Tx SOW` field directly. This separation prevents regression.

2. **SOW pattern**:
   - The exact SOW string is "MW New Link / Reroute" (not "MW NEW LINK" or "MW REROUTE" alone).
   - Both checks use case-insensitive matching.

3. **Remarks-driven design**:
   - The code now loads the `Remarks` column from the PR model and uses it as the primary filter for 350000589343/344.
   - This makes the solution data-driven and maintainable; updates to the PR model only require correct Remarks entries.

4. **LOS Survey items** are an exception to Remarks filtering (they have no Remarks) and require the special Site ID-based selection.

### Impact
- **TSS Scope**: Output now contains consistent, non-conflicting quantities and correct Survey selection for MW New Link / Reroute projects.
- **TI Scope**: No regression; routing logic restored to original SOW-based behavior.
- **Backwards Compatibility**: Only affects TSS MW New Link / Reroute items; other scopes unchanged.
- **Maintainability**: Solution is now model-driven via Remarks column, reducing need for code changes when PR model is updated.

### Files Modified
| File | Change |
|------|--------|
| `scripts/generate_tss_pr_ecc.py` | Restored `is_mw_reroute_row()`, added Remarks loading, updated TSS matching algorithm |
| `scripts/test_fix.py` | Comprehensive regression tests (TI + TSS) |
| `SKILL.md` | Updated matching procedure documentation |
| `CHANGELOG.md` | This entry |
