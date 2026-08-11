# Jendela Before-MW Antenna Parser Design

## Scope

This design applies only to `jendela_tx_migration_pr_v1` TI decisions that require `Dismantle MW` and therefore need a Before MW antenna size from `Installation > Wireless RAN > MW Config`.

## Business Rule

`MW Config` is the source of truth for **Before MW antenna size**. `Antenna Size NE` / `Antenna Size FE` remain **After/install antenna** evidence only. Before and After evidence must never cross-fallback.

`SP`, `DP`, and `XPIC` are **optional parsing hints**, not mandatory business data. Their absence must not by itself make a record review-required.

When more than one valid Before MW antenna diameter can be identified from the MW Config, the business rule is to use the **largest valid antenna size** for the MW Dismantle selection. Different valid antenna sizes are therefore not, by themselves, a review-required ambiguity.

## Parser Contract

The parser must identify valid Jendela v4.1 MW Dismantle antenna diameters from MW Config structure and return the largest valid diameter found.

1. Prefer numeric antenna tokens structurally associated with polarization markers (`SP`, `DP`, `XPIC`) when such markers exist.
2. When no polarization marker exists, infer antenna candidates from the standard MW Config sequence between the frequency token and the radio configuration token such as `1+0`.
3. A structurally valid antenna token may be accepted without polarization wording. Example: `18G 1.2 1+0` -> `1.2m`.
4. Bandwidth-only values such as `3.5M` must not be treated as antenna diameters merely because they are numeric.
5. When multiple valid antenna diameters are identified, return the maximum. Example: `18G 0.6 SP 1+0 / 23G 1.2 SP 1+0` -> `1.2m`.
6. Invalid, missing, malformed, or nonnumeric antenna evidence in a complete MW link remains fail-closed; the maximum rule applies only to successfully identified valid antenna diameters.
7. Standalone smaller numeric content outside a valid MW link does not invalidate a larger valid link result. The production source is not expected to emit hybrid values such as `18G 1.2 1+0 / 0.6`; if encountered, the larger valid antenna result remains authoritative.

## Required Regression Cases

Accepted:

- `18G 1.2 SP 1+0` -> `1.2`
- `18G 1.2 1+0` -> `1.2`
- `18G 112M 1.2M SP 1+0` -> `1.2`
- `18G 3.5M 1.2M SP 1+0` -> `1.2`
- `18G 0.6 SP 1+0 / 23G 1.2 SP 1+0` -> `1.2`
- `18G 0.6 1.2 1+0` -> `1.2`
- `18G 3.5M 1.2M 1+0` -> `1.2`
- `18G 1.2M 1.20M 1+0` -> `1.2`
- `18G 1.2 1+0 / 0.6` -> `1.2`
- `0.6 / 18G 1.2 1+0` -> `1.2`

Rejected / unresolved:

- `18G 3.5M 1+0` when the only numeric body token is a non-supported bandwidth value
- any complete MW link with missing, nonnumeric, malformed, or unsupported antenna evidence
- signed or identifier-embedded antenna candidates such as `-1.2`, `+1.2`, or `OD1.2`

## 4034R Acceptance

`MW Config = 18G 1.2 SP 1+0` must resolve to Before MW antenna size `1.2m`. For `TX Before Migration = MW` and `Tx SOW = BBU Patching`, the atomic TI plan remains `MW Dismantle (1.2m) + BBU Patching`.

## Safety

The parser must never let bandwidth, malformed, missing, or unsupported evidence masquerade as a valid antenna diameter. The maximum-selection rule operates only across valid antenna candidates represented by the approved Jendela v4.1 MW Dismantle model.
