# Jendela TX Migration v4.1 Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy Jendela `TX Before Migration + Final Backhaul` matrix with an atomic TI work plan derived independently from `TX Before Migration` and `Tx SOW`, while keeping `Final Backhaul` non-decisional.

**Architecture:** `derive_jendela_migration_decision()` will create two independent work-item lists (dismantle and additional work) and atomically combine them. The Jendela DU Profile keeps `Final Backhaul` only as optional source evidence. Existing renderer, duplicate, contract, reconciliation, baseline-governance and non-Jendela behavior remain shared and unchanged.

**Tech Stack:** Python 3, unittest/pytest-compatible tests, JSON-formatted YAML profiles, openpyxl-backed production test fixtures already present in the repository.

## Global Constraints

- Applies only to `jendela_tx_migration_pr_v1` / `Jendela TX Migration`.
- `Final Backhaul` must not influence TI PR decisions or blocking.
- `TX Before Migration` controls dismantle work.
- `Tx SOW` controls additional work.
- Combined work plan is atomic; no partial ECC.
- TSS remains unchanged.
- Preserve Issue #75 PR Model baseline governance and do not promote v4.1 until all gates pass.

---

### Task 1: Add focused Issue #77 behavior tests

**Files:**
- Create: `tests/test_issue_77_jendela_redesign.py`
- Read: `scripts/jendela_migration_decision.py`

**Interfaces:**
- Consumes: `derive_jendela_migration_decision(profile_id, scope, pr_context)`
- Produces: regression contract for the new Jendela decision model.

- [ ] Write tests proving Final Backhaul invariance.
- [ ] Write tests for Starlink/MW/Fiber Own Build dismantle decisions.
- [ ] Write tests for patching, MW New Link/Reroute, MW by others, blank and unknown Tx SOW.
- [ ] Write tests proving non-Jendela and TSS return `None`.
- [ ] Run focused tests and confirm they fail against the legacy matrix.

### Task 2: Replace legacy Jendela transition matrix

**Files:**
- Modify: `scripts/jendela_migration_decision.py`
- Test: `tests/test_issue_77_jendela_redesign.py`

**Interfaces:**
- Consumes: `pr_context.tx_before_migration`, `pr_context.tx_sow_raw`; retains `final_backhaul` only in `source_values` if present.
- Produces: structured `migration_decision` with `classification`, `reason_code`, `decision_code`, `source_values`, `work_items`.

- [ ] Remove `_MATRIX` and introduce independent normalized mappings.
- [ ] Fail closed on missing/unknown `TX Before Migration`.
- [ ] Map patching and MW New Link/Reroute from `Tx SOW` only.
- [ ] Treat `MW by others`, blank and `-` as no additional work.
- [ ] Return intentional approved empty plan only when both decisions produce no work.
- [ ] Run focused tests and confirm pass.

### Task 3: Make Final Backhaul optional in Jendela profile

**Files:**
- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml`
- Test: `tests/test_issue_77_jendela_redesign.py`

**Interfaces:**
- Consumes: existing four-layer Final Backhaul fingerprint as optional provenance.
- Produces: profile where missing Final Backhaul cannot block PR-input readiness.

- [ ] Set `final_backhaul.required` to false.
- [ ] Update profile version/mapping version and profile notes to describe the new two-input responsibility model.
- [ ] Preserve source candidate fingerprint for audit evidence.
- [ ] Preserve all unrelated mappings and header-hash controls.

### Task 4: Retire stale Jendela regression assumptions

**Files:**
- Modify: `tests/test_human_uat_remediation_48_54.py`
- Modify if required: `tests/test_jendela_approved_pr_model.py`

**Interfaces:**
- Consumes: new Issue #77 decision contract.
- Produces: broad regression suite that no longer treats Final Backhaul as a decision input.

- [ ] Replace four-combination expectations with `TX Before Migration + Tx SOW` cases.
- [ ] Replace missing/unknown Final Backhaul failure expectations with invariance/optional evidence expectations.
- [ ] Preserve Cancel/Drop, TSS isolation, route/geography, duplicate, contract and atomic-output coverage.
- [ ] Run Jendela legacy regression files.

### Task 5: Validate integration and PR Model v4.1 compatibility

**Files:**
- Read: `Info/input/pr_model_v4.1.xlsx`
- Read: `config/pr_model_baseline.yaml`
- Use existing compatibility analyzer/promotion scripts from Issue #75.

**Interfaces:**
- Consumes: candidate SHA `6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f`.
- Produces: Issue #77 compatibility/approval evidence without bypassing regression.

- [ ] Run targeted Jendela tests.
- [ ] Run PR Model change analyzer against production v4.0 vs candidate v4.1.
- [ ] Confirm all requested work items resolve to actual candidate rows; unresolved/ambiguous items remain fail-closed.
- [ ] Run broad repository regression.
- [ ] Promote v4.1 only if compatibility/approval evidence and regression all pass.

### Task 6: Finish branch

**Files:**
- Review all Issue #77 diff.

- [ ] Verify branch contains no unrelated changes.
- [ ] Open PR referencing Issue #77.
- [ ] Review CI/review findings and fix only valid Issue #77 findings.
- [ ] Merge only after required gates pass.