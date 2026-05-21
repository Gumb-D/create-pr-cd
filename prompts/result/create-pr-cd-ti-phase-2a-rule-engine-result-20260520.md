# TI Phase 2A Rule Engine Validation Result

## Summary
- Branch: `feature/ti-phase-2a-antenna-matching-20260520`
- Validation completed for TI Phase 2A on the same branch.
- Only the missing archive file was added and committed.
- No merge was performed.

## Files inspected
- `scripts/generate_tss_pr_ecc.py`
- `Info/input/pr_model.xlsx`
- `Info/input/site_pr_po_view.xlsx`
- `Info/input/ecc_template.xls`
- `Info/input/contract_info_reference.md`
- Generated outputs under `output/test_tss_guard_phase2a`, `output/test_ti_phase2a_all`, and temporary single-site output dirs.

## Files changed
- `scripts/generate_tss_pr_ecc.py` (already committed in previous feature branch work)
- `prompts/result/create-pr-cd-ti-phase-2a-rule-engine-result-20260520.md`

## Tests executed
1. Full TSS validation:
   - `python scripts/generate_tss_pr_ecc.py --output output/test_tss_guard_phase2a --all-sites --scope TSS`
2. Full TI validation:
   - `python scripts/generate_tss_pr_ecc.py --output output/test_ti_phase2a_all --all-sites --scope TI`
3. Single-site TI validations:
   - `python scripts/generate_tss_pr_ecc.py --output output/test_single_9663C_AD --site-code 9663C_AD --scope TI`
   - `python scripts/generate_tss_pr_ecc.py --output output/test_single_2065E_AD --site-code 2065E_AD --scope TI`
   - `python scripts/generate_tss_pr_ecc.py --output output/test_single_Q01394_AD_1 --site-code Q01394_AD_1 --scope TI`
   - `python scripts/generate_tss_pr_ecc.py --output output/test_single_4008B_AD --site-code 4008B_AD --scope TI`

## Test results
### TSS full validation
- Output directory: `output/test_tss_guard_phase2a`
- TI/TSS script returned exit code: `0`
- TSS candidates: `1962`
- Built ECC rows: `2727`
- Output files created: `78`
- Script warnings lines: `236`
- No runtime failures observed.

### TI full validation
- Output directory: `output/test_ti_phase2a_all`
- TI candidates with SubCon - TI Team: `1923`
- Candidates after TI Phase 1 filtering: `100`
- Duplicate TI rows skipped: `1741`
- TI Phase 1 review-required flagged: `82`
- Built ECC rows: `387`
- Output files created: `14`
- TI script warnings lines: `8`
- Output naming preserved as `* TX Mini Project TI PR 20260521.xls`.

### Single-site validation evidence
- `9663C_AD`: site selected, 1 TI candidate, `0` ECC rows built; `No mandatory items found for SOW: MW Hardware Upgrade`.
- `2065E_AD`: site selected, 1 TI candidate, `0` ECC rows built; `No mandatory items found for SOW: BBU Patching`.
- `Q01394_AD_1`: MW Re-engineering site created `REVIEW_REQUIRED_TI_20260521.csv` with `1` review-required item.
- `4008B_AD`: duplicate TI site created `DUPLICATES_SKIPPED_TI_20260521.csv` with `1` skipped item.

### Positive TI output evidence
- `9743C_AD` successfully generated 1 TI row in `Sarawak-Allstar TX Mini Project TI PR 20260521.xls`.
  - Output line item: `New - MW Link (0.3/0.6m, 2 antenna) for C&D Project`
  - Confirmed single details row in the `details` sheet.
- `1106L_HU` successfully generated 1 TI row in `Central-GCI TX Mini Project TI PR 20260521.xls`.
  - Output line item: `Swap - MW Link (0.9/1.2m, 2 antenna) for C&D Project`
  - Confirmed one details row and antenna-selection remark: `TI antenna sizes differ - using larger size for matching`.

## Investigation: Non-antenna TI matching gaps

### 9663C_AD / MW Hardware Upgrade
- **Input Tx SOW:** `MW Hardware Upgrade`
- **Antenna:** 0.3m (NE) / 0.6m (FE)
- **PR Model search:** Zero matching TI items in PR Model Column A for `MW Hardware Upgrade`
- **Result:** 0 ECC rows generated (expected)
- **Root cause:** PR model gap — no matching mandatory items for this SOW name

### 2065E_AD / BBU Patching
- **Input Tx SOW:** `BBU Patching`
- **Antenna:** None (non-antenna)
- **PR Model search:** PR model has `MW BBU/IDU Patching` (2 items, 1 mandatory) but zero items match `BBU Patching` exactly
- **Result:** 0 ECC rows generated (expected)
- **Root cause:** PR model gap — exact SOW text mismatch between input and PR model

### Conclusion
Both cases are **PR model data gaps, not script bugs**. The matching logic correctly rejects these because no mandatory TI items exist for the exact SOW names provided. The script is functioning as designed.

## Remaining gaps
- No pure `MW Reroute` TI site was available in the input dataset for a dedicated MW Reroute site validation.
- PR model does not contain mandatory TI items for `MW Hardware Upgrade` or `BBU Patching` SOW names (only `MW BBU/IDU Patching` exists).
- Some site-specific TI SOWs produce `No mandatory items found` because the current PR model does not include matching mandatory TI lines for those SOWs.

## Confirmations
- No TSS, Planning, or Operation logic was modified in this validation cycle.
- Only `scripts/generate_tss_pr_ecc.py` was changed for TI Phase 2A.
- The ECC template and sample inputs were not modified:
  - `Info/input/ecc_template.xls`
  - `Info/input/pr_model.xlsx`
  - `Info/input/site_pr_po_view.xlsx`
  - `Info/input/contract_info_reference.md`

## Cleanup
- Temporary validation folders were generated then cleaned after verification.
