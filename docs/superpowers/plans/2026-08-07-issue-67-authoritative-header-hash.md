# Issue #67 Authoritative Header Hash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scope DU header-structure approval to the authoritative DU record sheet while preserving all workbook sheets in audit inventory.

**Architecture:** Keep `build_header_inventory()` unchanged as the full-workbook audit boundary. Add a fail-closed authoritative-sheet resolver used only by header hash/structure approval. Prefer explicit `export_structure.sheet_selector`; otherwise accept a single-sheet export or resolve exactly one sheet containing a strict `site|fix00012|<du_model_id>|<view_id>` identity column. Hash only selected authoritative sheets, preserving the existing View-only structural normalization from Issue #64.

**Tech Stack:** Python 3.12, openpyxl, unittest, GitHub Actions.

## Global Constraints

- Preserve full workbook/sheet inventory for audit evidence.
- Do not globally ignore any helper-sheet name such as `drop_down`.
- Fail closed when zero or multiple authoritative sheets are found in a multi-sheet workbook.
- Explicit profile `sheet_selector` takes precedence when configured and must resolve exactly.
- Existing single-sheet CSV behavior remains unchanged.
- Do not weaken Project + DU Model identity or Issue #64 View-independent structural normalization.
- Do not change lifecycle, scope, subcontractor, contract, duplicate, Cancel/Drop, SM, PR-model, renderer, or ECC business rules.

---

### Task 1: Add failing authoritative-sheet regression tests

**Files:**
- Create: `tests/test_issue_67_authoritative_header_hash.py`
- Create: `.github/workflows/issue-67-regression.yml`

**Interfaces:**
- Consumes: `build_header_inventory`, `calculate_header_hash`, `calculate_structural_header_hash`, `resolve_approved_header_structure` from `scripts/profile_du_export.py`.
- Produces: regression coverage proving helper-sheet changes do not affect approval hashes and authoritative-sheet changes do.

- [ ] **Step 1: Write the failing tests** covering: a `data` sheet with strict site identity plus a large `drop_down` sheet; helper-only mutation; authoritative header mutation; View-only identity mutation; ambiguous two-authoritative-sheet failure; single-sheet CSV stability.
- [ ] **Step 2: Run the targeted workflow and verify RED**. Expected: helper-only mutation currently changes the hash and/or ambiguous-sheet behavior is not fail-closed.
- [ ] **Step 3: Commit test/workflow evidence** without production-code changes.

### Task 2: Implement authoritative-sheet selection and scoped hashing

**Files:**
- Modify: `scripts/profile_du_export.py`
- Test: `tests/test_issue_67_authoritative_header_hash.py`

**Interfaces:**
- Produces: `resolve_authoritative_sheets(inventory, profile=None)` returning the exact sheet mappings used for structure approval.
- Existing public hash helpers keep backward-compatible call sites while gaining optional profile-aware selection.

- [ ] **Step 1: Implement minimal authoritative-sheet resolver**: explicit selector first; otherwise one-sheet fallback; otherwise exactly one sheet containing a strict site identity column; raise `ValueError` on zero/multiple candidates.
- [ ] **Step 2: Route `_header_hash`, `calculate_header_hash`, and `calculate_structural_header_hash` through selected authoritative sheets only.**
- [ ] **Step 3: Pass the profile into `resolve_approved_header_structure` hash calls** so configured `sheet_selector` is honored.
- [ ] **Step 4: Keep `build_header_inventory`, candidate discovery, and inventory Markdown full-workbook for audit/discovery.**
- [ ] **Step 5: Run targeted tests and verify GREEN.**

### Task 3: Compatibility regression and PR readiness

**Files:**
- Modify only if needed: `.github/workflows/issue-67-regression.yml`

**Interfaces:**
- Consumes the completed fix.
- Produces CI evidence for profiler, Issue #64 identity behavior, adapter behavior, and related production regressions.

- [ ] **Step 1: Run targeted Issue #67 tests plus `tests.test_du_export_profiler`, `tests.test_issue_64_view_independent_identity`, `tests.test_issue_64_layout_evidence`, and `tests.test_du_export_adapter`.**
- [ ] **Step 2: Run the repository full unittest suite if practical in CI.**
- [ ] **Step 3: Review diff for unrelated business-rule changes; expected none.**
- [ ] **Step 4: Mark PR ready only after workflows pass and no unresolved review findings remain.**
