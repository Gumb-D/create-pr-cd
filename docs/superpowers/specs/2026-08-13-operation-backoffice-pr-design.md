# Operation Backoffice PR Design

**Issue:** #94
**Scope:** Operation Backoffice PR only
**Status:** Business logic approved for implementation
**Production PR Model baseline:** v4.1 via `config/pr_model_baseline.yaml`

## Purpose

Implement Operation Backoffice PR as an independent governed PR scope, isolated from Planning PR (#34 / PR #86) and existing TSS/TI behavior.

Backoffice PR is milestone-triggered and monthly-volume-tiered. It is not driven by a Backoffice subcontractor/status field in iEPMS because no Backoffice PR status exists there. Historical issued-PR state is read from the external `TX Outsource & NOC Database.xls` tracker.

## Core business model

```text
iEPMS DU
-> resolve Project + DU Model
-> resolve approved Backoffice completion milestone
-> valid Actual End Date creates one entitlement
-> 1 eligible DU = 1 Hop
-> billing month = trigger Actual End Date calendar month
-> aggregate all supported DU Models for that month
-> choose monthly PBOM tier
-> remove already-issued entitlement using external tracker
-> render remaining candidate rows into Operation Backoffice ECC
-> reconcile every selected entitlement
```

## Supported DU Models and completion triggers

| DU Model | Trigger rule |
|---|---|
| `2023 Celcomdigi BAU` | Microwave TX Cutover Date |
| `2024 Celcomdigi BAU` | Microwave TX Cutover Date |
| `Celcomdigi USP` | Microwave TX Cutover Date |
| `TX Mini Project` | TX Integrated actual end |
| `Jendela TX Migration` | Cut Over actual end |
| `MW EOS Swap` | Site Integrated actual end |
| `ZTE TX MINI` | Site Integrated actual end |
| `2023 TX Rollout` | SOW-driven: TX Integrated or L1 Approved |
| `CD consolidation 2023` | SOW-driven: MOCN or Decom |

Source columns must be resolved through approved four-layer Header Fingerprints. Fixed Excel column positions are not production identities.

## 2023 TX Rollout SOW mapping

### L1 Approved flow

The following TX SOW values use `L1 Approved actual end`:

- `Decom - Relo`
- `Decom`
- `Decom - Decom + Relo`
- `Decom - Reroute`
- `Decom - Remain`
- `Decom - Decom + Reroute`

The duplicate business value is normalized to one configuration entry.

### TX Integrated flow

The following TX SOW values use `TX Integrated actual end`:

- `MW Re-engineering`
- `MW New Link / Reroute`
- `MW Hardware Upgrade`
- `MW Remote Upgrade`
- `MW Parallel Link`
- `MW Swap`
- `BBU Patching`
- `MW IDU Relocation`
- `MW IDU Patching`
- `IPRAN Port Upgrade`

### Unknown TX SOW

Unknown/new/unmatched TX Rollout SOW does **not** block generation. It defaults to TX Integrated flow and records the non-blocking warning:

```text
BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED
```

## CD consolidation 2023 SOW mapping

### MOCN flow

Use `MOCN actual end` for:

- `Swap`
- `Modernization`
- `Remote MOCN`
- `GF MOCN`

### Decom flow

Use `Decom actual end` for:

- `MOCN Decomm(Dismantle Passive)`
- `MOCN Decomm`
- `Decomm`
- `Maintain USP MOCN(Dismantle Passive)`
- `Decomm, MOCN By Other Vendor`

Unknown CD consolidation SOW is not approved for automatic fallback. It is `REVIEW_REQUIRED` when either governed CD milestone could place the entitlement in the requested billing month. If neither milestone is complete, the record is `NOT_YET_ELIGIBLE`; if all completed governed CD milestones are outside the requested billing month, the record is ignored as `BACKOFFICE_OUTSIDE_BILLING_MONTH`.

## Entitlement and billing month

A DU becomes billable only when its governed trigger Actual End Date is present and valid.

```text
1 eligible DU record = 1 billable Hop
billing_month = YYYY-MM(trigger Actual End Date)
```

A blank trigger date is a normal non-output state: `NOT_YET_ELIGIBLE`.

## Monthly aggregation and PBOM tier

All supported Backoffice DU Models are aggregated together for one calendar month.

```text
monthly entitled hops <= 800
-> PBOM 350000592793

monthly entitled hops > 800
-> PBOM 350000592794
```

Exactly 800 uses `350000592793` even though the PR Model description says “Less Than 800”. The business boundary is explicitly inclusive.

## Main PR issuance cadence

Backoffice is issued in the following month after the billing month closes.

Examples:

```text
1-Aug -> issue July Backoffice PR
1-Sep -> issue August Backoffice PR
```

The Main PR for a billing month freezes that month's PBOM tier at issuance.

## Supplementary PR

Supplementary PR is allowed for entitlements found after the Main PR.

If the Main PR tier was frozen at `350000592793`, later supplementary entitlements continue using `350000592793` even if cumulative discovered volume later exceeds 800. The original Main PR is not amended solely because late discovery crosses the threshold.

Therefore the monthly tier source of truth is:

1. If a Main PR already exists in the external tracker for that billing month, reuse its PBOM tier.
2. Otherwise calculate the tier from all currently-known entitlements for the closed month and freeze it when Main PR is issued.

## Duplicate prevention

iEPMS has no Backoffice PR status. `TX Outsource & NOC Database.xls`, sheet `TX Outsource Details`, is the external issued-PR source of truth.

`TX NOC Details` is not part of Issue #94.

The governed duplicate identity is:

```text
Delivery Unit Code + Canonical Backoffice Event
```

Billing month, Site ID and PR filename are audit attributes, not duplicate identity.

Canonical events:

- `TX_ROLLOUT_INTEGRATION`
- `TX_ROLLOUT_DECOM`
- `CD_CONSOLIDATION_MOCN`
- `CD_CONSOLIDATION_DECOM`
- `TX_MINI_INTEGRATION`
- `BAU_2023_CUTOVER`
- `BAU_2024_CUTOVER`
- `USP_CUTOVER`
- `JENDELA_CUTOVER`
- `MW_EOS_INTEGRATION`
- `ZTE_TX_MINI_INTEGRATION`

Historical tracker SOW text is mapped to canonical event codes; free-text tracker values must not become production logic keys.

## Vendor and contract

Current commercial assignment:

```text
Operation Backoffice -> Allstar -> S1MY2024042501WBF1
NOC                 -> GCI     -> S1MY2024110601WBF2
```

Issue #94 uses Operation Backoffice only. Vendor and contract are configurable because they may change in future. The selector must not hard-code Allstar/GCI as immutable business rules.

Vendor/contract configuration must support effective dates and be resolved by Backoffice trigger Actual End Date so historical service follows the commercial arrangement effective when the service entitlement was created.

## Fail-closed and warning behavior

`REVIEW_REQUIRED`:

- Unsupported DU Model.
- CD consolidation SOW not in approved MOCN/Decom mapping.
- Required four-layer fingerprint missing or ambiguous.
- Invalid/unparseable trigger date.
- Missing Delivery Unit Code.
- External tracker unavailable/unreadable.
- Tracker duplicate identity cannot be resolved deterministically.
- Required Backoffice PBOM missing from current production PR Model.
- No valid Operation Backoffice vendor/contract for trigger date.
- For `2023 TX Rollout`, when the SOW-selected milestone is unavailable but TX Integrated evidence is available, default to TX Integrated flow and record `BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED`; do not block.
- For `CD consolidation 2023`, incompatible MOCN/Decom evidence remains `REVIEW_REQUIRED` because no fallback was approved.

Non-blocking warning:

- Unknown/new/unmatched 2023 TX Rollout SOW defaults to TX Integrated and records `BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED`.

Normal non-output:

- Correct trigger Actual End Date blank -> `NOT_YET_ELIGIBLE`.
- Duplicate already present in tracker -> `DUPLICATE_BLOCKED`.

No partial ECC is allowed for a blocked candidate set.

## Output and reconciliation

Each run must produce terminal accounting for every selected DU:

- `GENERATED`
- `DUPLICATE_BLOCKED`
- `NOT_YET_ELIGIBLE` / approved ignored reason
- `REVIEW_REQUIRED`
- `FAILED`

A monthly summary must state at least:

- billing month;
- known entitled Hop total;
- frozen/calculated tier source;
- selected PBOM;
- already issued count;
- new candidate count;
- review-required count;
- warning count;
- Main vs Supplementary mode.

## Architecture

```text
Project + DU Model profile routing
-> approved Backoffice source fingerprints
-> Backoffice trigger resolver
-> entitlement builder
-> monthly tier resolver / freeze reader
-> external tracker duplicate guard
-> effective-dated vendor/contract resolver
-> production PR Model validation
-> Operation Backoffice renderer
-> terminal reconciliation + monthly summary
```

Planning/TSS/TI selectors remain separate. Shared infrastructure may be reused, but Backoffice eligibility, tier, tracker and supplementary logic stay scope-specific.

## Safety constraints

- Production PR Model is the authoritative current baseline controlled by `config/pr_model_baseline.yaml`.
- No raw iEPMS exports or external tracker data are committed unless repository policy explicitly allows them.
- Reference files may remain local-only under `Info/reference/backoffice-pr`.
- Project + DU Model remains DU Profile routing identity; View ID is evidence only.
- Existing TSS/TI/Planning behavior must remain regression protected.
## ECC output partitioning

Each Backoffice ECC workbook may contain at most 30 unique Site IDs. Larger validated provider/contract groups are partitioned into deterministic numbered `Part N` workbooks without changing entitlement, PBOM, provider, contract, or reconciliation identity. If effective-dated provider/contract changes occur within one billing month, candidates are first partitioned by validated provider/contract. Same-day filename collisions must preserve the earlier artifact by allocating a deterministic `Batch N` suffix rather than overwriting it. Required renderer identity fields (`Site ID`, `Site Name`, `Delivery Unit Code`, `Region`) require approved Backoffice-scope source mappings.
