# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model and writing ECC output grouped by region, subcontractor, and scope.

## Project Purpose

This repository provides a daily workflow for refreshing site PR/PO data and producing CelcomDigi TX PR ECC files in the required template format.

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
<Region>-<Subcon> TX Mini Project <Scope> PR <YYYYMMDD>.xls
```

Split files apppear as:

```text
<Northern>-<GCI> TX Mini Project TSS PR 20260518 Part 1.xls
<Northern>-<GCI> TX Mini Project TSS PR 20260518 Part 2.xls
```

Operation Backoffice files also use the same naming pattern with `Allstar` as the subcontractor.

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

- If a required input file is missing, place it in `Info/input/` or pass the correct path via CLI.
- If the ECC template does not contain a `details` sheet, the script will raise a validation error.
- If subcontractor names are unknown, the mapping file must be updated.
- If PR model matches fail, verify `Tx SOW` values and PR model SOW definitions.

---

Commit message:

`refactor: restructure PR generator input workflow`
