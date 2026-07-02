# Validation Report - Strict TI SOW Matching for PR #13

**Date**: 2026-07-02  
**Scope**: PR #13 strict TI SOW matching blocker  
**Validated Commit**: `c3ccb22cb000e975c2b47a5e0759dc40c01a8557`  
**Status**: Passed

## Commands Executed

```bash
python -m py_compile scripts\pr_helpers.py scripts\generate_tss_pr_ecc.py tests\test_ti_sow_matching.py tests\test_geography_resolver.py tests\test_mw_reroute.py
python -m unittest discover -s tests -v
python scripts\generate_tss_pr_ecc.py --site-data C:\dev\create-pr-cd-pr13-fix-artifacts\2026-07-02\real-generator-strict-ti-sow\strict_ti_site_data.xlsx --pr-model Info\input\pr_model.xlsx --template Info\input\ecc_template.xls --mapping Info\input\contract_info_reference.md --output C:\dev\create-pr-cd-pr13-fix-artifacts\2026-07-02\real-generator-strict-ti-sow\output --scope TI --all-sites
```

The first two commands were re-run from a clean detached worktree at commit `c3ccb22cb000e975c2b47a5e0759dc40c01a8557`.

## Results Summary

| Command | Result |
|---|---|
| `python -m py_compile ...` | Exit `0` |
| `python -m unittest discover -s tests -v` | Exit `0`, `Ran 43 tests`, `OK` |
| Real generator command | Exit `0`, `Built 4 ECC output rows`, `Created 3 ECC workbooks`, `Created review-required file ... (3 items)` |

## Strict Matching Contract

- `normalize_ti_sow()` canonicalizes TI SOW values by collapsing repeated whitespace, trimming edges, uppercasing, and failing closed for blank or NaN-like inputs.
- `ti_sow_matches_model()` allows only canonical exact equality after normalization.
- No substring matching, `startswith`, or fuzzy SOW matching remains in TI mandatory-model selection or antenna-requirement detection.
- The alias map is intentionally empty because the current PR model evidence did not show any legitimate TI SOW aliases that require exceptions.

## Regression Coverage

- `tests.test_ti_sow_matching.TestStrictTiSowMatcher` verifies the production helper accepts harmless case and whitespace variation but rejects unsupported supersets.
- `tests.test_ti_sow_matching.TestProductionTiSowMatching` writes a temporary Excel site workbook and runs `scripts/generate_tss_pr_ecc.py` as a subprocess against the real PR model.
- The subprocess regression proves:
  - `BBU Patching` still emits the mandatory TI item with blank antennas.
  - `MW IDU Patching` still emits the mandatory TI item with blank antennas.
  - `BBU Patching Extended` does not emit the `BBU Patching` mandatory item and is routed to review.
  - `MW Parallel Link` with blank antennas is still `REVIEW_REQUIRED`.
  - `MW Parallel Link` with valid `1.2m` antenna data selects the expected antenna PBOM.
  - `MW Parallel Link Extended` no longer triggers the antenna-required path by substring and instead fails closed as no match.

## Real Generator Verification

Artifact directory:

```text
C:\dev\create-pr-cd-pr13-fix-artifacts\2026-07-02\real-generator-strict-ti-sow
```

Generated files:

- `strict_ti_site_data.xlsx`
- `output\Northern-GTSB TX Mini Project TI PR 20260702.xlsx`
- `output\Sabah-NR Services TX Mini Project TI PR 20260702.xlsx`
- `output\Sarawak-Trintel TX Mini Project TI PR 20260702.xlsx`
- `output\REVIEW_REQUIRED_TI_20260702.csv`

Observed ECC output:

| Site | Source SOW | Output PBOM(s) | Outcome |
|---|---|---|---|
| `TI_BBU_OK` | `bbu   patching` | `350001095420` | Valid TI output without antenna review |
| `TI_IDU_OK` | `mw idu patching` | `350001095420` | Valid TI output without antenna review |
| `TI_MW_ANT_OK` | `MW Parallel Link` | `350000212476`, `350001095410` | Valid TI output with route + antenna selection |

Observed review output:

| Site | Source SOW | Reason Code | Outcome |
|---|---|---|---|
| `TI_BBU_EXT` | `BBU Patching Extended` | `NO_MATCHING_TI_PR_MODEL_ITEM` | Unsupported superset stayed out of ECC output |
| `TI_MW_ANT_REVIEW` | `MW Parallel Link` | `MISSING_TI_ANTENNA_SIZE` | Antenna-required TI row still fails closed with blank antenna data |
| `TI_MW_EXT` | `MW Parallel Link Extended` | `NO_MATCHING_TI_PR_MODEL_ITEM` | Unsupported superset did not trigger antenna-required substring matching |
