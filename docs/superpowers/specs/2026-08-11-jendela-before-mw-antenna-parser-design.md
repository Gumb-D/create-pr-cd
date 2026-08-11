# Jendela Before-MW Antenna Parser Design

## Scope

This design applies only to `jendela_tx_migration_pr_v1` TI decisions that require `Dismantle MW` and therefore need a Before MW antenna size from `Installation > Wireless RAN > MW Config`.

## Business Rule

`MW Config` is the source of truth for **Before MW antenna size**. `Antenna Size NE` / `Antenna Size FE` remain **After/install antenna** evidence only. Before and After evidence must never cross-fallback.

`SP`, `DP`, and `XPIC` are **optional parsing hints**, not mandatory business data. Their absence must not by itself make a record review-required.

## Parser Contract

The parser must return an antenna diameter in metres only when the value can be identified unambiguously from the MW Config structure.

1. Prefer a numeric antenna token immediately adjacent to a polarization marker (`SP`, `DP`, `XPIC`) when such markers exist.
2. When no polarization marker exists, infer from the standard MW Config sequence using the position after the frequency token and before the radio configuration token such as `1+0`, while rejecting bandwidth-like or competing numeric tokens.
3. A single structurally unambiguous antenna token may be accepted even without polarization wording. Example: `18G 1.2 1+0` -> `1.2m`.
4. A channel-width-only value such as `18G 3.5M 1+0` must not be treated as a 3.5m antenna merely because it is numerically in the antenna range.
5. Multiple complete link configurations are accepted only when every link can be parsed and all resolved antenna sizes agree. Missing, invalid, or conflicting link evidence fails closed.
6. If the parser cannot distinguish antenna size from other numeric tokens with confidence, return unresolved rather than guess.

## Required Regression Cases

Accepted:

- `18G 1.2 SP 1+0` -> `1.2`
- `18G 1.2 1+0` -> `1.2`
- `18G 112M 1.2M SP 1+0` -> `1.2`
- `18G 3.5M 1.2M SP 1+0` -> `1.2`
- `18G 1.2 SP 1+0 / 23G 1.2 DP 1+0` -> `1.2`

Rejected / unresolved:

- `18G 3.5M 1+0` when no other structure establishes that `3.5M` is an antenna diameter
- `18G 3.5M 1.2M 1+0` when both tokens remain structurally ambiguous
- `18G 0.6 SP 1+0 / 23G 1.2 SP 1+0`
- any multi-link value where one complete link has missing, nonnumeric, or invalid antenna evidence

## 4034R Acceptance

`MW Config = 18G 1.2 SP 1+0` must resolve to Before MW antenna size `1.2m`. For `TX Before Migration = MW` and `Tx SOW = BBU Patching`, the atomic TI plan remains `MW Dismantle (1.2m) + BBU Patching`.

## Safety

The parser must remain fail-closed on ambiguity. This change removes the incorrect polarization prerequisite but must not restore the earlier generic “first in-range M token wins” behavior.