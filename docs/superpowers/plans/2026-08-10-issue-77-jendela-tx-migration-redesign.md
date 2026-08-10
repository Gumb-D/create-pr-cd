# Issue #77 — Jendela TX Migration Redesign Implementation Plan

**Goal:** Replace the historical Jendela Final-Backhaul matrix with the approved independent dismantle/additional-work decision model and promote PR Model v4.1 only after all safety gates pass.

## Task 1 — Decision contract

- Update `scripts/jendela_migration_decision.py`.
- Make `TX Before Migration` the sole dismantle selector.
- Make `Tx SOW` the sole additional-work selector.
- Keep `Final Backhaul` audit-only.
- Fail closed for unknown actionable inputs.
- Add focused decision tests.

## Task 2 — DU Profile validation

- Keep the existing Jendela source fingerprint mapping.
- Set `final_backhaul.required = false`.
- Preserve strict header/hash validation and Project + DU Model routing.
- Add profile/validator regression proving Final Backhaul cannot block output.

## Task 3 — PR Model v4.1 mapping

- Bind Starlink dismantle to `Starlink Dismanle` and exact mandatory PBOMs `350000597850` + `350000597852`.
- Bind patching to v4.1 split SOWs and mandatory PBOM `350001095420`.
- Bind MW dismantle to `MW Dismantle` with model-driven geography/antenna choose groups.
- Bind MW New Link to `MW New Link / Reroute` with model-driven inbound/antenna choose groups.
- Separate `Remarks = Reroute` TI rows so Jendela new-link work cannot inherit reroute dismantle groups.
- Preserve ordinary non-Jendela reroute behavior.

## Task 4 — Regression migration

- Replace legacy tests that derive work from `Final Backhaul`.
- Keep atomicity, PBOM uniqueness, geography, Cancel/Drop, TSS isolation, and non-Jendela guards.
- Update discovery/governance assertions so missing optional Final Backhaul is not a required-field blocker.

## Task 5 — Compatibility and approval

- Run full regression to zero failures against the existing v4.0 production baseline plus v4.1 candidate evidence.
- Run `analyze_pr_model_change.py` v4.0 → v4.1.
- Record all returned reason codes.
- Create exact-SHA Issue #77 approval evidence covering all reason codes.

## Task 6 — Atomic promotion

- Promote candidate through `promote_pr_model.py` / Issue #75 baseline mechanism.
- Keep production path `Info/input/pr_model.xlsx`.
- Update version/hash and legacy transitional mirrors atomically.
- Re-run the full regression after promotion.

## Task 7 — Review and merge

- Update PR #79 description with final validation evidence.
- Mark ready for review only after current-head checks are clean.
- Request Codex review.
- Fix every actionable blocker and rerun affected/current-head validation.
- Squash merge using expected head SHA.
- Confirm Issue #77 is closed and `main` has v4.1 as the sole production PR Model baseline.
