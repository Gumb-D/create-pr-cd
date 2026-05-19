---
name: create-pr-cd
description: Create CelcomDigi TX PR ECC output from site PR/PO data by matching the correct PR model, subcontractor, contract information, and mandatory line items.
---

# create-pr-cd Skill

## 1. Purpose

This skill generates CelcomDigi TX PR ECC files from site-level PR/PO data.

The skill must:

1. Read the site data reference.
2. Determine which PR scopes are required per site.
3. Match each site to the correct PR model or fixed PR line item.
4. Retrieve contract and purchasing information.
5. Generate ECC output files using the ECC Template format.
6. Prevent duplicate PR generation when PR already exists.
7. Flag incomplete or ambiguous cases as `REVIEW_REQUIRED` instead of silently guessing.

## 2. Reference Files

The skill uses these input references:

### 2.1 PR Model Reference

File name pattern:

```text
Celcomdigi TX PR Model & Line Item 20250416 Rev 2.0
```

Used for:

- TSS PR model matching
- TI PR model matching
- PBOM Code
- SOW description
- Unit
- Mandatory line item identification
- Contract information sheet: `contract infor`
- Purchasing Area
- Contract No

### 2.2 Site Data Reference

File name pattern:

```text
A-P202202168750_D002-TX Mini Project-Mira's PR_PO View-YYYYMMDDHHMMSS
```

Used for:

- Site ID
- Site Name
- DU Code
- Region
- Tx SOW
- MW Config Antenna Size NE
- MW Config Antenna Size FE
- SubCon - TSS Team
- SubCon - TI Team
- Subcon - Planning
- TX Integrated actual end date
- Existing PR status / PR number columns

### 2.3 ECC Template

File name pattern:

```text
ECC Template
```

Used as the required output format.

### 2.4 ECC Sample Reference

Example output file:

```text
Northern-GCI TX Mini Project TSS PR 20260515.xls
```

Use this sample to understand:

- Expected file naming style
- ECC column order
- Data formatting
- Header structure
- Mandatory ECC fields

## 3. Supported PR Scopes

The skill supports the following PR scopes:

1. TSS
2. TI
3. Planning
4. Operation Backoffice

Do not generate other scopes unless the user explicitly requests an extension.

### 3.1 Site Selection Layer

The generator accepts either selected Site Code(s) or a Generate All option before PR scope evaluation.

- `--site-code` accepts one or more comma-separated site codes.
- `--all-sites` generates for all eligible sites.
- If neither option is provided, the generator exits with an error.
- If both options are provided, the generator exits with an error.
- Filtering occurs before evaluating TSS, TI, Planning, or Operation Backoffice triggers.

## 4. Scope Trigger Logic

### 4.1 TSS PR Trigger

Generate TSS PR when:

- `SubCon - TSS Team` is not blank; and
- the related TSS PR status / PR number field is blank; and
- user has not requested duplicate generation.

If existing TSS PR number/status exists, skip TSS PR generation for that site.

### 4.2 TI PR Trigger

Generate TI PR when:

- `SubCon - TI Team` is not blank; and
- the related TI PR status / PR number field is blank; and
- user has not requested duplicate generation.

If existing TI PR number/status exists, skip TI PR generation for that site.

### 4.3 Planning PR Trigger

Generate Planning PR when:

- `Subcon - Planning` is not blank; and
- the related Planning PR status / PR number field is blank.

If `Subcon - Planning` is blank, ignore the site for Planning PR.

If `Subcon - Planning` contains an unknown non-blank value, output the row with `REVIEW_REQUIRED`.

### 4.4 Operation Backoffice PR Trigger

Generate Operation Backoffice PR when:

- `TX Integrated actual end date` is populated; and
- the related Operation Backoffice PR status / PR number field is blank.

Operation Backoffice subcon is fixed:

```text
Allstar
```

Operation Backoffice output does not need region-based or scope-based grouping.

## 5. Duplicate PR Prevention

Default rule:

- If a PR number/status already exists for the same site and same scope, do not generate again.

The skill does not force regenerate duplicate PRs.

If duplicate exists:

- Skip the site-scope combination.
- Record the skip reason in the processing summary.

## 6. Subcontractor Mapping

Use these fields by scope:

| PR Scope | Subcontractor Source |
|---|---|
| TSS | `SubCon - TSS Team` |
| TI | `SubCon - TI Team` |
| Planning | `Subcon - Planning` |
| Operation Backoffice | Fixed value: `Allstar` |

Normalize subcontractor names before matching:

- Trim leading/trailing spaces.
- Treat repeated spaces as one space.
- Preserve original display value for ECC output where possible.
- Use normalized value for lookup matching.

## 7. Primary SOW Logic

Use `Tx SOW` as the source field for SOW detection.

If one site has multiple SOW keywords in the same `Tx SOW` string:

- Use the first SOW keyword found in the text.
- Do not generate PR for secondary SOWs.

Example:

```text
MW Swap + MW Decom
```

Primary SOW is:

```text
MW Swap
```

## 8. PR Model Matching Logic

### 8.1 TSS Model Matching

TSS does not require antenna size.

TSS PR model matching key:

```text
Tx SOW only
```

Steps:

1. Read primary SOW from `Tx SOW`.
2. Match the primary SOW against the TSS model section in the PR model reference.
3. Select only mandatory line items.
4. Quantity is always `1` per site per matched mandatory line item.

If multiple TSS models match the same SOW:

- Do not choose automatically.
- Mark as `REVIEW_REQUIRED`.

### 8.2 TI Model Matching

TI requires SOW plus antenna size category.

TI PR model matching key:

```text
Tx SOW + antenna size category
```

Antenna source fields:

- `MW Config Antenna Size NE`
- `MW Config Antenna Size FE`

Antenna selection rule:

1. If NE and FE antenna sizes are both populated and different, use the larger antenna size.
2. If NE and FE antenna sizes are both populated and same, use that size.
3. If one side is blank, mark as `REVIEW_REQUIRED`.
4. If both sides are blank, mark as `REVIEW_REQUIRED`.

Antenna category matching:

| Antenna Size | Category |
|---|---|
| 0.3m | Small antenna model |
| 0.6m | Small antenna model |
| 1.2m | 1.2m model |
| 1.8m | 1.8m model |
| 2.4m | 2.4m model |

Steps:

1. Read primary SOW from `Tx SOW`.
2. Determine antenna category using NE and FE antenna size.
3. Match the primary SOW and antenna category against the TI model section in the PR model reference.
4. Select only mandatory line items.
5. Quantity is always `1` per site per matched mandatory line item.

If multiple TI models match the same SOW and antenna category:

- Do not choose automatically.
- Mark as `REVIEW_REQUIRED`.

### 8.3 Planning Model Logic

The Planning PR model is not available in the PR model reference file.

Planning is generated per site basis regardless of SOW and region.

Use `Subcon - Planning` to determine the Planning line item.

Planning item rule:

| `Subcon - Planning` Value | PBOM Code | SOW | Unit | Qty |
|---|---:|---|---|---:|
| `GCI` or `GTSB` | `350001000403` | `Detailed end to end transmission planning and design` | `Hop` | `1` |
| Any value ending with `_AA` | `350001042321` | `Detailed end to end transmission planning and design (for AA modification & AA submisison sow only` | `Hop` | `1` |

Rules:

- If `Subcon - Planning` is blank, ignore and do not generate Planning PR.
- If `Subcon - Planning` contains an unknown non-blank value, mark as `REVIEW_REQUIRED`.

### 8.4 Operation Backoffice Logic

Operation Backoffice is generated when `TX Integrated actual end date` is populated.

Subcon is fixed:

```text
Allstar
```

The skill must retrieve the Operation Backoffice PBOM Code, SOW, Unit, and mandatory line item logic from the PR model reference if available.

If the Operation Backoffice line item cannot be found in the PR model reference:

- Output the site with `REVIEW_REQUIRED` in Remarks.
- Do not invent PBOM Code or SOW.

## 9. Mandatory Line Item Rule

Generate only mandatory line items automatically.

Do not generate optional line items.

Do not auto-select choose-one optional or transportation items unless they are explicitly marked mandatory and unambiguous.

If a mandatory group contains multiple possible choices and no deterministic rule exists:

- Mark as `REVIEW_REQUIRED`.

## 10. Quantity Rule

Default quantity rules:

| Scope | Quantity Rule |
|---|---|
| TSS | Always `1` per site per mandatory line item |
| TI | Always `1` per site per mandatory line item |
| Planning | Always `1` per site |
| Operation Backoffice | Use matched mandatory line item quantity; if unclear, default to `1` with `REVIEW_REQUIRED` remark |

## 11. Contract and Purchasing Area Logic

Use the `contract infor` sheet from the PR model reference.

### 11.1 Contract No

Match contract number by subcontractor.

Rules:

- Same subcontractor uses the same contract number for all regions.
- Region is not used for contract number matching.
- Scope is not used unless the `contract infor` sheet explicitly requires it.

### 11.2 Purchasing Area

Retrieve `Purchasing Area` from the `contract infor` sheet.

Match by subcontractor.

If purchasing area cannot be found:

- Fill `REVIEW_REQUIRED` where applicable.
- Add explanation in Remarks.

## 12. ECC Output Columns

The skill must output using the ECC Template format.

Mandatory ECC fields:

| ECC Field | Source / Logic |
|---|---|
| `Purchasing Area*` | From `contract infor` sheet by subcontractor |
| `Region*` | From site data field `Region` |
| `Site ID*` | From site data |
| `Site Name*` | From site data |
| `DU Code*` | From site data |
| `Contract No*` | From `contract infor` sheet by subcontractor |
| `Subcontractor*` | Scope-based subcon mapping |
| `PBOM Code*` | Matched PR model or fixed Planning logic |
| `SOW*` | Matched PR model or fixed Planning logic |
| `Unit*` | Matched PR model or fixed Planning logic |
| `Quantity*` | Scope quantity rule |
| `Remarks` | Blank if normal; otherwise use `REVIEW_REQUIRED: <reason>` |

If any mandatory ECC field is missing:

- Still output the row.
- Put `REVIEW_REQUIRED: missing <field_name>` in Remarks.

Do not skip the row solely because of missing mandatory data.

## 13. ECC Output Grouping

### 13.1 TSS / TI / Planning

Generate one ECC file per:

```text
Scope + Subcon + Region
```

### 13.2 Operation Backoffice

Generate one ECC file only:

```text
Allstar TX Mini Project Operation PR <YYYYMMDD>.xls
```

No region-based grouping is required for Operation Backoffice.

## 14. ECC File Naming Convention

Use this file naming format for TSS / TI / Planning:

```text
<Region>-<Subcon> TX Mini Project <Scope> PR <YYYYMMDD>.xls
```

Examples:

```text
Northern-GCI TX Mini Project TSS PR 20260515.xls
Southern-GTSB TX Mini Project TI PR 20260515.xls
Northern-GCI TX Mini Project Planning PR 20260515.xls
```

Operation Backoffice file name:

```text
Allstar TX Mini Project Operation PR <YYYYMMDD>.xls
```

Use the execution date for `<YYYYMMDD>` unless the user provides a specific date.

## 15. Review Required Handling

Use `REVIEW_REQUIRED` when the skill cannot safely determine the correct output.

Common cases:

1. Missing mandatory ECC field.
2. Missing contract number.
3. Missing purchasing area.
4. Multiple PR models match the same SOW.
5. Multiple TI models match the same SOW and antenna category.
6. TI antenna size has one side blank.
7. TI antenna size has both sides blank.
8. Unknown non-blank Planning subcon.
9. Operation Backoffice line item cannot be found.
10. Mandatory choose-one line item cannot be selected deterministically.

Remarks format:

```text
REVIEW_REQUIRED: <clear reason>
```

Example:

```text
REVIEW_REQUIRED: TI antenna size incomplete; NE populated but FE blank
```

## 16. Processing Steps

The agent must execute the skill in this order:

1. Load PR model reference.
2. Load `contract infor` sheet.
3. Load site data reference.
4. Load ECC Template structure.
5. Normalize column names and subcontractor names.
6. Identify existing PR status / PR number columns for duplicate prevention.
7. For each site row:
   - Evaluate TSS trigger.
   - Evaluate TI trigger.
   - Evaluate Planning trigger.
   - Evaluate Operation Backoffice trigger.
8. For each triggered scope:
   - Determine subcontractor.
   - Determine contract number.
   - Determine purchasing area.
   - Match PR model or fixed line item.
   - Generate mandatory line items only.
   - Validate ECC mandatory fields.
   - Add `REVIEW_REQUIRED` remarks where needed.
9. Group output rows into ECC files.
10. Save files using required naming convention.
11. Produce a processing summary.

## 17. Output Summary Requirement

After generating ECC files, the agent must provide a summary table:

| Scope | Subcon | Region | Output File | Site Count | Line Count | Review Required Count | Skipped Duplicate Count |
|---|---|---|---|---:|---:|---:|---:|

For Operation Backoffice, Region may be shown as:

```text
ALL
```

Also provide a separate issue list for all `REVIEW_REQUIRED` rows:

| Site ID | Scope | Subcon | Region | Issue |
|---|---|---|---|---|

## 18. Do Not Do

The agent must not:

1. Generate optional PR line items automatically.
2. Guess between multiple matched PR models.
3. Use secondary SOW if multiple SOW keywords exist.
4. Generate duplicate PR when PR already exists.
5. Invent contract number, purchasing area, PBOM code, or SOW.
6. Skip rows with missing mandatory fields without reporting.
7. Modify source reference files unless explicitly requested.

## 19. Expected Inputs from User

The user should provide:

1. PR model reference file.
2. Site data reference file.
3. ECC template file.
4. Optional ECC sample file.
5. Optional output date if different from execution date.

## 20. Expected Outputs

The skill must output:

1. ECC `.xls` or `.xlsx` files grouped by required naming convention.
2. Processing summary.
3. `REVIEW_REQUIRED` issue list.
4. Skipped duplicate summary.

## 21. Acceptance Criteria

The skill is successful when:

1. ECC output follows the provided ECC Template format.
2. TSS PR is matched by `Tx SOW` only.
3. TI PR is matched by `Tx SOW + antenna size category`.
4. Planning PR uses fixed Planning PBOM logic based on `Subcon - Planning`.
5. Operation Backoffice uses fixed Allstar subcon and is triggered by `TX Integrated actual end date`.
6. Contract No and Purchasing Area are matched from `contract infor` by subcontractor.
7. Only mandatory line items are generated.
8. Existing PR records are not regenerated.
9. Review-required cases are visible and traceable.
10. Output files are grouped and named correctly.
