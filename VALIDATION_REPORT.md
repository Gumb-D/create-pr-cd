# Validation Report - PBOM Normalization for LOS Survey Selection

**Date**: 2026-07-02  
**Scope**: PR #8 PBOM normalization blocker  
**Status**: Passed

## Commands Executed

```bash
python -m py_compile scripts\pr_helpers.py scripts\generate_tss_pr_ecc.py tests\test_mw_reroute.py tests\test_geography_resolver.py
python -m unittest discover -s tests -v
python scripts\generate_tss_pr_ecc.py --site-data Info\input\site_pr_po_view.xlsx --pr-model Info\input\pr_model.xlsx --template Info\input\ecc_template.xls --mapping Info\input\contract_info_reference.md --output C:\dev\create-pr-cd-pr8-fix-artifacts\2026-07-02\real-generator-four-scenarios --scope TSS --site-code 4008B_AD,1679H_LOS,4982B,1258H_LOS
```

## Results Summary

| Command | Result |
|---|---|
| `python -m py_compile ...` | Exit `0` |
| `python -m unittest discover -s tests -v` | Exit `0`, `Ran 41 tests`, `OK` |
| Real generator command | Exit `0`, `Built 12 ECC output rows`, `Created 3 ECC workbooks` |

## Regression Coverage

- `tests.test_mw_reroute.TestProductionExcelPBOMNormalization` creates a real temporary Excel PR model whose PBOM cells load as `350000062773.0` and `350000062776.0`, then runs `scripts/generate_tss_pr_ecc.py` as a subprocess.
- The regression asserts all four TSS scenarios through the production generator path.
- Existing TI controls remain covered:
  `IPRAN Reroute` is not MW reroute, `MW Swap` with `dismantle` is not MW reroute, and `MW New Link / Reroute` / reroute routing stays intact.

## Real Generator Verification

Artifact directory:

```text
C:\dev\create-pr-cd-pr8-fix-artifacts\2026-07-02\real-generator-four-scenarios
```

Verified `details` sheet output by site:

| Site | Scenario | Survey PBOM rows | `350000589343` | `350000589344` |
|---|---|---|---|---|
| `4008B_AD` | MW New Link, non-LOS | `350000062773` once | `1.0` once | `1.0` once |
| `1679H_LOS` | MW New Link, `_LOS` | `350000062773` once | `1.0` once | `1.0` once |
| `4982B` | MW Reroute, non-LOS | `350000062773` once | `1.5` once | `1.5` once |
| `1258H_LOS` | MW Reroute, `_LOS` | `350000062776` once | `1.5` once | `1.5` once |

Observed outcome:

- No workbook emitted both survey PBOMs for the same site.
- Survey PBOM cells were canonical values without `.0`.
- Both controlled quantity PBOMs appeared exactly once per site with the expected quantity.
