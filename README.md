# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model and writing ECC output grouped by region, subcontractor, and scope.

## Purpose

This repository provides a daily workflow for refreshing site PR/PO data and producing CelcomDigi TX PR ECC files in the required template format.

Input files are placed at fixed placeholder paths (`Info/input/*`), allowing daily refresh without code changes.

## Folder Structure

```text
create-pr-cd/
├─ Info/
│  ├─ input/
│  │  ├─ site_pr_po_view.xlsx
│  │  ├─ pr_model.xlsx
│  │  ├─ ecc_template.xls
│  │  └─ contract_info_reference.md
│  ├─ sample/
│  │  └─ Northern-GCI TX Mini Project TSS PR 20260515.xls
│  └─ OPENCLAW_SKILL_DEVELOPMENT_GUIDELINE.md
├─ output/
├─ scripts/
├─ create-pr-cd_SKILL.md
└─ README.md
```

## Input Placeholder Table

| Placeholder Path | Description |
|---|---|
| `Info/input/site_pr_po_view.xlsx` | Daily refreshed Site PR/PO View file |
| `Info/input/pr_model.xlsx` | PR model file |
| `Info/input/ecc_template.xls` | ECC template file containing `details` sheet |
| `Info/input/contract_info_reference.md` | Region → Purchasing Area and Subcontractor → Contract Number mapping |

## Daily Operation Steps

1. Download the latest Site PR/PO View file.
2. Rename or copy it to `Info/input/site_pr_po_view.xlsx`.
3. Ensure the PR model is available as `Info/input/pr_model.xlsx`.
4. Ensure the ECC template is available as `Info/input/ecc_template.xls`.
5. Ensure the mapping file is available as `Info/input/contract_info_reference.md`.
6. Run the generator.
7. Review generated files under `output/`.

## Command Examples

Basic execution:

```bash
python scripts/generate_tss_pr_ecc_amended.py
```

Override paths if needed:

```bash
python scripts/generate_tss_pr_ecc_amended.py --site-data Info/input/site_pr_po_view.xlsx --pr-model Info/input/pr_model.xlsx --template Info/input/ecc_template.xls --mapping Info/input/contract_info_reference.md --output output
```

## Output Naming Convention

Generated ECC files follow this format:

```text
<Region>-<Subcontractor> TX Mini Project <Scope> PR <YYYYMMDD>.xls
```

**Examples:**

```text
Northern-GCI TX Mini Project TSS PR 20260518.xls
Central-GTSB TX Mini Project TSS PR 20260518.xls
Sabah-Seri Pancar TX Mini Project TSS PR 20260518.xls
```

**Split files** (when >30 unique Site IDs in a group):

```text
Northern-GCI TX Mini Project TSS PR 20260518 Part 1.xls
Northern-GCI TX Mini Project TSS PR 20260518 Part 2.xls
```

**Operation Backoffice** files use `Allstar` as the subcontractor:

```text
Central-Allstar TX Mini Project Operation PR 20260518.xls
```

## Supported PR Scopes

The generator supports the following Project Report (PR) scopes:

| Scope | Description |
|---|---|
| TSS | Microwave Site Survey PR |
| TI | Microwave Integration PR |
| Planning | Microwave Planning PR |
| Operation Backoffice | Microwave Backoffice PR |

Each scope uses different matching logic and PR model definitions (see **Key Matching Rules** section below).

---

## Key Matching Rules

### Matching Logic by Scope

| Scope | Matching Logic |
|---|---|
| TSS | Tx SOW from site data |
| TI | Tx SOW + Antenna Size from site data |
| Planning | Fixed PBOM logic using `Subcon - Planning` mapping |
| Operation Backoffice | Allstar + `TX Integrated actual end date` from site data |

### Mapping Rules

- **Purchasing Area** ← derived from Region mapping in `Info/input/contract_info_reference.md`
- **Contract Number** ← derived from Subcontractor mapping in `Info/input/contract_info_reference.md`
- **Unknown Subcontractors** ← fuzzy matching enabled, using highest similarity match above 60% threshold

### ECC Output Rules

- Single sheet named `details` only
- `SOW*` ← sourced from PR model Description
- `PBOM Code*` ← sourced from PR model Code
- `Unit*` ← sourced from PR model Unit
- `Quantity*` ← PR model quantity or scope-specific quantity rule
- `SN.` ← sequential (1-based) per output file
- Max 30 unique Site IDs per output file

---

## Validation Checklist

- Only one sheet named `details` is generated.
- `SN.` starts at `1` and is sequential per file.
- `Purchasing Area*` uses region mapping from `Info/input/contract_info_reference.md`.
- `Contract Number*` uses subcontractor mapping from `Info/input/contract_info_reference.md`.
- Column `P` repeats the same value as `Contract Number *`.
- `SOW*` is sourced from the PR model `Description`.
- `PBOM Code*` is sourced from the PR model code.
- `Unit*` is sourced from the PR model unit.
- Output files contain no more than `30` unique site IDs.

## Troubleshooting

**Missing input files:**
- If a required input file is missing, place it in `Info/input/` or pass the correct path via CLI.

**ECC template validation errors:**
- If the ECC template does not contain a `details` sheet, the script will raise a validation error.
- Ensure `Info/input/ecc_template.xls` is valid and contains the required sheet.

**Unknown subcontractor handling:**
- Unknown subcontractor names use fuzzy matching to find the highest similarity match (minimum 60% threshold).
- If the fuzzy match result is incorrect or undesired:
  1. Do not automatically change the mapping file.
  2. Verify the correct subcontractor name in the source data.
  3. Confirm the correct contract number mapping with business stakeholders.
  4. After confirmation, either:
     - Update `Info/input/contract_info_reference.md` with the new mapping, **or**
     - Standardize the subcontractor naming in the source data.
  5. Re-run the generator.

**PR model matching failures:**
- If PR model matches fail, verify:
  1. `Tx SOW` values in site data match PR model SOW descriptions (or are substrings).
  2. PR model sheet name is correct: `TX Line Item (After 21-Apr 26)`.
  3. Required columns exist in the PR model: `SOW`, `Description`, `Code`, `Unit`, `Quantity`.

---
