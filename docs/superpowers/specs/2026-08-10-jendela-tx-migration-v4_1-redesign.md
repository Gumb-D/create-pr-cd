# Jendela TX Migration v4.1 Redesign

## Scope

This design applies only to DU Profile `jendela_tx_migration_pr_v1` / DU Model `Jendela TX Migration`.

The previous transition matrix based on `TX Before Migration + Final Backhaul` is retired. `Final Backhaul` remains optional audit evidence only and must not influence PR classification, work-item selection, or `REVIEW_REQUIRED`.

## Decision model

Jendela TI work planning is composed from two independent decisions and then combined atomically.

### 1. Existing transport dismantle

`TX Before Migration` controls dismantle work:

- `Starlink` -> `Dismantle Starlink`
  - SOW: `Starlink Dismantle (Return/MRCF included) & Migration`
  - required PBOM: `350000597850`, `350000597852`
- `MW` or `Microwave` -> `Dismantle MW`
  - SOW: `MW Dismantle`
  - downstream selection uses MW configuration evidence where the PR Model requires it
- `Fiber Own Build` -> no dismantle work
- blank or unknown value -> fail closed with `REVIEW_REQUIRED`

### 2. New / additional TX work

`Tx SOW` independently controls additional work:

- `BBU Patching / MW IDU Patching` -> patching work item mapped to the approved patching PR Model
- `MW New Link / Reroute` -> `MW New Link`, mapped to the approved MW installation/new-link PR Model; antenna size NE/FE remain conditional evidence
- `MW by others` -> no additional subcontractor PR
- `-` or blank -> no additional work
- `Cancel / Drop` -> existing global hard stop remains higher priority than Jendela work planning
- unsupported actionable values -> fail closed; do not infer from `Final Backhaul`

### 3. Atomic combination

The dismantle work list and additional work list form one Jendela TI work plan. If any required component cannot resolve to approved PR Model evidence, block the entire site and do not emit partial ECC.

Examples:

- Starlink + Patching -> Starlink dismantle + patching
- MW + MW New Link / Reroute -> MW dismantle + MW new link
- Fiber Own Build + MW New Link / Reroute -> MW new link only
- MW + blank / `-` -> MW dismantle only
- Fiber Own Build + blank / `-` -> intentional no-output

## Invariants preserved

- Project + DU Model profile routing; View ID is not identity.
- TSS behavior is unchanged by this redesign.
- Cancel / Drop hard stop.
- SM / work-by-others no-subcontractor-PR controls where already implemented.
- Huawei-owned MW Installation no subcontractor PR where already implemented.
- Duplicate prevention, contract validation, header validation, terminal-site reconciliation, and fail-closed behavior.
- PR Model baseline governance introduced by Issue #75.

## PR Model v4.1

`Info/input/pr_model_v4.1.xlsx` is candidate evidence only until Issue #77 targeted and broad regression gates pass. Candidate SHA-256: `6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f`.

Promotion to production is a separate final gate and must remain atomic.