# Issue #34 — All-DU Planning PR Design

**Date:** 2026-08-11  
**Status:** Business-approved design baseline  
**Issue:** #34

## 1. Goal

Implement Planning PR as a shared PR scope for all currently supported TX/MW DU Models, using DU-specific source-field mapping but one common Planning business rule engine.

Planning PR is independent from TSS/TI SOW matching and from Operation Backoffice. Operation Backoffice remains a separate future scope.

## 2. Supported DU Models

Planning PR must support these eight DU Models:

1. `2023 TX Rollout`
2. `TX Mini Project`
3. `2023 Celcomdigi BAU`
4. `2024 Celcomdigi BAU`
5. `Celcomdigi USP`
6. `Jendela TX Migration`
7. `MW EOS Swap`
8. `ZTE TX MINI`

The local discovery/reference evidence is stored under:

```text
Info/reference/planning-pr/
```

Raw iEPMS exports are evidence only and must not be committed to Git.

## 3. Source Fields

Planning PR uses these business fields from each DU export/profile:

- `Subcon Planning` / `Subcon - Planning`
- `Subcon PR - Planning` / equivalent approved Planning PR status/number field

`TX Planning Remarks` is explicitly **not used** for Planning PR eligibility, line-item selection, contract selection, or duplicate prevention.

Each DU Profile may resolve different four-layer iEPMS fingerprints to the same canonical Planning fields.

## 4. Eligibility and Duplicate Prevention

A site is eligible for Planning PR when:

1. Planning subcontractor is non-blank; and
2. Planning PR status/number field is blank.

If Planning subcontractor is blank, ignore the site for Planning scope.

If Planning PR status/number is non-blank, do not generate another Planning PR for that site.

If Planning subcontractor is non-blank but not one of the approved values below, fail closed to `REVIEW_REQUIRED`; do not guess a contract or line item.

Approved source values:

```text
GCI
GTSB
GCI_AA
GTSB_AA
```

## 5. Subcontractor and Contract Normalization

Contract resolution reuses the same authoritative mapping as other PR scopes:

```text
Info/input/contract_info_reference.md
```

No Planning-specific contract table is introduced.

Contract identity normalization:

```text
GCI       -> GCI
GTSB      -> GTSB
GCI_AA    -> GCI
GTSB_AA   -> GTSB
```

The `_AA` suffix is not a separate subcontractor. It is a Planning line-item selector only.

## 6. Planning Line-Item Decision Matrix

### 6.1 `_AA` branch — highest precedence

For **all eight DU Models**:

```text
Subcon Planning = GCI_AA or GTSB_AA
-> generate only PBOM 350001042321
-> quantity 1
-> unit Hop
-> do not also generate 350001143904
-> do not also generate 350001143905
```

Although `350001042321` is an optional Planning line item in the reference, this is an explicitly approved deterministic exception to the global no-optional-auto-selection rule.

### 6.2 Standard Planning branch — five DU Models

For these five DU Models:

- `2023 TX Rollout`
- `2023 Celcomdigi BAU`
- `2024 Celcomdigi BAU`
- `Celcomdigi USP`
- `Jendela TX Migration`

when:

```text
Subcon Planning = GCI or GTSB
```

generate:

```text
PBOM: 350001143904
Quantity: 1
Unit: Hop
```

This is the default for these five DU Models under every normal Planning condition. No SOW, TX Planning Remarks, antenna, region, or TX Upgrade Scope condition changes this selection.

### 6.3 Standard Planning branch — remaining three DU Models

For:

- `TX Mini Project`
- `MW EOS Swap`
- `ZTE TX MINI`

when:

```text
Subcon Planning = GCI or GTSB
```

generate:

```text
PBOM: 350001143905
Quantity: 1
Unit: Hop
```

## 7. Decision Table

| Planning Subcon | DU Model group | PBOM | Contract identity | Additional Planning item |
|---|---|---:|---|---|
| `GCI` / `GTSB` | 2023 TX Rollout; 2023 Celcomdigi BAU; 2024 Celcomdigi BAU; Celcomdigi USP; Jendela TX Migration | `350001143904` | GCI / GTSB | None |
| `GCI` / `GTSB` | TX Mini Project; MW EOS Swap; ZTE TX MINI | `350001143905` | GCI / GTSB | None |
| `GCI_AA` / `GTSB_AA` | All supported DU Models | `350001042321` | GCI / GTSB | None |

Exactly one Planning PBOM is selected per eligible site.

## 8. Explicit Non-Inputs

The following must not influence Planning line-item selection:

- `Tx SOW`
- `TX Planning Remarks`
- `TX Upgrade Scope`
- antenna size
- coordinates
- region, except where region is independently needed for ECC purchasing/output grouping
- TSS subcontractor
- TI subcontractor

## 9. Output and Shared Controls

Planning should reuse existing safe shared behavior where applicable:

- canonical Site Code identity;
- Project + DU Model profile resolution;
- approved four-layer Header Fingerprint resolution;
- lifecycle/profile gate;
- contract lookup from `contract_info_reference.md`;
- purchasing-area lookup from the same controlled reference;
- duplicate/no-output accounting;
- `REVIEW_REQUIRED` fail-closed behavior;
- ECC template validation;
- max 30 unique Site IDs per output file;
- renderer reconciliation and terminal site accounting.

Planning output should group by:

```text
Planning scope + normalized subcontractor + region
```

and use the resolved DU Model name in the filename, consistent with the current generic naming convention.

## 10. Runtime Boundary Before Implementation

Until Issue #34 code and regression tests are merged:

```text
--scope Planning
```

must remain unsupported by the production CLI.

Documenting approved Planning rules does not itself enable Planning ECC generation.

## 11. Fail-Closed Cases

At minimum, Planning generation must block/review when:

- Planning subcontractor is unknown and non-blank;
- Planning PR control/status field required for duplicate prevention cannot be resolved;
- contract identity cannot be resolved from `contract_info_reference.md`;
- required ECC output fields cannot be resolved;
- DU Model is not in the approved Planning support set;
- more than one Planning PBOM would otherwise be selected;
- the runtime profile/header evidence is not approved under existing DU Profile governance.

No partial Planning ECC may be emitted for a blocked site.

## 12. Acceptance Matrix

The implementation must prove at least:

1. Each of the five `350001143904` DU Models selects `350001143904` for GCI/GTSB.
2. Each of the three `350001143905` DU Models selects `350001143905` for GCI/GTSB.
3. Every supported DU selects only `350001042321` for GCI_AA/GTSB_AA.
4. `_AA` contract identity strips the suffix for contract lookup.
5. `TX Planning Remarks` changes do not affect Planning selection.
6. Blank Planning subcon produces no Planning PR.
7. Existing/non-blank Planning PR status/number prevents duplicate generation.
8. Unknown Planning subcon fails closed.
9. Existing TSS/TI behavior is unchanged.
10. Production Planning remains blocked until the complete Issue #34 implementation is intentionally enabled and validated.

## 13. Scope Exclusion

Issue #34 does **not** implement Operation Backoffice. Previous Issue #34 wording that tied this work to `CD consolidation 2023` Backoffice/Operation PR is superseded by this business-approved all-DU Planning definition.
