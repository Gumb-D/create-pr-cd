# create-pr-cd

Generate CelcomDigi TX PR ECC output files from site PR/PO data by matching site data with the PR model or approved deterministic selectors and writing ECC output grouped by region, subcontractor, DU Model, and scope.

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

TSS example:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --all-sites --output output
```

Planning example:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope Planning --all-sites --output output
```

Use formal execution only when the resolved DU Profile status is `PRODUCTION`. A non-`PRODUCTION` profile returns `PROFILE_NOT_PRODUCTION`.

### Explicit non-production UAT execution

Use this mode to generate reviewable ECC output from a `PR_INPUT_READY` profile:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TSS --all-sites --output output --non-production-uat
```

Generate TI scope for selected sites in UAT mode:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope TI --site-code A01073_AD --output output --non-production-uat
```

Planning UAT uses the same lifecycle gate:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope Planning --all-sites --output output --non-production-uat
```

Override paths if needed:

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --pr-model Info/input/pr_model.xlsx --template Info/input/ecc_template.xls --mapping Info/input/contract_info_reference.md --scope Planning --all-sites --output output --non-production-uat
```

UAT output is isolated under:

```text
<requested-output>/NON_PRODUCTION_UAT/<UTC-run-id>/
```

The directory, ECC/review filenames, and summary filename contain `NON_PRODUCTION_UAT`. UAT files are validation artefacts and must not be treated as production ECC.

## Site Selection Mode

The generator supports explicit site selection or full-site generation.

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope Planning --site-code B00123 --output output
```

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope Planning --site-code B00123,B00456,K00340 --output output
```

```bash
python scripts/create_pr.py --site-data Info/input/site_pr_po_view.xlsx --scope Planning --all-sites --output output
```

The script requires exactly one of `--site-code` or `--all-sites`.

- Official `--scope` supports `TSS`, `TI`, `Planning`, and `BACKOFFICE`.
- Operation Backoffice is implemented independently under Issue #94 and does not reuse Issue #34 Planning eligibility or line-item logic.

## Output Naming Convention

Generated formal ECC files follow this generic format:

```text
<Region>-<Subcontractor> <DU Model> <Scope> PR <YYYYMMDD>.xlsx
```

Examples:

```text
Northern-GCI TX Mini Project TSS PR 20260518.xlsx
Central-GTSB TX Mini Project TSS PR 20260518.xlsx
Sabah-Seri Pancar MW EOS Swap TI PR 20260518.xlsx
Northern-GCI 2023 TX Rollout Planning PR 20260811.xlsx
```

Split files when a group exceeds 30 unique Site IDs:

```text
Northern-GCI 2023 TX Rollout Planning PR 20260811 Part 1.xlsx
Northern-GCI 2023 TX Rollout Planning PR 20260811 Part 2.xlsx
```

Explicit UAT artefacts insert `_NON_PRODUCTION_UAT` before the file extension and are stored in the isolated UAT run directory.

## Supported PR Scopes

| Scope | Runtime Status | Business Status | Description |
|---|---|---|---|
| TSS | Active | Implemented | Microwave Site Survey PR |
| TI | Active | Implemented | Microwave Integration PR |
| Planning | Active | Implemented / Issue #34 | Microwave Planning PR for all eight supported DU Models |
| Operation Backoffice | Active | Implemented / Issue #94 | Milestone-triggered monthly Microwave Backoffice PR |

## Operation Backoffice PR Business Rules — Issue #94

Operation Backoffice uses the official `scripts/create_pr.py --scope BACKOFFICE` entrypoint. Main issuance requires `--all-sites` and a source directory that resolves to the complete nine governed DU-model export set, because all eligible DUs for the closed billing month must be aggregated before the monthly tier is selected. Supplementary issuance may use a narrower source after the Main PBOM has been frozen in the authoritative tracker.

Example Main run:

```bash
python scripts/create_pr.py --site-data Info/reference/backoffice-pr --scope BACKOFFICE --all-sites --backoffice-tracker "TX Outsource & NOC Database.xls" --billing-month 2026-07 --output output
```

Governed rules:

- One eligible Delivery Unit record equals one Hop.
- Billing month is the calendar month of the approved Backoffice trigger Actual End Date.
- All supported DU Models aggregate into the same monthly tier.
- `<=800` Hops uses PBOM `350000592793`; `>800` uses `350000592794`. Exactly 800 uses the lower tier.
- Main PR is issued only for the immediately previous closed month and freezes that month's PBOM. Supplementary PR reuses the frozen Main PBOM.
- Duplicate identity is `Delivery Unit Code + Canonical Backoffice Event`; Site ID is not the duplicate or reconciliation key. Historical duplicates are blocked from the tracker, while repeated entitlement identity inside the same current run fails closed for review.
- The authoritative issued-history source is `TX Outsource & NOC Database.xls`, sheet `TX Outsource Details`; NOC scope is excluded.
- Provider/contract are effective-dated and resolved from `config/backoffice_service_registry.yaml` using the trigger date. A billing month spanning a provider/contract transition is partitioned into separate validated provider/contract workbooks before the 30-site split.
- Current configured Backoffice provider is Allstar / `S1MY2024042501WBF1`, but the renderer derives the provider from validated runtime data rather than hard-coding it.
- Unknown TX Rollout SOW defaults to TX Integrated and records `BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED`.
- Unknown CD consolidation SOW requires review only when a governed MOCN/Decom milestone could affect the requested billing month; clearly historical or not-yet-complete records are ignored with an approved reason.
- Any `REVIEW_REQUIRED` record blocks the entire Backoffice ECC run; partial ECC output is not allowed.
- Backoffice ECC filenames use `TX Outsource-<Provider> Backoffice <MAIN|SUPPLEMENTARY> <YYYY-MM> PR <YYYYMMDD>.xlsx`; batches above 30 unique Site IDs are emitted as numbered `Part N` files with at most 30 unique Site IDs per workbook. If an otherwise identical same-day target already exists, a deterministic `Batch N` suffix preserves the earlier issued artifact instead of overwriting it.
- Required renderer identity (`Site ID`, `Site Name`, `Delivery Unit Code`, `Region`) must have approved Backoffice-scope source mappings before production generation.

## Planning PR Business Rules — Issue #34

### Supported DU Models

Planning PR is implemented for:

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
- `Subcon PR - Planning` / `Subcon - PR Planning`

The exact four-layer header fingerprint is controlled by each DU Profile. `TX Planning Remarks` is explicitly not a Planning PR decision input.

### Eligibility

```text
Planning subcon non-blank
AND Planning PR status/number blank
-> evaluate Planning PBOM
```

Blank Planning subcon is ignored. A non-blank existing Planning PR status/number prevents duplicate generation. An explicit `No PR required...` value is ignored. Unknown non-blank Planning subcon is `REVIEW_REQUIRED` and is not fuzzy-substituted.

### Planning PBOM matrix

| Planning Subcon | DU Model group | PBOM | Qty | Unit |
|---|---|---:|---:|---|
| `GCI` / `GTSB` | 2023 TX Rollout; 2023 Celcomdigi BAU; 2024 Celcomdigi BAU; Celcomdigi USP; Jendela TX Migration | `350001143904` | 1 | Hop |
| `GCI` / `GTSB` | TX Mini Project; MW EOS Swap; ZTE TX MINI | `350001143905` | 1 | Hop |
| `GCI_AA` / `GTSB_AA` | All eight supported DU Models | `350001042321` only | 1 | Hop |

For `_AA`, do not also generate `350001143904` or `350001143905`. PBOM `350001042321` is the approved deterministic optional-item exception for Planning only.

### Planning descriptions

| PBOM | SOW description |
|---:|---|
| `350001143904` | `2026-Detailed end to end transmission planning and design` |
| `350001143905` | `2026-Single-hop planning and design` |
| `350001042321` | `Detailed end to end transmission planning and design (for AA modification & AA submisison sow only)` |

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

### Runtime architecture

```text
Project + DU Model profile routing
-> approved four-layer Planning fields
-> canonical Planning record
-> duplicate/eligibility gate
-> deterministic Planning selector
-> shared contract/purchasing reference
-> dedicated Planning ECC renderer
-> shared terminal reconciliation
```

The implementation intentionally does not reuse the legacy TSS/TI line-item renderer for Planning. Existing TSS/TI behavior remains isolated.

Design and implementation references:

- `docs/superpowers/specs/2026-08-11-planning-pr-all-du-design.md`
- `docs/superpowers/plans/2026-08-11-planning-pr-all-du.md`

---

## Current TI Logic Status

The TI implementation is active for `--scope TI`.

- Duplicate prevention is implemented using existing TI PR status values.
- `REVIEW_REQUIRED` framework is implemented for unsafe or incomplete TI cases.
- Antenna-aware TI matching is implemented.
- Mandatory choose-1 logic is implemented.
- MW Reroute dual install/decom logic is implemented.
- MW Re-engineering intentionally remains manual review until business rules are confirmed.

---

## Key Matching Rules

| Scope | Matching Logic |
|---|---|
| TSS | Tx SOW from site data |
| TI | Tx SOW + applicable antenna/subtype evidence from site data |
| Planning | DU Model + `Subcon Planning`; fixed approved PBOM matrix above; no Tx SOW/Planning Remarks input |
| Operation Backoffice | Approved DU trigger milestone + Delivery Unit/event duplicate identity + monthly PBOM tier |

### Mapping Rules

- **Purchasing Area** ← Region mapping in `Info/input/contract_info_reference.md`
- **Contract Number** ← Subcontractor mapping in `Info/input/contract_info_reference.md`
- **Planning `_AA` contract identity** ← `GCI_AA → GCI`, `GTSB_AA → GTSB`
- **Unknown Planning subcontractors** ← fail closed; do not fuzzy substitute
- **Generic non-Planning unknown subcontractors** ← existing runtime behavior remains governed separately

### ECC Output Rules

- Single sheet named `details` only
- `SOW*` ← approved model/selector description
- `PBOM Code*` ← approved model/selector
- `Unit*` ← approved model/selector
- `Quantity*` ← model quantity or scope-specific quantity rule
- `SN.` ← sequential (1-based) per output file
- Max 30 unique Site IDs per output file
- Planning Column O/source Tx SOW is blank because Tx SOW is not a Planning decision input
- Column P repeats the approved Contract Number

---

## Validation Checklist

- Only one sheet named `details` is generated.
- `SN.` starts at `1` and is sequential per file.
- `Purchasing Area*` uses `Info/input/contract_info_reference.md`.
- `Contract Number*` uses `Info/input/contract_info_reference.md`.
- Column `P` repeats the same value as `Contract Number *` where the renderer contract applies.
- PBOM/Description/Unit/Quantity come from an approved model or deterministic selector.
- Output files contain no more than `30` unique Site IDs.
- Formal output is generated only for a `PRODUCTION` profile.
- UAT output is visibly marked and isolated under `NON_PRODUCTION_UAT/<run-id>/`.
- Planning is covered by all-eight-DU raw four-header end-to-end regression plus full repository regression.

## Troubleshooting

**Profile lifecycle gate:**
- `PROFILE_NOT_PRODUCTION`: the resolved profile is not approved for formal ECC. Use `--non-production-uat` only for approved UAT, or complete formal production promotion.
- `PROFILE_NOT_UAT_ELIGIBLE`: the profile has not reached `PR_INPUT_READY`, is deprecated, or is otherwise ineligible for ECC UAT.

**Missing input files:**
- If a required input file is missing, place it in `Info/input/` or pass the correct path via CLI.

**Planning contract/subcontractor handling:**
- The authoritative mapping is `Info/input/contract_info_reference.md`.
- Planning accepts only `GCI`, `GTSB`, `GCI_AA`, and `GTSB_AA` for automatic processing.
- Planning `_AA` values normalize only for contract lookup; they are not separate contracts.
- Unknown Planning subcontractors fail closed rather than use fuzzy matching.

**PR model / selector failures:**
- For TSS/TI, verify the active PR Model and approved scope-specific rules.
- For Planning, verify the DU Model and Planning subcontractor against the approved three-PBOM matrix; Tx SOW and TX Planning Remarks are not Planning selectors.

---
