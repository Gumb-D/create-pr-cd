---
name: create-pr-cd
description: Create CelcomDigi TX PR ECC output from site PR/PO data by matching the correct PR model, subcontractor, contract information, and approved line-item rules.
---

# create-pr-cd Skill

## Platform Contract

For contract execution, use `python src/main.py --input-manifest <workspace>/input.json`. The public interface is declared in `skill.json`; all business rules in this document remain skill-owned.

## 1. Purpose

This skill generates CelcomDigi TX PR ECC files from site-level PR/PO data.

The skill must:

1. Read the site data reference.
2. Determine which PR scopes are required per site.
3. Match each site to the correct PR model or approved deterministic fixed line item.
4. Retrieve contract and purchasing information from the controlled mapping reference.
5. Generate ECC output files using the ECC Template format.
6. Prevent duplicate PR generation when PR already exists.
7. Flag incomplete or ambiguous cases as `REVIEW_REQUIRED` instead of silently guessing.

## 2. Reference Files

The skill uses these input references:

### 2.1 PR Model Reference

Current governed production path:

```text
Info/input/pr_model.xlsx
```

Used for:

- TSS PR model matching
- TI PR model matching
- PBOM Code
- SOW description
- Unit
- Quantity
- Mandatory/optional/choose-group line-item evidence

The PR Model is **not** the authoritative contract/purchasing mapping source.

### 2.2 Site Data Reference

The runtime consumes site data through the approved DU Profile/canonical input path. Source iEPMS exports differ by Project and DU Model.

Used for fields such as:

- Site ID / Site Code
- Site Name
- DU Code
- Region
- Tx SOW
- MW Config Antenna Size NE
- MW Config Antenna Size FE
- SubCon - TSS Team
- SubCon - TI Team
- Subcon Planning / Subcon - Planning
- Subcon PR - Planning / approved equivalent Planning PR status field
- Existing PR status / PR number columns

For Issue #34 Planning discovery/UAT, business reference exports may be stored locally under:

```text
Info/reference/planning-pr/
```

Raw iEPMS exports are reference evidence only and must not be committed.

### 2.3 ECC Template

Current path:

```text
Info/input/ecc_template.xls
```

Used as the required output format.

### 2.4 Contract and Purchasing Reference

Authoritative path:

```text
Info/input/contract_info_reference.md
```

Used for:

- Region → Purchasing Area
- Normalized Subcontractor → Contract Number

Do not use the historical PR Model `contract infor` sheet as the active mapping authority.

### 2.5 ECC Sample Reference

Example output files may be used to understand:

- Expected file naming style
- ECC column order
- Data formatting
- Header structure
- Mandatory ECC fields

## 3. Supported PR Scopes

Business scope catalogue:

1. TSS
2. TI
3. Planning
4. Operation Backoffice

Runtime status:

- Official `scripts/create_pr.py` supports `--scope TSS`, `--scope TI`, and `--scope Planning`.
- Planning is implemented under Issue #34 for all eight supported DU Models with approved profile mappings, deterministic selection, dedicated ECC rendering and terminal reconciliation.
- Operation Backoffice remains a separate future scope and is not part of Issue #34.

Do not generate any scope unless the CLI is explicitly enabled for it.

### 3.1 Site Selection Layer

The generator accepts either selected Site Code(s) or a Generate All option before PR scope evaluation.

- `--site-code` accepts one or more comma-separated site codes.
- `--all-sites` generates for all eligible sites.
- If neither option is provided, the generator exits with an error.
- If both options are provided, the generator exits with an error.
- Filtering occurs before evaluating PR scope triggers.
- Current official CLI supports site selection for `TSS`, `TI`, and `Planning`.

### 3.2 Implementation Status

Current TI logic implementation status:

- TI Phase 1 is complete: trigger hardening, duplicate prevention, and `REVIEW_REQUIRED` foundation.
- TI Phase 2A is complete: antenna-aware matching, mandatory choose-1 handling, and exact antenna group matching.
- TI Phase 2B1 is complete: silent 0-row prevention through `REVIEW_REQUIRED` output.
- TI Phase 2B2 is complete: MW Reroute dual install/decom logic.

Current Planning status:

- All-DU Planning business logic was approved on 2026-08-11 under Issue #34.
- Planning canonical-field/profile mapping, selector, eligibility/duplicate prevention, contract normalization, official entrypoint, ECC renderer and terminal reconciliation are implemented.
- Automated regression includes all eight DU Models from raw four-header export shape through ECC output.
- Operation Backoffice is excluded from Issue #34.

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

### 4.3 Planning PR Trigger — Issue #34 Approved and Implemented

Planning applies to these eight DU Models:

1. `2023 TX Rollout`
2. `TX Mini Project`
3. `2023 Celcomdigi BAU`
4. `2024 Celcomdigi BAU`
5. `Celcomdigi USP`
6. `Jendela TX Migration`
7. `MW EOS Swap`
8. `ZTE TX MINI`

Generate Planning PR when:

- `Subcon Planning` / `Subcon - Planning` is non-blank; and
- the approved `Subcon PR - Planning` / equivalent Planning PR status or PR-number field is blank.

If Planning subcon is blank:

```text
ignore / no Planning PR
```

If the Planning PR status/number field is non-blank:

```text
skip duplicate / existing Planning PR
```

If Planning subcon is non-blank but not one of:

```text
GCI
GTSB
GCI_AA
GTSB_AA
```

then:

```text
REVIEW_REQUIRED
no partial Planning ECC
```

`TX Planning Remarks` is explicitly **not involved** in Planning eligibility, PBOM selection, contract selection, or duplicate prevention.

### 4.4 Operation Backoffice PR Trigger

Operation Backoffice remains a future scope and is not defined by Issue #34. Do not infer or enable it from the Planning implementation.

## 5. Duplicate PR Prevention

Default rule:

- If a PR number or controlled status already exists for the same site and same scope, do not generate again.

For Planning, use the approved `Subcon PR - Planning` / equivalent Planning PR control field from the resolved DU Profile.

If duplicate/existing status exists:

- Skip the site-scope combination.
- Record the terminal skip reason in the processing summary/reconciliation evidence.

## 6. Subcontractor Mapping

Use these fields by scope:

| PR Scope | Subcontractor Source |
|---|---|
| TSS | `SubCon - TSS Team` |
| TI | `SubCon - TI Team` |
| Planning | `Subcon Planning` / `Subcon - Planning` |
| Operation Backoffice | Future scope; not defined by Issue #34 |

Normalize ordinary subcontractor names before matching according to existing shared behavior.

### 6.1 Planning-specific subcontractor normalization

Planning permits exactly:

```text
GCI
GTSB
GCI_AA
GTSB_AA
```

Contract identity normalization:

```text
GCI       -> GCI
GTSB      -> GTSB
GCI_AA    -> GCI
GTSB_AA   -> GTSB
```

The `_AA` suffix is **not** a separate subcontractor and must not use a separate contract. `_AA` is preserved only as evidence for Planning line-item selection.

Unknown Planning subcontractors must fail closed. Do not fuzzy-substitute an unknown Planning value into GCI/GTSB.

## 7. Primary SOW Logic

Use `Tx SOW` as the source field for SOW detection for scopes that require SOW matching.

If one site has multiple SOW keywords in the same `Tx SOW` string:

- Use the approved primary-SOW behavior for TSS/TI.
- Do not generate PR for secondary SOWs unless a scope-specific rule explicitly requires it.

**Planning exception:** Planning PBOM selection does not use `Tx SOW` at all.

## 8. PR Model / Fixed Selector Logic

### 8.1 TSS Model Matching

TSS does not require antenna size.

TSS PR model matching key:

```text
1. Tx SOW
2. TX Upgrade Scope (only for MW New Link / Reroute)
3. Site ID (for LOS Survey selection in MW Reroute)
```

Steps:
1. Read primary SOW from `Tx SOW`.
2. For MW New Link / Reroute SOW (exact pattern: `MW New Link / Reroute`), read `TX Upgrade Scope`. If the field contains `dismantle` (case insensitive), it is a MW Reroute; otherwise, it is a MW New Link. **This classification only applies to TSS MW New Link / Reroute**.
3. Match mandatory line items from the TSS model section using the approved TSS matching behavior.
4. For MW New Link / Reroute, apply model-driven filtering using the PR model `Remarks` column.
5. LOS Survey exception remains governed by the approved TSS MW New Link/Reroute rule.
6. Preserve the approved quantity behavior.
7. If mandatory model selection is ambiguous, mark `REVIEW_REQUIRED` and block partial ECC.

### 8.2 TI Model Matching

TI uses the approved strict Tx SOW and scope-specific technical evidence/matching rules implemented in the current runtime.

Antenna-dependent TI models must use the governed antenna resolver behavior. Antenna-independent SOWs must not be blocked solely by absent antenna evidence when the current approved runtime says antenna is not required.

If no safe TI match or multiple mandatory groups match:

```text
REVIEW_REQUIRED
no partial ECC
```

### 8.3 Planning Model Logic — Issue #34 Approved

Planning is generated per eligible site and does **not** use Tx SOW or TX Planning Remarks for PBOM selection.

Planning selection key:

```text
DU Model + Subcon Planning
```

Quantity and unit for all approved Planning items:

```text
Quantity = 1
Unit = Hop
```

#### 8.3.1 `_AA` branch — highest precedence, all supported DUs

If:

```text
Subcon Planning = GCI_AA or GTSB_AA
```

then generate only:

```text
PBOM 350001042321
```

Rules:

- Applies to all eight supported DU Models.
- Do not also generate `350001143904`.
- Do not also generate `350001143905`.
- Normalize `_AA` to GCI/GTSB only for contract lookup.
- PBOM `350001042321` is an explicitly approved deterministic optional-item exception for Planning.

#### 8.3.2 Standard branch — five full-planning DU Models

For:

- `2023 TX Rollout`
- `2023 Celcomdigi BAU`
- `2024 Celcomdigi BAU`
- `Celcomdigi USP`
- `Jendela TX Migration`

if:

```text
Subcon Planning = GCI or GTSB
```

select:

```text
PBOM 350001143904
```

This is the default under all normal Planning conditions for these five DU Models. No SOW, TX Planning Remarks, antenna, coordinates, or TX Upgrade Scope changes this selection.

#### 8.3.3 Standard branch — remaining three supported DU Models

For:

- `TX Mini Project`
- `MW EOS Swap`
- `ZTE TX MINI`

if:

```text
Subcon Planning = GCI or GTSB
```

select:

```text
PBOM 350001143905
```

#### 8.3.4 Planning decision table

| `Subcon Planning` | DU Model group | PBOM Code | Unit | Qty |
|---|---|---:|---|---:|
| `GCI` or `GTSB` | 2023 TX Rollout; 2023 Celcomdigi BAU; 2024 Celcomdigi BAU; Celcomdigi USP; Jendela TX Migration | `350001143904` | Hop | 1 |
| `GCI` or `GTSB` | TX Mini Project; MW EOS Swap; ZTE TX MINI | `350001143905` | Hop | 1 |
| `GCI_AA` or `GTSB_AA` | All supported DU Models | `350001042321` only | Hop | 1 |

Exactly one Planning PBOM may be selected per eligible site.

The previous Planning PBOM `350001000403` is obsolete and must not be used.

### 8.4 Operation Backoffice Logic

Operation Backoffice remains separate future scope. Do not reuse Issue #34 Planning logic to infer Operation Backoffice triggers, line items, subcontractor, or output behavior.

## 9. Mandatory / Optional Line Item Rule

Default rule:

- Generate only deterministic approved line items automatically.
- Do not auto-select optional line items merely because they exist in the PR Model.
- Do not guess between unresolved choose-one alternatives.

### Approved Planning exception

The only Issue #34 optional auto-selection exception is:

```text
Planning + (GCI_AA or GTSB_AA)
-> PBOM 350001042321
```

This exception is deterministic and approved. It does not authorize any other optional item.

If a mandatory or approved deterministic group cannot be resolved uniquely:

```text
REVIEW_REQUIRED
whole site blocked
no partial ECC
```

## 10. Quantity Rule

Default quantity rules:

| Scope | Quantity Rule |
|---|---|
| TSS | Use approved TSS model/scope-specific rule |
| TI | Use approved TI rule |
| Planning | Always `1` per selected Planning line item |
| Operation Backoffice | Future scope; not defined here |

## 11. Contract and Purchasing Area Logic

Authoritative source:

```text
Info/input/contract_info_reference.md
```

### 11.1 Contract No

Resolve contract number by normalized subcontractor identity from the controlled mapping reference.

Rules:

- Same approved subcontractor identity uses the mapped contract according to the reference.
- Planning `GCI_AA` uses GCI contract identity.
- Planning `GTSB_AA` uses GTSB contract identity.
- `_AA` is stripped only for contract lookup; it still controls Planning PBOM selection.
- Do not invent a Planning-specific contract.

### 11.2 Purchasing Area

Resolve `Purchasing Area` using the Region mapping in:

```text
Info/input/contract_info_reference.md
```

If purchasing area cannot be resolved safely:

- fail closed according to the shared review policy;
- preserve actionable review evidence;
- do not emit partial ECC for a blocked site.

## 12. ECC Output Columns

The skill must output using the ECC Template format and current shared renderer contract.

Mandatory ECC fields include the applicable:

| ECC Field | Source / Logic |
|---|---|
| `Purchasing Area*` | `Info/input/contract_info_reference.md` Region mapping |
| `Region*` | Canonical site data |
| `Site ID*` | Canonical site data |
| `Site Name*` | Canonical site data |
| `DU Code*` | Canonical site data |
| `Contract No*` | `Info/input/contract_info_reference.md` normalized subcontractor mapping |
| `Subcontractor*` | Scope-based subcontractor mapping |
| `PBOM Code*` | Matched PR model or approved deterministic Planning selector |
| `SOW*` | Matched PR model / approved Planning line-item description according to renderer contract |
| `Unit*` | Matched model / approved selector |
| `Quantity*` | Scope quantity rule |
| `Remarks` | Blank if normal; otherwise review evidence as governed by current renderer/reconciliation flow |

Blocked sites must not leak partial ECC rows.

## 13. ECC Output Grouping

### 13.1 TSS / TI / Planning

Approved grouping contract:

```text
Scope + normalized Subcontractor + Region
```

Output filename must include the actual resolved DU Model, not hardcode TX Mini Project.

### 13.2 Operation Backoffice

Future scope. Do not define or enable its grouping as part of Issue #34.

## 14. ECC File Naming Convention

Use this generic format for supported runtime scopes:

```text
<Region>-<Subcontractor> <DU Model> <Scope> PR <YYYYMMDD>.xlsx
```

Examples:

```text
Northern-GCI TX Mini Project TSS PR 20260515.xlsx
Southern-GTSB MW EOS Swap TI PR 20260515.xlsx
Northern-GCI 2023 TX Rollout Planning PR 20260811.xlsx
```

Planning uses this convention through the dedicated Planning ECC renderer.

## 15. Review Required Handling

Use `REVIEW_REQUIRED` when the skill cannot safely determine the correct output.

Planning-specific cases include:

1. Unknown non-blank Planning subcontractor.
2. Planning PR duplicate/status field cannot be resolved when required for safe duplicate prevention.
3. Contract identity cannot be resolved from `contract_info_reference.md`.
4. Purchasing Area / mandatory ECC data cannot be resolved.
5. DU Model is outside the approved Planning support set.
6. More than one Planning PBOM would otherwise be selected.
7. Required DU Profile/header evidence is unapproved or ambiguous.

Global rule:

```text
REVIEW_REQUIRED
-> whole site blocked where the condition is blocking
-> no partial ECC
-> terminal outcome remains traceable
```

## 16. Processing Steps

The agent/runtime must execute in this order:

1. Resolve Project + DU Model profile identity.
2. Resolve approved source fields through the canonical adapter.
3. Load `Info/input/contract_info_reference.md`.
4. Load PR Model only for scopes/rules that require it.
5. Load ECC Template structure.
6. Apply site selection.
7. Evaluate the requested scope eligibility and duplicate gate.
8. For an eligible scope:
   - determine/normalize subcontractor;
   - determine contract number;
   - determine purchasing area;
   - match PR model or execute an approved deterministic selector;
   - validate mandatory output data;
   - create review evidence when needed.
9. Apply whole-site blocking/no-partial-output rules.
10. Group passed rows into ECC files.
11. Reconcile every requested site to exactly one terminal outcome.
12. Save files and processing summary.

For Planning specifically:

```text
DU Model + Subcon Planning
-> one approved Planning PBOM
```

Do not read `TX Planning Remarks` for this decision.

## 17. Output Summary Requirement

After generating ECC files, provide a summary equivalent to the current governed runtime summary, including scope, subcon, region, output file, site/line counts, review count and duplicate/ignored count.

Every requested site must be terminally reconciled.

## 18. Do Not Do

The agent/runtime must not:

1. Auto-generate optional PR line items **except** the explicit Planning `GCI_AA/GTSB_AA -> 350001042321` rule.
2. Guess between multiple matched PR models/selector outcomes.
3. Use `TX Planning Remarks` to choose a Planning PBOM.
4. Use Tx SOW to choose a Planning PBOM.
5. Generate duplicate PR when the applicable PR status/number field is non-blank.
6. Invent contract number, purchasing area, PBOM code, or SOW/description.
7. Treat `GCI_AA` or `GTSB_AA` as separate contracts.
8. Combine `350001042321` with `350001143904` or `350001143905` for the same Planning site.
9. Commit raw iEPMS reference exports.
10. Enable Operation Backoffice while implementing or operating Issue #34 Planning scope.

## 19. Expected Inputs from User / Business Owner

Controlled production inputs remain the governed runtime inputs. Business discovery may additionally use local reference exports under `Info/reference/planning-pr/` to verify four-layer field fingerprints and golden outcomes.

## 20. Expected Outputs

For implemented runtime scopes, the skill produces:

1. ECC `.xlsx` files grouped by the approved naming convention.
2. Processing summary.
3. `REVIEW_REQUIRED` issue list/evidence.
4. Skipped duplicate/ignored summary.
5. Terminal reconciliation evidence.
6. `CREATE_PR_DELIVERY_<scope>.zip` containing every declared workbook and report.

The platform contract also returns one terminal disposition for every selected source Site ID. These reconciliation Site IDs preserve the exact canonical source identity even where a separately approved renderer rule changes a workbook-facing display value.

## 21. Acceptance Criteria

Planning implementation is successful only when all of the following remain implemented and regression-tested:

1. Planning supports exactly the eight approved DU Models.
2. Planning eligibility uses Planning subcon plus Planning PR status/number, not TSS/TI fields.
3. Five full-planning DU Models select `350001143904` for `GCI/GTSB`.
4. TX Mini Project, MW EOS Swap and ZTE TX MINI select `350001143905` for `GCI/GTSB`.
5. Every supported DU selects **only** `350001042321` for `GCI_AA/GTSB_AA`.
6. `GCI_AA/GTSB_AA` use GCI/GTSB contract identities from `Info/input/contract_info_reference.md`.
7. `TX Planning Remarks` cannot change Planning eligibility or PBOM selection.
8. Blank Planning subcon generates no Planning PR.
9. Non-blank Planning PR status/number prevents regeneration.
10. Unknown Planning subcon fails closed without fuzzy substitution or partial ECC.
11. Existing TSS/TI behavior remains unchanged.
12. Official `scripts/create_pr.py --scope Planning` remains protected by DU Profile lifecycle, all-DU regression and terminal reconciliation controls.
13. Operation Backoffice remains out of scope.
