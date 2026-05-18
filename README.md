# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model and writing ECC template output grouped by scope, subcontractor, and region.

## Project Purpose

This repository converts site-level PR/PO source data into CelcomDigi TX PR ECC files using PR model line items, contract references, and ECC output conventions.

Key goals:
- Read site data and PR model references.
- Match each site to the correct PR scope and PR model line items.
- Generate ECC output in the required template format.
- Group output by region, subcontractor, and scope.
- Prevent duplicate PR generation.

## Input Files

The tool uses these reference files in `Info/`:

- `Info/A-P202202168750_D002-TX Mini Project-Mira's PR_PO View-YYYYMMDDHHMMSS.xlsx`
  - Site data source.
  - Contains site ID, region, `Tx SOW`, antenna size, subcontractor assignments, PR status, and operation dates.
- `Info/Celcomdigi TX PR Model & Line Item 20250416 Rev 2.0.xlsx`
  - PR model and line item reference.
  - Provides SOW definitions, PR line item descriptions, PBOM codes, units, quantities, and mandatory flags.
- `Info/ECC Template.xls`
  - ECC output format template.
  - Used to align output columns and formatting.
- `Info/contract_info_reference.md`
  - Region → Purchasing Area mapping.
  - Subcontractor → Contract Number mapping.

## Supported PR Scopes

This repository currently supports these PR scopes:

- `TSS`
- `TI`
- `Planning`
- `Operation Backoffice`

## Key Business Logic

### Scope matching logic

- `TSS`: match by `Tx SOW` only.
- `TI`: match by `Tx SOW` plus antenna size.
- `Planning`: fixed PBOM logic based on `Subcon - Planning`.
- `Operation Backoffice`: fixed subcontractor `Allstar` when `TX Integrated actual end date` exists.

### Mandatory PR generation rules

- Only generate PR rows for mandatory PR model line items.
- Do not regenerate a PR if the same scope already has an existing PR number/status for a site.
- If a site already has an existing PR, the tool skips duplicate generation for that scope.

### Model value sourcing

- `SOW*` is taken from the PR model `Description` field.
- `PBOM Code*`, `Unit*`, and `Quantity*` are sourced from PR model line items.

### Contract and purchasing mapping

- `Purchasing Area*` is derived from `Region` using `Info/contract_info_reference.md`.
- `Contract Number*` is derived from subcontractor mappings in `Info/contract_info_reference.md`.
- Column `P` (`Contract Number`) is populated with the same value as `Contract Number *`.

## ECC Output Rules

- Output files contain exactly one sheet named `details`.
- `SN.` is sequential and starts at `1` for each output file.
- `Purchasing Area` is mapped from `Region`.
- `Contract Number` is mapped from subcontractor.
- Column `P` repeats the same contract number as `Contract Number *`.
- Each output file may contain at most `30` unique site IDs.
- Files are split into parts when unique site count exceeds `30`.

## Output Naming Convention

Standard output filename format:

```text
<Region>-<Subcon> TX Mini Project <Scope> PR <YYYYMMDD>.xls
```

Split file example:

```text
Northern-GCI TX Mini Project TSS PR 20260518 Part 1.xls
Northern-GCI TX Mini Project TSS PR 20260518 Part 2.xls
```

Operation Backoffice output uses the same naming convention, with `Allstar` as the subcontractor.

## How to Run

1. Install Python 3.
2. Install dependencies:

```bash
pip install pandas openpyxl
```

3. Run the generator script from the repository root:

```bash
python scripts/generate_tss_pr_ecc_amended.py
```

4. Expected output folder:

- `output/outputs/`

Generated ECC files are saved into `output/outputs/`.

## Validation Checklist

- `details` sheet only.
- `SOW*`, `PBOM Code*`, and `Unit*` are from the PR model.
- `Contract Number*` and `Purchasing Area*` are mapped correctly.
- No duplicate PR generation for the same scope and site when existing PR data exists.
- Each file contains at most `30` unique site IDs.

## Troubleshooting

- Missing columns in input files may cause failures when reading site or PR model data.
- Unknown subcontractor names may be fuzzy-matched, but if no match is found the file will use `UNKNOWN` contract values.
- If a PR model match is missing, review the `Tx SOW` source text and PR model `SOW` definitions.
- Cases that cannot be resolved automatically should be flagged as `REVIEW_REQUIRED` before final processing.

---

Commit message:

`docs: add README for create-pr-cd ECC generation`
