# Non-Production Canonical-to-Generator Bridge Design

## Purpose

Add a local-only bridge that converts approved four-header iEPMS exports into a normalized workbook compatible with the existing PR generator input contract, without enabling ECC output or changing any DU profile lifecycle.

## Chosen approach

Use a thin bridge instead of refactoring `generate_tss_pr_ecc.py`. The bridge reuses the approved DU profile loader, exact four-layer fingerprint resolver, canonical record builder, canonical SOW registry, and existing validation rules. It produces UAT artifacts only.

## Inputs

- Original `.xlsx`, `.xlsm`, or `.csv` iEPMS export with four header rows.
- Approved DU profile path.
- Scope: `TSS` or `TI`.
- Canonical SOW registry.
- Local output directory under ignored `output/`.

## Outputs

A single `.xlsx` UAT packet with:

- `generator_input`: normalized rows using the existing generator column names.
- `uat_candidates`: records structurally ready for UAT and not blocked by duplicate status.
- `duplicate_blocked`: records whose approved scope PR-reference field is `PR_EXISTS`.
- `no_pr_required`: records marked `NO_PR_REQUIRED`.
- `review_required`: incomplete, quarantined, unsupported-SOW, or otherwise blocked records.
- `traceability`: source file, row, profile, mapping version, header hash, and classification.
- `summary`: aggregate counts and a permanent `ECC_Allowed = false` marker.

The bridge also writes a JSON summary for automation.

## Safety rules

- Accept only exact profile fingerprints.
- Require the computed Header Hash to be in the profile approved hash list.
- Reject DRAFT, PROFILED, BUSINESS_VALIDATED, DEPRECATED, and unknown profiles.
- Accept `PR_INPUT_READY` and `PRODUCTION` only for UAT packet generation; neither status allows this bridge to generate ECC.
- Never invoke or import `generate_tss_pr_ecc.py`.
- Never write outside the caller-supplied output directory.
- Never copy raw four-header workbook rows into tracked fixtures.
- Preserve `PR_EXISTS`, `NO_PR_REQUIRED`, and `NO_PR` semantics.
- Missing approved mappings, ambiguous fingerprints, missing SOW, and unsupported SOW remain fail-closed.

## Normalized generator columns

The bridge emits the legacy field names consumed by the current generator:

- `Site Code`
- `Tx SOW`
- `region`
- `Province/State`
- `Subcon - TSS`
- `Subcon - TI`
- `Existing TSS PR Status`
- `Existing TI PR Status`
- `Latitude (North Plus South Minus)`
- `Longitude (East Plus West Minus)`
- `MW Config Antenna Size NE`
- `MW Config Antenna Size FE`
- `BOQ Configuration`
- `TX SOW Details`
- `NE SOW Details`
- `FE SOW Details`
- `Source Row Number`
- `DU Profile ID`
- `DU Profile Version`
- `Mapping Version`
- `Header Hash`
- `UAT Classification`
- `UAT Blocking Reasons`
- `ECC Allowed`

## Classification

For the selected scope:

1. Canonical validation failure or unapproved SOW normalization → `REVIEW_REQUIRED`.
2. Scope PR status `PR_EXISTS` → `DUPLICATE_BLOCKED`.
3. Scope PR status `NO_PR_REQUIRED` → `NO_PR_REQUIRED`.
4. Otherwise → `UAT_CANDIDATE`.

Every output row has `ECC Allowed = false`.

## Testing

Synthetic tests cover:

- exact generator-column mapping;
- candidate, duplicate, no-PR-required, and review classification;
- strict Header Hash rejection;
- non-production ECC lock;
- workbook packet sheets and JSON summary;
- no dependency on customer exports.

A local-only real-workbook test may run when the approved ZTE TX MINI export exists, and must skip cleanly otherwise.
