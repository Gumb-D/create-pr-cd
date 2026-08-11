# Issue #84 — Jendela Before-MW Antenna Evidence Design

Date: 2026-08-11  
Repository: `Gumb-D/create-pr-cd`  
Scope: `Malaysia_CelcomDigi_Project` / `Jendela TX Migration` / TI only

## Problem

Production UAT site `4034R` is incorrectly classified `REVIEW_REQUIRED` with `MISSING_TI_ANTENNA_SIZE` even though the iEPMS export contains existing-MW antenna evidence:

- field code: `docata|ZDCSZ01022277`
- WBS: `Installation`
- task: `Wireless RAN`
- display header: `MW Config`
- value: `18G 1.2 SP 1+0`

The value means 18 GHz, 1.2 m antenna, single polarization, 1+0. For Jendela, the `1.2` m component is the **before/dismantle antenna size**.

## Business rule

1. Applies only to DU Profile `jendela_tx_migration_pr_v1` / DU Model `Jendela TX Migration`.
2. `Installation > Wireless RAN > MW Config` is the approved source for **Before MW Antenna Size** when `TX Before Migration = MW/Microwave` creates `MW Dismantle` work.
3. `Antenna Size NE` / `Antenna Size FE` remain **After/install antenna** evidence for `MW New Link` work.
4. Before and After antenna evidence are independent. No fallback is allowed in either direction.
5. If MW dismantle requires an antenna and `MW Config` is blank/unparseable, fail closed.
6. Patching remains antenna-independent.

## Architecture

Add one Jendela-specific canonical technical field, `before_mw_config_raw`, mapped to the exact approved four-layer fingerprint. Parse its antenna size at the Jendela decision boundary and store the parsed `before_mw_antenna_size_m` plus raw provenance on the `Dismantle MW` work item.

The canonical-to-renderer projection remains work-item scoped:

- `Dismantle MW`: project the parsed before antenna size into the renderer antenna inputs for that row only, so the existing PR Model-driven dismantle choose-one logic can be reused without changing its global behavior.
- `MW New Link`: retain the original NE/FE values only.
- Other work items: unchanged.

This row-scoped projection is an internal compatibility bridge; it does not redefine `MW Config` as an After antenna source.

## Parsing contract

The parser accepts the Jendela MW configuration format and extracts a supported numeric antenna-size token from examples such as:

`18G 1.2 SP 1+0` -> `1.2`

It must not interpret the frequency (`18G`) or topology (`1+0`) as antenna size. Blank or values with no supported antenna-size token return unresolved so the site remains fail-closed when dismantle requires it.

## 4034R regression

Input evidence:

- `TX Before Migration = MW`
- `Tx SOW = BBU Patching`
- `MW Config = 18G 1.2 SP 1+0`
- NE/FE antenna fields blank

Expected atomic Jendela TI plan:

1. `MW Dismantle`, using before antenna `1.2 m` from `MW Config`.
2. `BBU Patching`.

The site must not enter `MISSING_TI_ANTENNA_SIZE` because NE/FE are blank.

## Non-goals

- No change to Issue #77 Jendela work-plan decision matrix.
- No change to Final Backhaul behavior.
- No global change to non-Jendela antenna logic.
- No use of MW Config as After/install antenna evidence.
- No PR Model baseline/version change.

## Tests

- parser: `18G 1.2 SP 1+0` -> `1.2`;
- parser fail-closed for blank/unparseable input;
- Jendela decision enriches only `Dismantle MW` with before antenna evidence;
- renderer projection uses before antenna only on `Dismantle MW` row and preserves original NE/FE on `MW New Link` row;
- 4034R-style regression produces `MW Dismantle + BBU Patching` without missing-antenna review;
- Issue #77 targeted regression and broad TSS/TI regression remain green.