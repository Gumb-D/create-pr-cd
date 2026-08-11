# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model and writing ECC output grouped by region, subcontractor, and scope.

## Purpose

This repository provides a daily workflow for refreshing site PR/PO data and producing CelcomDigi TX PR ECC files in the required template format.

## Standard Skill Contract

The platform and standalone contract entrypoint is:

```text
python src/main.py --input-manifest <workspace>/input.json
```

`skill.json` declares version `4.0.0`, one `site_data` `.xlsx` input, TSS/TI and site-selection parameters, timeout, cancellation, and result contract `1.0`. The command emits NDJSON progress and writes authoritative `result.json`. PR model, template, mappings, profiles, and policies remain internal approved-package assets rather than public platform inputs.

The existing `scripts/create_pr.py` command remains the direct domain CLI.

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
│  │  └─ Northern-GCI TX Mini Project TSS PR 20260515.xlsx
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
6. Run either formal production mode or explicit non-production UAT mode, according to the resolved DU Profile status.
7. Review generated files under the effective output directory recorded in the JSON summary.

## Lifecycle Gate and Command Examples

The official entrypoint enforces the structured DU Profile lifecycle status:

```text
PRODUCTION
→ formal ECC generation is allowed

PR_INPUT_READY
→ formal ECC generation is blocked
→ explicit --non-production-uat is required for business validation

DRAFT / PROFILED / BUSINESS_VALIDATED / DEPRECATED
→ ECC generation is blocked in both modes
```

The gate uses `profile.status`; profile notes cannot enable ECC output.

### Formal production execution

Use this command only when the resolved DU Profile status is `PRODUCTION`:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --all-sites --output output
```

A non-`PRODUCTION` profile returns:

```text
PROFILE_NOT_PRODUCTION
```

### Explicit non-production UAT execution

Use this mode to generate reviewable ECC output from a `PR_INPUT_READY` profile:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --all-sites --output output --non-production-uat
```

Generate TI scope for selected sites in UAT mode:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TI --site-code A01073_AD --output output --non-production-uat
```

Override paths if needed:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --pr-model Info/input/pr_model.xlsx --template Info/input/ecc_template.xls --mapping Info/input/contract_info_reference.md --scope TSS --all-sites --output output --non-production-uat
```

UAT output is isolated under:

```text
<requested-output>/NON_PRODUCTION_UAT/<UTC-run-id>/
```

The directory, ECC/review filenames, and summary filename contain `NON_PRODUCTION_UAT`. The summary records:

```text
run_mode
profile_status
non_production_uat
production_ecc_allowed
requested_output
output_root
run_id
```

UAT files are validation artefacts and must not be treated as production ECC.

## Site Selection Mode

The generator supports explicit site selection or full-site generation.

### Generate selected site for UAT

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --site-code B00123 --output output --non-production-uat
```

### Generate multiple selected sites for UAT

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --site-code B00123,B00456,K00340 --output output --non-production-uat
```

### Generate all eligible sites for UAT

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --all-sites --output output --non-production-uat
```

Remove `--non-production-uat` only for a formally promoted `PRODUCTION` profile.

The script requires either `--site-code` or `--all-sites`.
Do not use both at the same time.

- `--scope` currently supports only `TSS` and `TI`.
- Planning and Operation Backoffice are defined in the skill documentation but are not available in the current CLI implementation.

## Output Naming Convention

Generated formal ECC files follow this format:

```text
<Region>-<Subcontractor> <DU Model> <Scope> PR <YYYYMMDD>.xlsx
```

**Examples:**

```text
Northern-GCI TX Mini Project TSS PR 20260518.xlsx
Central-GTSB TX Mini Project TSS PR 20260518.xlsx
Sabah-Seri Pancar TX Mini Project TSS PR 20260518.xlsx
```

**Split files** (when >30 unique Site IDs in a group):

```text
Northern-GCI TX Mini Project TSS PR 20260518 Part 1.xlsx
Northern-GCI TX Mini Project TSS PR 20260518 Part 2.xlsx
```

Explicit UAT artefacts insert `_NON_PRODUCTION_UAT` before the file extension and are stored in the isolated UAT run directory.

**Operation Backoffice** files use `Allstar` as the subcontractor:

```text
Central-Allstar TX Mini Project Operation Backoffice PR 20260518.xlsx
```

> Note: The current CLI generator accepts only `--scope TSS` and `--scope TI`. Planning and Operation Backoffice are defined as target scopes but are not yet implemented in this script.

## Supported PR Scopes

### Current CLI Support

The CLI currently supports these scopes:

| Scope | Status | Description |
|---|---|---|
| TSS | ✓ Active | Microwave Site Survey PR |
| TI | ✓ Active | Microwave Integration PR |

### Skill Roadmap

The skill documentation defines additional scopes for future implementation:

| Scope | Status | Description |
|---|---|---|
| Planning | 📋 Planned | Microwave Planning PR |
| Operation Backoffice | 📋 Planned | Microwave Backoffice PR |

Each scope uses different matching logic and PR model definitions (see **Key Matching Rules** section below).

---

## Current TI Logic Status

The TI implementation is active for the current CLI `--scope TI` flow.

- Duplicate prevention is implemented using existing TI PR status values.
- `REVIEW_REQUIRED` framework is implemented for unsafe or incomplete TI cases.
- Antenna-aware TI matching is implemented.
- Mandatory choose-1 logic is implemented.
- MW Reroute dual install/decom logic is implemented.
- MW Re-engineering intentionally remains manual review until business rules are confirmed.
- Current CLI scope support remains `TSS` and `TI` only.

Current stable baseline:

| Scope / Metric | Current Result |
|---|---:|
| TSS output | 78 files / 2727 rows |
| TI output | 14 files / 234 rows |
| TI `REVIEW_REQUIRED` | 163 |
| TI duplicates skipped | 1741 |

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
- **Unknown Subcontractors** ← fuzzy matching enabled using nearest / highest similarity match

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
- Formal output is generated only for a `PRODUCTION` profile.
- UAT output is visibly marked and isolated under `NON_PRODUCTION_UAT/<run-id>/`.

## Troubleshooting

**Profile lifecycle gate:**
- `PROFILE_NOT_PRODUCTION`: the resolved profile is not approved for formal ECC. Use `--non-production-uat` only for approved business validation, or complete formal production promotion.
- `PROFILE_NOT_UAT_ELIGIBLE`: the profile has not reached `PR_INPUT_READY`, is deprecated, or is otherwise ineligible for ECC UAT.

**Missing input files:**
- If a required input file is missing, place it in `Info/input/` or pass the correct path via CLI.

**ECC template validation errors:**
- If the ECC template does not contain a `details` sheet, the script will raise a validation error.
- Ensure `Info/input/ecc_template.xls` is valid and contains the required sheet.

**Unknown subcontractor handling:**
- Unknown subcontractor names use fuzzy matching to find the nearest / highest similarity match.
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
