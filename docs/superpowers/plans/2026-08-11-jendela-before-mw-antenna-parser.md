# Jendela Before-MW Antenna Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct PR #85 so Jendela `MW Config` resolves the Before MW / dismantle antenna size using the **largest valid supported antenna diameter**, without requiring `SP`/`DP`/`XPIC`, while remaining fail-closed on malformed or unsupported complete-link evidence.

**Architecture:** Keep `parse_jendela_before_mw_antenna_size()` as the only Jendela-specific parser. First validate the standard MW link structure and any polarization-qualified evidence. `SP`/`DP`/`XPIC` remain strong structural hints but are optional. Collect antenna diameters represented by the approved Jendela v4.1 `MW Dismantle` model from valid complete links and supported standalone evidence outside recognized link spans, then return the largest valid diameter. Unsupported bandwidth-like values do not become antenna evidence. Malformed complete links, missing/nonnumeric/unsupported polarization-qualified antenna evidence, mismatched link structure, or unmatched polarization-qualified segments remain fail-closed.

**Tech Stack:** Python 3.12, `re`, `unittest`, GitHub Actions PR Model Baseline Governance.

## Global Constraints

- Applies only to `jendela_tx_migration_pr_v1` TI Before MW / dismantle antenna evidence.
- `Installation > Wireless RAN > MW Config` is Before MW evidence only.
- `Antenna Size NE / FE` remain After/install evidence only.
- Before and After evidence never cross-fallback.
- `SP`, `DP`, `XPIC` are optional hints, never mandatory data.
- Supported dismantle diameters are exactly those represented by approved Jendela v4.1 `MW Dismantle`: `0.3`, `0.6`, `0.9`, `1.2`, `1.8`, `2.4`, `3.2` metres.
- If multiple valid supported antenna diameters are identified, use the **largest**.
- `18G 1.2 SP 1+0` must remain `1.2m` for site 4034R.
- `18G 1.2 1+0` -> `1.2m`.
- `18G 3.5M 1+0` -> unresolved because 3.5 is not an approved dismantle diameter.
- `18G 3.5M 1.2M 1+0` -> `1.2m`; the unsupported 3.5 token must not override valid 1.2m evidence.
- `18G 0.6 SP 1+0 / 23G 1.2 SP 1+0` -> `1.2m`.
- `2.4 / 18G 1.2 1+0` and `18G 1.2 1+0 / 2.4` -> `2.4m`.
- A malformed complete link such as `23G N/A SP 1+0`, a dash/missing antenna before a polarization marker, or unmatched polarization-qualified evidence must fail closed.
- Approved PR Model v4.1 workbook/baseline remains unchanged.

---

### Task 1: Lock the parser regression contract

**Files:**
- Modify: `tests/test_issue_84_jendela_before_mw_antenna.py`
- Modify/add follow-up coverage: `tests/test_issue_84_codex_final_followup.py`

**Interfaces:**
- Consumes: `parse_jendela_before_mw_antenna_size(value: Any) -> float | None`
- Produces: regression expectations for optional polarization, largest-valid selection, and fail-closed malformed evidence.

- [ ] **Step 1: Cover standard valid parsing**

Required examples:

```text
18G 1.2 SP 1+0    -> 1.2
18G 1.2 1+0       -> 1.2
18G 1.2M 1+0      -> 1.2
18GHz 1.2 1+0     -> 1.2
18 GHz 1.2 1+0    -> 1.2
18G 1,2 SP 1+0    -> 1.2
```

- [ ] **Step 2: Cover largest-valid selection**

Required examples:

```text
18G 3.5M 1.2M 1+0                   -> 1.2
18G 0.6 SP 1+0 / 23G 1.2 SP 1+0    -> 1.2
18G 0.6 1.2 1+0                     -> 1.2
2.4 / 18G 1.2 1+0                   -> 2.4
18G 1.2 1+0 / 2.4                   -> 2.4
```

The parser must not treat multiple valid supported antenna diameters as an ambiguity. Ordering must not affect the result.

- [ ] **Step 3: Cover fail-closed malformed evidence**

Required examples include:

```text
18G 3.5M 1+0                         -> None
18G 3.5M SP 1+0                      -> None
18G -1.2 SP 1+0                      -> None
18G OD1.2 SP 1+0                     -> None
18G 1.2 SP 1+0 / 23G N/A SP 1+0     -> None
18G 1.2 SP 1+0 / N/A SP              -> None
```

- [ ] **Step 4: Verify RED before production changes**

Run the relevant Issue #84 regression tests and confirm each new contract fails on the pre-fix implementation for the expected reason.

### Task 2: Implement structurally validated largest-valid selection

**Files:**
- Modify: `scripts/jendela_migration_decision.py`
- Test: `tests/test_issue_84_jendela_before_mw_antenna.py`
- Test: `tests/test_issue_84_codex_final_followup.py`

**Interfaces:**
- Consumes: raw Jendela Before `MW Config` string.
- Produces: largest valid supported Before MW antenna diameter or `None`.

- [ ] **Step 1: Define approved Jendela v4.1 dismantle diameters**

Use:

```python
_JENDELA_V41_DISMANTLE_ANTENNA_SIZES_M = frozenset(
    {0.3, 0.6, 0.9, 1.2, 1.8, 2.4, 3.2}
)
```

- [ ] **Step 2: Validate complete MW links first**

Recognize `G/GHz -> body -> N+N` link structure. Frequency/link/radio-configuration counts must remain consistent. Every `SP`/`DP`/`XPIC` marker must be covered by a recognized complete link and must have valid supported antenna evidence. Missing, nonnumeric, dash, signed/embedded, or unsupported qualified antenna evidence fails the entire value closed.

- [ ] **Step 3: Collect supported antenna evidence**

For each valid complete link:
- polarization-qualified path: collect supported antenna diameter(s) tied to the marker structure;
- unpolarized path: collect supported dismantle diameter(s) in the link body and ignore unsupported bandwidth-like numeric tokens.

Then scan supported standalone antenna candidates outside recognized link spans. Do not allow standalone evidence to rescue a malformed complete link.

- [ ] **Step 4: Select the largest valid diameter**

After structural validation succeeds:

```python
return max(valid_supported_antenna_sizes)
```

This same rule applies whether candidates came from one link, multiple links, multiple supported body tokens, or supported standalone evidence outside links.

- [ ] **Step 5: Preserve Before/After isolation**

The selected value enriches only the Jendela `Dismantle MW` work item as Before evidence. `Antenna Size NE / FE` remain After/install evidence and are never used to fill a missing Before value.

### Task 3: Final verification and review gate

**Files:**
- No additional production changes expected after verification.

**Interfaces:**
- Consumes: final PR #85 head.
- Produces: merge-gate evidence.

- [ ] **Step 1: Run standard governance workflow**

Required:

```text
PR Model baseline governance: PASS
Broad repository regression: PASS
```

- [ ] **Step 2: Inspect full logs**

Record exact test count and skips; specifically verify:
- 4034R remains 1.2m;
- largest-valid multi-link/body/standalone cases pass;
- malformed complete-link cases fail closed;
- Issue #77 behavior remains green.

- [ ] **Step 3: Resolve Codex feedback with evidence**

Reply with final head and workflow evidence only after the relevant regression is green.

- [ ] **Step 4: Request fresh Codex review**

Run `@codex review` on the final validated head and do not merge while any actionable review thread remains unresolved.
