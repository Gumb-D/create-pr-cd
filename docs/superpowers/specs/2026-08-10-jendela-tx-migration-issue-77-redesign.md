# Issue #77 — Jendela TX Migration PR Decision Redesign

Date: 2026-08-10  
Repository: `Gumb-D/create-pr-cd`  
Scope: `Malaysia_CelcomDigi_Project` / `Jendela TX Migration` / TI only

## 1. Decision authority

This design supersedes the historical Jendela `TX Before Migration + Final Backhaul` transition matrix.

The business decision is derived only from:

1. `TX Before Migration` — dismantle work;
2. `Tx SOW` — additional work.

`Final Backhaul` remains optional source/audit evidence only. It is not required, does not select PR work, and must not cause `REVIEW_REQUIRED` when blank, missing, changed, or unexpected.

## 2. Dismantle decision

| TX Before Migration | Dismantle work |
|---|---|
| `Starlink` | `Dismantle Starlink` |
| `MW` / `Microwave` | `Dismantle MW` |
| `Fiber Own Build` | none |
| blank / unknown | `REVIEW_REQUIRED` |

## 3. Additional-work decision

| Tx SOW | Additional work |
|---|---|
| `BBU Patching` | patching |
| `MW IDU Patching` | patching |
| `BBU Patching / MW IDU Patching` | patching |
| `MW New Link / Reroute` | `MW New Link` |
| `MW by others` | none |
| `-` / blank | none |
| unsupported actionable value | `REVIEW_REQUIRED` |

The two decisions are combined into one atomic Jendela TI work plan. A failure in any selected component blocks the complete plan; no partial ECC may survive.

## 4. PR Model v4.1 evidence

Candidate workbook:

- file: `Info/input/pr_model_v4.1.xlsx`
- SHA-256: `6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f`

### Starlink dismantle

Workbook SOW is exactly `Starlink Dismanle` (spelling preserved from the approved candidate workbook).

Mandatory PBOMs:

- `350000597850` — Starlink Dismantling with 1 antenna (Cage Top)
- `350000597852` — Starlink cut over to Existing MW/IP transmission

Both must be selected exactly once.

### Patching

v4.1 contains separate SOWs:

- `BBU Patching`
- `MW IDU Patching`

For both SOWs, the mandatory business PBOM is `350001095420` (`IDU Patching for C&D Project`). `350000062748` (`MW Hardware Cutover`) is optional and is not automatically selected by this Jendela decision.

The literal source value `BBU Patching / MW IDU Patching` therefore resolves to the BBU Patching model with mandatory PBOM `350001095420`; exact `MW IDU Patching` remains mapped to its own v4.1 SOW.

### MW dismantle

Workbook SOW: `MW Dismantle`.

Mandatory selection remains model-driven:

- outbound/simple-packing geography choose-one group;
- dismantle antenna choose-one group.

Antenna selection uses the approved Jendela MW configuration evidence. No dynamic PBOM from these choose groups is hardcoded in the Jendela decision table.

### MW New Link

Workbook SOW: `MW New Link / Reroute`.

v4.1 combines New Link and Reroute rows under one visible SOW. Reroute-only rows are explicitly marked with workbook `Remarks = Reroute`.

For Jendela Issue #77:

- `MW New Link` additional work selects only the non-Reroute rows;
- it must not invoke the legacy reroute decom selector;
- dismantle remains solely controlled by `TX Before Migration`;
- ordinary non-Jendela reroute behavior remains unchanged.

The New Link mandatory groups remain model-driven:

- inbound transportation geography choose-one group;
- install antenna choose-one group.

## 5. Global guardrails

Issue #77 must preserve existing system-level controls:

- `Cancel / Drop` is the highest-priority intentional no-output state;
- `SM` is passed to another vendor and produces no subcontractor PR;
- `MW by others` produces no additional Jendela MW PR;
- duplicate PR prevention remains before rendering;
- contract validation remains mandatory;
- Project + DU Model remains the DU Profile identity route;
- View ID remains runtime layout/audit evidence, not profile identity;
- strict four-layer header evidence and header-hash validation remain in force;
- TSS behavior is not redesigned by Issue #77;
- other DU Profiles do not use the Jendela exception;
- terminal reconciliation must classify every selected site exactly once;
- any ambiguous/missing mandatory model selection fails closed.

## 6. Validation and promotion

PR Model v4.1 is a candidate until all gates pass:

1. focused Issue #77 decision and model-selection tests;
2. full repository regression with zero failures;
3. v4.0 → v4.1 change-analyzer report;
4. exact-SHA business approval covering every `REVIEW_REQUIRED` reason code;
5. atomic promotion through the Issue #75 baseline mechanism;
6. post-promotion full regression;
7. current-head PR review with no unresolved actionable blockers.

Production promotion must keep the canonical path `Info/input/pr_model.xlsx` and make v4.1 the sole current production baseline. The candidate filename must not become a second production baseline.
