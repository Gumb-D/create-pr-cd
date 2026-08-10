# Issue #82 MW EOS Antenna Evidence Design

## Context

A production staff warning on 2026-08-10 shows `S01088-7261A / TI / MW SWAP / mw_eos_swap_pr_v1` entering `MISSING_TI_ANTENNA_SIZE`. The current renderer evaluates ordinary MW Swap antenna selection from `MW Config Antenna Size NE/FE`. The EOS profile exposes direct `MW Antenna Size NE/FE` candidates, but rows with blank direct values have no governed fallback in the ordinary MW Swap path.

Related Issue #80 already identifies the same architectural gap for TX Rollout: antenna decisions should consume approved evidence through one governed resolver rather than profile-specific ad-hoc parsing.

## Decision

Use a shared, deterministic antenna-evidence resolver at the generator boundary.

Priority for an endpoint installation size:

1. direct canonical antenna field (`MW Config Antenna Size NE/FE`);
2. endpoint-specific SOW detail (`NE SOW Details` / `FE SOW Details`) when present in canonical input;
3. no result when neither contains a supported deterministic size.

The resolver must not infer from site code, region, subcontractor, free-form unrelated fields, or a default antenna size.

For a single choose-one antenna group, when both endpoint sizes are resolved, retain the established rule of using the largest supported size. Direct evidence remains higher priority than SOW-detail fallback for each endpoint.

## Data flow

```text
DU profile mapping
  -> Canonical PR Site Record
  -> create_pr renderer row
  -> governed antenna evidence resolver
  -> existing PR-model antenna group matcher
  -> ECC row OR precise REVIEW_REQUIRED
```

The resolver returns the resolved NE/FE sizes plus evidence source labels. The existing PR-model selector remains authoritative for which PBOM row is valid.

## EOS profile boundary

Do not invent or promote an unverified EOS four-header mapping. `mw_eos_swap_pr_v1` may only add `NE SOW Details` / `FE SOW Details` fingerprints if an existing approved repository evidence source identifies those exact fingerprints. If such fingerprint evidence is unavailable in source control, the implementation must still support the canonical fields generically and leave EOS source mapping unchanged; the production case remains fail-closed until approved source evidence is supplied.

This prevents a symptom fix from weakening the DU-profile governance model.

## Error handling

- Direct size valid: use it.
- Direct size blank, SOW detail contains one supported installation size: use fallback.
- Both endpoints resolved and differ: choose largest for the existing single antenna group decision.
- One endpoint unresolved: preserve existing incomplete/missing review behavior unless the PR-model rule can be satisfied safely by the resolved evidence.
- Both unresolved or unsupported: `MISSING_TI_ANTENNA_SIZE` / existing precise downstream review reason.
- No site-specific exceptions.

## Testing

Focused unit regression tests must cover:

- direct field priority over detail text;
- `0.6` and `0.6m` normalization;
- endpoint SOW-detail fallback;
- different NE/FE sizes selecting the larger size for the group decision;
- missing/unsupported evidence remaining fail-closed;
- evidence source/provenance returned by the resolver.

A generator integration test must prove an MW Swap row with blank direct fields and valid NE/FE SOW-detail evidence no longer becomes `MISSING_TI_ANTENNA_SIZE`.

Existing MW reroute, patching, relocation, hardware-upgrade, duplicate-prevention, and direct-antenna regressions must remain green.

## Scope control

Issue #82 fixes the shared resolver capability and EOS regression path only. The broader TX Rollout NLOS and dismantle decision matrix remains owned by Issue #80 and must not be silently bundled here.