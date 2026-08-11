# Issue #84 Jendela Before-MW Antenna Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Jendela MW dismantle use the existing-MW antenna size parsed from `Installation > Wireless RAN > MW Config` while preserving NE/FE exclusively for After/install antenna selection.

**Architecture:** Extend the canonical technical context with one Jendela before-MW configuration field, parse antenna size at the Jendela decision boundary, and carry the parsed value on the `Dismantle MW` work item. Reuse the current renderer's PR Model-driven antenna choose-one logic by projecting that parsed value only onto the Dismantle-MW renderer row; all other rows keep existing NE/FE semantics.

**Tech Stack:** Python 3, JSON DU Profile config, pytest/unittest-style repository tests, openpyxl-backed integration tests.

## Global Constraints

- Applies only to `jendela_tx_migration_pr_v1` / `Jendela TX Migration` TI.
- Source fingerprint is exactly `docata|ZDCSZ01022277 | Installation | Wireless RAN | MW Config`.
- `MW Config` is Before/dismantle evidence only.
- `Antenna Size NE` / `Antenna Size FE` are After/install evidence only.
- No cross-fallback between Before and After evidence.
- PR Model v4.1 baseline remains unchanged.
- Missing/unparseable Before evidence fails closed when MW dismantle requires antenna selection.

---

### Task 1: Reproduce and lock the parsing/business regression

**Files:**
- Create: `tests/test_issue_84_jendela_before_mw_antenna.py`

**Interfaces:**
- Consumes: `derive_jendela_migration_decision(...)`, canonical renderer helpers.
- Produces: failing regression for `18G 1.2 SP 1+0` and 4034R-style work plan.

- [ ] **Step 1: Write failing parser/decision tests**

Add tests asserting that a Jendela TI record with `TX Before Migration = MW`, `Tx SOW = BBU Patching`, and `before_mw_config_raw = "18G 1.2 SP 1+0"` resolves `before_mw_antenna_size_m == 1.2` on the `Dismantle MW` work item.

- [ ] **Step 2: Write failing projection test**

Assert that `Dismantle MW` renderer row receives `1.2` in its antenna inputs while the `BBU Patching` row retains the original blank NE/FE values.

- [ ] **Step 3: Run targeted test and confirm RED**

Run: `python -m pytest tests/test_issue_84_jendela_before_mw_antenna.py -q`

Expected: FAIL because the canonical field/parser/projection do not exist yet.

### Task 2: Add exact Jendela before-MW source mapping

**Files:**
- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml`
- Modify: `scripts/canonical_site_validator.py`

**Interfaces:**
- Produces: `technical_context.before_mw_config_raw` from the approved exact fingerprint.

- [ ] **Step 1: Add canonical field path/default**

Add `before_mw_config_raw` under `technical_context` and `FIELD_PATHS`.

- [ ] **Step 2: Add exact approved profile mapping**

Map `before_mw_config_raw` to field code `docata|ZDCSZ01022277`, WBS `Installation`, task `Wireless RAN`, header `MW Config`, transform `trim`, mapping status `APPROVED`.

- [ ] **Step 3: Keep the field optional at structural validation**

Do not make it a universal TI required field; the Jendela MW-dismantle business decision will fail closed only when the work plan actually requires it.

### Task 3: Parse and attach before antenna evidence to Dismantle MW

**Files:**
- Modify: `scripts/jendela_migration_decision.py`
- Modify: `scripts/du_export_adapter.py`

**Interfaces:**
- `derive_jendela_migration_decision(..., technical_context=...)` consumes raw before configuration.
- `Dismantle MW` work item produces `before_mw_config_raw` and `before_mw_antenna_size_m`.

- [ ] **Step 1: Add narrow Jendela MW-config parser**

Parse numeric antenna-size tokens while excluding GHz/frequency and topology tokens. `18G 1.2 SP 1+0` must return `1.2`; blank/unparseable returns `None`.

- [ ] **Step 2: Pass technical context into Jendela decision**

Update `du_export_adapter.py` to supply `record["technical_context"]`.

- [ ] **Step 3: Enrich only Dismantle MW**

When the work plan includes `Dismantle MW`, require a parsed before antenna size and attach it to that work item. If unavailable, return `REVIEW_REQUIRED` with a Jendela-specific before-antenna reason code. Do not inspect or fall back to NE/FE.

### Task 4: Project before antenna only onto the dismantle renderer row

**Files:**
- Modify: `scripts/create_pr_impl.py`

**Interfaces:**
- Consumes work-item `before_mw_antenna_size_m`.
- Produces row-scoped renderer inputs compatible with existing PR Model antenna selection.

- [ ] **Step 1: Keep base row unchanged**

`_renderer_row()` continues to expose actual NE/FE values from canonical technical context.

- [ ] **Step 2: Override only Dismantle MW row**

In `_renderer_rows()`, when `Migration Work Item == Dismantle MW`, set both renderer antenna size inputs to the parsed before antenna size for that row only. Do not alter MW New Link or patching rows.

- [ ] **Step 3: Run targeted test and confirm GREEN**

Run: `python -m pytest tests/test_issue_84_jendela_before_mw_antenna.py -q`

Expected: PASS.

### Task 5: Regression and release gates

**Files:**
- Existing tests only unless a regression assertion requires refinement.

- [ ] **Step 1: Run Issue #77 targeted tests**

Run: `python -m pytest tests/test_issue_77_jendela_redesign.py tests/test_issue_77_v4_1_selection.py tests/test_issue_77_jendela_profile_validation.py -q`

Expected: PASS.

- [ ] **Step 2: Run broad repository regression**

Run the repository's current full Python test command and any documented validation scripts used by PR #79.

- [ ] **Step 3: Verify no PR Model baseline changes**

Confirm `config/pr_model_baseline.yaml` and `Info/input/pr_model.xlsx` are unchanged.

- [ ] **Step 4: Open PR and request current-head Codex review**

PR body must reference `Fixes #84`, list 4034R regression evidence, and state the no-cross-fallback invariant.

- [ ] **Step 5: Resolve actionable review blockers and rerun affected tests**

Do not merge until current-head CI is clean and no unresolved actionable review blocker remains.