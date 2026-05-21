# TI Implementation Milestone Summary - 2026-05-21

## Completed phases

### TI Phase 1

- Added TI trigger hardening.
- Implemented duplicate prevention using existing `Subcon PR - TI` status.
- Established `REVIEW_REQUIRED` handling for missing or unsafe TI cases.

### TI Phase 2A

- Added antenna-aware TI matching.
- Added mandatory choose-1 group handling.
- Added exact antenna group matching for TI model selection.

### TI Phase 2B1

- Prevented silent 0-row TI drops by writing unmatched candidates to `REVIEW_REQUIRED`.
- Preserved visibility for rows that cannot safely map to PR model items.

### TI Phase 2B2

- Added dedicated MW Reroute dual install/decom logic.
- Install/new item uses target antenna size extraction.
- Dismantle/decom item uses only decom/existing context.
- Missing or ambiguous decom antenna size is sent to `REVIEW_REQUIRED`.

## Current stable baseline

- TSS: 78 files / 2727 rows
- TI: 14 files / 234 rows
- REVIEW_REQUIRED: 163
- Duplicate skipped: 1741

## Known limitations

- MW Re-engineering remains `REVIEW_REQUIRED`.
- MW Reroute decom antenna size is unreliable and requires manual review when missing or ambiguous.
- Planning CLI is not implemented.
- Operation Backoffice CLI is not implemented.

## Recommended next phases

1. Regression test framework.
2. Planning scope CLI.
3. Operation Backoffice CLI.
4. MW Re-engineering rule definition after business confirmation.

## Scope guard

This checkpoint is documentation-only. It does not change business logic, script behavior, input files, or ECC template files.
