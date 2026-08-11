# Jendela Before-MW Antenna Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct PR #85 so Jendela `MW Config` can resolve Before MW antenna size without requiring `SP`/`DP`/`XPIC`, while remaining fail-closed on bandwidth and ambiguous numeric evidence.

**Architecture:** Keep `parse_jendela_before_mw_antenna_size()` as the only Jendela-specific parser. Polarization-qualified structure remains the strongest signal. When polarization wording is absent, parse only a single candidate located between a GHz frequency token and the terminal radio configuration token (`N+N`), and accept it only if it is one of the antenna diameters supported by the approved Jendela v4.1 `MW Dismantle` model. Multiple numeric candidates or unsupported values remain unresolved.

**Tech Stack:** Python 3.12, `re`, `unittest`, GitHub Actions PR Model Baseline Governance.

## Global Constraints

- Applies only to `jendela_tx_migration_pr_v1` TI Before MW / dismantle antenna evidence.
- `Installation > Wireless RAN > MW Config` is Before MW evidence only.
- `Antenna Size NE / FE` remain After/install evidence only.
- `SP`, `DP`, `XPIC` are optional hints, never mandatory data.
- `18G 1.2 SP 1+0` must remain `1.2m` for site 4034R.
- `18G 1.2 1+0` must resolve to `1.2m`.
- `18G 3.5M 1+0` must remain unresolved.
- Ambiguous multi-token or multi-link evidence must fail closed.
- Approved PR Model v4.1 workbook/baseline remains unchanged.

---

### Task 1: Correct parser regression contract

**Files:**
- Modify: `tests/test_issue_84_jendela_before_mw_antenna.py`

**Interfaces:**
- Consumes: `parse_jendela_before_mw_antenna_size(value: Any) -> float | None`
- Produces: regression expectations for optional polarization and fail-closed unpolarized ambiguity.

- [ ] **Step 1: Replace the over-strict test**

Change the current `18G 1.2M 1+0 -> None` expectation to accepted `1.2` and add explicit accepted bare-token coverage:

```python
def test_parser_accepts_unpolarized_standard_antenna_sequence(self):
    self.assertEqual(parse_jendela_before_mw_antenna_size("18G 1.2 1+0"), 1.2)
    self.assertEqual(parse_jendela_before_mw_antenna_size("18G 1.2M 1+0"), 1.2)
```

Keep:

```python
def test_parser_fails_closed_on_unpolarized_bandwidth_only_token(self):
    self.assertIsNone(parse_jendela_before_mw_antenna_size("18G 3.5M 1+0"))
```

Add:

```python
def test_parser_fails_closed_on_multiple_unpolarized_numeric_candidates(self):
    self.assertIsNone(parse_jendela_before_mw_antenna_size("18G 3.5M 1.2M 1+0"))
```

- [ ] **Step 2: Run targeted test to verify RED**

Run:

```text
python -m unittest tests.test_issue_84_jendela_before_mw_antenna -v
```

Expected before production fix: accepted unpolarized 1.2 cases fail because current head requires polarization.

- [ ] **Step 3: Commit regression contract**

Commit message:

```text
test(issue-84): make polarization optional for MW Config antenna
```

### Task 2: Implement optional-polarization structural fallback

**Files:**
- Modify: `scripts/jendela_migration_decision.py`
- Test: `tests/test_issue_84_jendela_before_mw_antenna.py`

**Interfaces:**
- Consumes: raw `MW Config` string.
- Produces: one unambiguous Jendela Before MW antenna diameter or `None`.

- [ ] **Step 1: Define approved Jendela v4.1 dismantle diameters**

Add:

```python
_JENDELA_V41_DISMANTLE_ANTENNA_SIZES_M = frozenset({0.3, 0.6, 0.9, 1.2, 1.8, 2.4, 3.2})
```

These values correspond to the approved `MW Dismantle` choose-one rows in PR Model v4.1.

- [ ] **Step 2: Add unpolarized standard-sequence parser**

Use the GHz token and final radio configuration token as boundaries. In an unpolarized value, accept only when exactly one numeric candidate exists between those boundaries and its normalized value belongs to `_JENDELA_V41_DISMANTLE_ANTENNA_SIZES_M`. Do not select one candidate from multiple numeric tokens.

Expected behavior:

```text
18G 1.2 1+0       -> 1.2
18G 1.2M 1+0      -> 1.2
18G 3.5M 1+0      -> None
18G 3.5M 1.2M 1+0 -> None
```

- [ ] **Step 3: Preserve polarization-qualified path**

Keep existing one-to-one marker/match validation, valid range checks, multi-link agreement, invalid/nonnumeric link rejection, and 4034R parsing.

- [ ] **Step 4: Run targeted regression**

Run:

```text
python -m unittest tests.test_issue_84_jendela_before_mw_antenna -v
```

Expected: all Issue #84 tests PASS.

- [ ] **Step 5: Commit production fix**

Commit message:

```text
fix(issue-84): parse unpolarized Jendela antenna structurally
```

### Task 3: Final verification and review gate

**Files:**
- No production file changes expected.

**Interfaces:**
- Consumes: final PR #85 head.
- Produces: merge-gate evidence.

- [ ] **Step 1: Run standard governance workflow**

Expected:

```text
PR Model baseline governance: PASS
Broad repository regression: PASS
```

- [ ] **Step 2: Inspect full logs**

Record exact test count and skips; specifically verify Issue #84 accepted/rejected parser cases pass.

- [ ] **Step 3: Reply to the Codex polarization/fallback thread**

Explain that polarization is now optional and the fallback is constrained by standard sequence plus approved v4.1 antenna diameters.

- [ ] **Step 4: Resolve the addressed thread and request fresh Codex review**

Request `@codex review` against the final validated head. Do not merge while any actionable thread remains.
