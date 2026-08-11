# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model and writing ECC output grouped by region, subcontractor, DU Model, and scope.

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
│  ├─ reference/
│  │  └─ planning-pr/              # local business/reference evidence; raw iEPMS exports are not committed
│  ├─ sample/
│  │  └─ Northern-GCI TX Mini Project TSS PR 20260515.xlsx
│  └─ OPENCLAW_SKILL_DEVELOPMENT_GUIDELINE.md
├─ output/
├─ scripts/
├─ SKILL.md
└─ README.md
```

## Input Placeholder Table

| Placeholder Path | Description |
|---|---|
| `Info/input/site_pr_po_view.xlsx` | Daily refreshed Site PR/PO View file |
| `Info/input/pr_model.xlsx` | PR model file |
| `Info/input/ecc_template.xls` | ECC template file containing `details` sheet |
| `Info/input/contract_info_reference.md` | Authoritative Region → Purchasing Area and Subcontractor → Contract Number mapping |

Planning discovery/UAT reference exports may be kept locally under `Info/reference/planning-pr/`. Raw iEPMS exports and generated UAT artefacts must not be committed.

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
- Planning business rules are approved under Issue #34 but the Planning CLI path is not enabled until implementation/regression/UAT are complete.
- Operation Backoffice remains a separate future scope and is not part of Issue #34.

## Output Naming Convention

Generated formal ECC files follow this generic format:

```text
<Region>-<Subcontractor> <DU Model> <Scope> PR <YYYYMMDD>.xlsx
```

**Examples:**

```text
Northern-GCI TX Mini Project TSS PR 20260518.xlsx
Central-GTSB TX Mini Project TSS PR 20260518.xlsx
Sabah-Seri Pancar MW EOS Swap TI PR 20260518.xlsx
```

**Split files** (when >30 unique Site IDs in a group):

```text
Northern-GCI TX Mini Project TSS PR 20260518 Part 1.xlsx
Northern-GCI TX Mini Project TSS PR 20260518 Part 2.xlsx
```

Explicit UAT artefacts insert `_NON_PRODUCTION_UAT` before the file extension and are stored in the isolated UAT run directory.

> Runtime note: the current CLI generator accepts only `--scope TSS` and `--scope TI`. Planning is business-approved but not yet executable. Operation Backoffice remains undefined/unsupported future scope.

## Supported PR Scopes

### Current CLI Support

| Scope | Runtime Status | Business Status | Description |
|---|---|---|---|
| TSS | Active | Implemented | Microwave Site Survey PR |
| TI | Active | Implemented | Microwave Integration PR |
| Planning | Disabled pending Issue #34 | Approved | Microwave Planning PR for all eight supported DU Models |
| Operation Backoffice | Unsupported | Future / separate scope | Microwave Backoffice PR |

## Planning PR Business Rules — Issue #34

### Supported DU Models

Planning PR is approved for:

1. `2023 TX Rollout`
2. `TX Mini Project`
3. `2023 Celcomdigi BAU`
4. `2024 Celcomdigi BAU`
5. `Celcomdigi USP`
6. `Jendela TX Migration`
7. `MW EOS Swap`
8. `ZTE TX MINI`

### Planning source fields

Planning uses:

- `Subcon Planning` / `Subcon - Planning`
- `Subcon PR - Planning` / approved equivalent Planning PR status/number field

`TX Planning Remarks` is explicitly not a Planning PR decision input.

### Eligibility

```text
Planning subcon non-blank
AND Planning PR status/number blank
-> evaluate Planning PBOM
```

Blank Planning subcon is ignored. A non-blank existing Planning PR status/number prevents duplicate generation. Unknown non-blank Planning subcon is `REVIEW_REQUIRED` and must not be fuzzy-substituted.

### Planning PBOM matrix

| Planning Subcon | DU Model group | PBOM | Qty | Unit |
|---|---|---:|---:|---|
| `GCI` / `GTSB` | 2023 TX Rollout; 2023 Celcomdigi BAU; 2024 Celcomdigi BAU; Celcomdigi USP; Jendela TX Migration | `350001143904` | 1 | Hop |
| `GCI` / `GTSB` | TX Mini Project; MW EOS Swap; ZTE TX MINI | `350001143905` | 1 | Hop |
| `GCI_AA` / `GTSB_AA` | All eight supported DU Models | `350001042321` only | 1 | Hop |

For `_AA`, do not also generate `350001143904` or `350001143905`. PBOM `350001042321` is an explicitly approved deterministic optional-item exception for Planning only.

### Planning contract identity

Contract and Purchasing Area use:

```text
Info/input/contract_info_reference.md
```

Normalize for contract lookup only:

```text
GCI_AA  -> GCI
GTSB_AA -> GTSB
```

The original `_AA` value remains the evidence that selects PBOM `350001042321`.

### Planning non-inputs

Planning PBOM selection does not depend on:

- Tx SOW
- TX Planning Remarks
- TX Upgrade Scope
- antenna size
- coordinates
- TSS/TI subcontractor

Region remains available to shared Purchasing Area/output grouping logic but does not select the Planning PBOM.

Design and implementation plan:

- `docs/superpowers/specs/2026-08-11-planning-pr-all-du-design.md`
- `docs/superpowers/plans/2026-08-11-planning-pr-all-du.md`

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

---

## Key Matching Rules

### Matching Logic by Scope

| Scope | Matching Logic |
|---|---|
| TSS | Tx SOW from site data |
| TI | Tx SOW + applicable antenna/subtype evidence from site data |
| Planning | DU Model + `Subcon Planning`; fixed approved PBOM matrix above; no Tx SOW/Planning Remarks input |
| Operation Backoffice | Future scope; not defined by Issue #34 |

### Mapping Rules

- **Purchasing Area** ← derived from Region mapping in `Info/input/contract_info_reference.md`
- **Contract Number** ← derived from Subcontractor mapping in `Info/input/contract_info_reference.md`
- **Planning `_AA` contract identity** ← `GCI_AA → GCI`, `GTSB_AA → GTSB`
- **Unknown Planning subcontractors** ← fail closed; do not fuzzy substitute
- **Generic non-Planning unknown subcontractors** ← existing runtime fuzzy behavior remains governed separately

### ECC Output Rules

- Single sheet named `details` only
- `SOW*` ← sourced from the applicable approved model/selector
- `PBOM Code*` ← sourced from the applicable approved model/selector
- `Unit*` ← sourced from the applicable approved model/selector
- `Quantity*` ← model quantity or scope-specific quantity rule
- `SN.` ← sequential (1-based) per output file
- Max 30 unique Site IDs per output file

---

## Validation Checklist

- Only one sheet named `details` is generated.
- `SN.` starts at `1` and is sequential per file.
- `Purchasing Area*` uses region mapping from `Info/input/contract_info_reference.md`.
- `Contract Number*` uses subcontractor mapping from `Info/input/contract_info_reference.md`.
- Column `P` repeats the same value as `Contract Number *` where the existing renderer contract applies.
- PBOM/Description/Unit/Quantity come from an approved model or deterministic scope selector.
- Output files contain no more than `30` unique Site IDs.
- Formal output is generated only for a `PRODUCTION` profile.
- UAT output is visibly marked and isolated under `NON_PRODUCTION_UAT/<run-id>/`.
- Planning remains runtime-disabled until Issue #34 implementation tests pass and the CLI is intentionally enabled.

## Troubleshooting

**Profile lifecycle gate:**
- `PROFILE_NOT_PRODUCTION`: the resolved profile is not approved for formal ECC. Use `--non-production-uat` only for approved business validation, or complete formal production promotion.
- `PROFILE_NOT_UAT_ELIGIBLE`: the profile has not reached `PR_INPUT_READY`, is deprecated, or is otherwise ineligible for ECC UAT.

**Missing input files:**
- If a required input file is missing, place it in `Info/input/` or pass the correct path via CLI.

**ECC template validation errors:**
- If the ECC template does not contain a `details` sheet, the script will raise a validation error.
- Ensure `Info/input/ecc_template.xls` is valid and contains the required sheet.

**Contract/subcontractor handling:**
- The authoritative mapping is `Info/input/contract_info_reference.md`.
- Planning accepts only `GCI`, `GTSB`, `GCI_AA`, and `GTSB_AA` for automatic processing.
- Planning `_AA` values normalize only for contract lookup; they are not separate contracts.
- Unknown Planning subcontractors must fail closed rather than use fuzzy matching.

**PR model / selector failures:**
- For TSS/TI, verify the active PR Model and approved scope-specific rules.
- For Planning after Issue #34 runtime implementation, verify the DU Model and Planning subcontractor against the approved three-PBOM matrix; Tx SOW and TX Planning Remarks are not Planning selectors.

---
