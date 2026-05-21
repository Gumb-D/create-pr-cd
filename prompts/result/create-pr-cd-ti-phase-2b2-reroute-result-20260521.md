# TI Phase 2B-2 MW Reroute Dual Logic Result - 2026-05-21

## Files inspected

- `scripts/generate_tss_pr_ecc.py`
- `Info/input/pr_model.xlsx`
- `Info/input/site_pr_po_view.xlsx`
- `prompts/result/*phase-2a*`
- `prompts/result/*phase-2b1*`

## Files changed

- `scripts/generate_tss_pr_ecc.py`

## Implementation summary

- Added a dedicated MW Reroute TI path guarded by `is_mw_reroute_row()`.
- Existing `match_ti_models()` behavior remains unchanged for non-MW-Reroute TI rows.
- Added strict install/new size extraction using:
  1. `MW Config Antenna Size NE` + `MW Config Antenna Size FE`
  2. `BOQ Configuration`
  3. `TX SOW Details`
  4. `NE SOW Details` + `FE SOW Details`
- Added best-effort decom/existing size extraction using:
  1. `BOQ Configuration`
  2. `TX SOW Details`
  3. `NE SOW Details`
  4. `FE SOW Details`
- Decom extraction never uses `MW Config Antenna Size NE/FE`.
- Decom extraction requires decom/existing context before the size within the same line/clause to avoid borrowing install sizes.
- MW Reroute generation now emits the install item when target size is found, emits dismantle only when decom size and model item are confidently matched, and otherwise emits explicit `REVIEW_REQUIRED` reasons.

## Validation commands

```powershell
python scripts/generate_tss_pr_ecc.py --output output_test/phase2b2_tss --all-sites --scope TSS
python scripts/generate_tss_pr_ecc.py --output output_test/phase2b2_ti --all-sites --scope TI
python scripts/generate_tss_pr_ecc.py --output output_test/phase2b2_samples --site-code 9743C_AD,7885A_AD,P00681_AD,4068D_AD,1834B_AD,1145B_AD,Q01461_AD,A00878_EB,2677C_LOS,4470A_HU --scope TI
python -m py_compile scripts/generate_tss_pr_ecc.py
git diff --check
```

## Validation results

- TSS: 78 files / 2727 ECC rows
- TI: 14 files / 234 ECC rows
- TI duplicate skipped: 1741
- TI review-required total: 163
- `git diff --check`: passed, with Windows LF-to-CRLF warning only
- `python -m py_compile`: passed

## Review counts

- No matching TI PR model item: 60
- MW Re-engineering follow-up required: 59
- Missing Tx SOW: 23
- MW Reroute decom antenna size missing: 15
- MW Reroute install antenna size missing: 4
- MW Reroute decom antenna size ambiguous: 2

## MW Reroute evidence

Sample validation confirmed install rows are generated where target/new size is found and decom is sent to review when missing or ambiguous:

- `9743C_AD`: install PBOM `350001095409`; review `MW Reroute decom antenna size ambiguous`
- `7885A_AD`: install PBOM `350001095410`; review `MW Reroute decom antenna size missing`
- `P00681_AD`: install PBOM `350001095410`; review `MW Reroute decom antenna size missing`
- `4068D_AD`: install PBOM `350001095409`; review `MW Reroute decom antenna size missing`
- `1834B_AD`: install PBOM `350001095410`; review `MW Reroute decom antenna size missing`
- `1145B_AD`: install PBOM `350001095410`; review `MW Reroute decom antenna size missing`
- `Q01461_AD`: install PBOM `350001095410`; review `MW Reroute decom antenna size missing`
- `A00878_EB`: install PBOM `350001095409`; review `MW Reroute decom antenna size missing`
- `2677C_LOS`: skipped by duplicate prevention
- `4470A_HU`: skipped by duplicate prevention

## Remaining gaps

- Decom antenna size is still not reliably extractable across the dataset.
- MW Reroute rows with missing or ambiguous decom size require manual review before dismantle item selection.
- Four current MW Reroute candidates have missing install size and therefore produce no ECC rows.

## Confirmations

- No TSS logic changed; TSS output stayed 78 files / 2727 rows.
- No Planning logic changed.
- No Operation logic changed.
- No ECC template changed.
- No quantity logic changed.
- No input files changed.
- No output/test files are staged for commit.
- No repo-root temporary files or residue were created.
