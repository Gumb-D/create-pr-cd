# Issue #82 MW EOS Antenna Evidence Design

## Context

A production staff warning on 2026-08-10 shows `S01088-7261A / TI / MW SWAP / mw_eos_swap_pr_v1` entering `MISSING_TI_ANTENNA_SIZE`. The current renderer evaluates ordinary MW Swap antenna selection from `MW Config Antenna Size NE/FE`. The EOS profile exposes direct `MW Antenna Size NE/FE` candidates, but rows with blank direct values have no governed fallback in the ordinary MW Swap path.

Related Issue #80 identifies the same broader architectural need for TX Rollout: antenna decisions should consume approved evidence through one governed resolver rather than profile-specific ad-hoc parsing. Issue #82 implements only the shared installation-evidence capability and EOS MW Swap regression path; it does not absorb #80's NLOS/dismantle decision scope.

## Decision

Use a shared, deterministic antenna-evidence resolver at the generator boundary.

Evidence priority is:

1. direct canonical endpoint antenna fields (`MW Config Antenna Size NE/FE`);
2. endpoint-specific SOW details (`NE SOW Details` / `FE SOW Details`) when those canonical fields are populated;
3. governed common `TX SOW Details` as a choose-group fallback only when endpoint evidence is incomplete and the text contains explicit supported antenna installation-size evidence;
4. no result when none of the governed evidence contains a supported deterministic size.

The resolver must not infer from site code, region, subcontractor, unrelated free-text fields, or a default antenna size.

For a single choose-one antenna group, when multiple governed supported sizes are present, retain the established rule of selecting the largest supported size. Direct endpoint evidence remains higher priority than SOW-detail fallback for each endpoint.

## Data flow

```text
DU profile mapping
  -> Canonical PR Site Record
  -> create_pr renderer row
  -> governed antenna evidence resolver
  -> existing PR-model antenna group matcher
  -> ECC row OR precise REVIEW_REQUIRED
```

The resolver returns resolved endpoint/group size information plus evidence source labels. The existing PR-model selector remains authoritative for which PBOM row is valid.

## EOS profile boundary

Do not invent or promote an unverified EOS four-header mapping. Repository evidence does not provide an approved exact EOS fingerprint for `NE SOW Details` / `FE SOW Details`, so Issue #82 does not add those mappings to `mw_eos_swap_pr_v1`.

The EOS profile already exposes canonical `TX SOW Details`. The shared resolver may consume that canonical field as governed common installation-size evidence when it contains an explicit supported antenna size. Endpoint-detail fallback remains available generically for profiles that already map those fields.

This prevents a symptom fix from weakening DU-profile governance while still fixing the renderer-side evidence gap that caused false `MISSING_TI_ANTENNA_SIZE` outcomes.

## Error handling

- Direct NE/FE size valid: use direct evidence.
- Direct endpoint size blank and its endpoint SOW detail contains a supported installation size: use endpoint fallback.
- Endpoint evidence incomplete and `TX SOW Details` contains explicit supported installation-size evidence: use the largest supported common size for the existing choose-one antenna group decision without fabricating source provenance.
- Both endpoints resolved and differ: choose the largest supported size for the existing single antenna-group decision.
- Exactly one endpoint resolves and there is no governed common fallback: remain `INCOMPLETE` and preserve existing fail-closed review behavior.
- All governed evidence missing or unsupported: preserve `MISSING_TI_ANTENNA_SIZE` / the existing precise downstream review reason.
- No site-specific exception is allowed.

## Parsing guardrails

- Dedicated antenna fields support controlled forms such as `0.6`, `0.6m`, and embedded dedicated-field forms such as `18G_1.2M`.
- Detail text accepts explicit metre-suffixed sizes.
- Bare decimal sizes in detail text are accepted only near installation/antenna context.
- Unrelated large values such as VLAN IDs, radio bands, and Mbps values are not treated as antenna sizes.
- Values outside the supported antenna-diameter range are rejected.

## Testing

Focused regression coverage includes:

- direct field priority over detail text;
- `0.6` and `0.6m` normalization;
- endpoint SOW-detail fallback;
- governed common `TX SOW Details` fallback;
- different supported sizes selecting the larger size for the group decision;
- unrelated numeric text ignored;
- one-endpoint-only evidence remaining incomplete;
- missing/unsupported evidence remaining fail-closed;
- evidence source/provenance returned by the resolver;
- generator integration proving an `MW SWAP` row with blank direct antenna fields and governed common detail evidence no longer fails as `MISSING_TI_ANTENNA_SIZE`.

The integration fixture uses a previously validated Sabah coordinate so the antenna regression is not masked by the independent geography safety control.

Existing MW reroute, patching, relocation, hardware-upgrade, duplicate-prevention, and direct-antenna regressions must remain green.

## Scope control

Issue #82 fixes the shared installation antenna-evidence resolver capability and EOS MW Swap regression path only. The broader TX Rollout NLOS and dismantle decision matrix remains owned by Issue #80 and must not be silently bundled here.