# Issue #82 MW EOS Antenna Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent valid MW EOS `MW SWAP` TI sites from entering false `MISSING_TI_ANTENNA_SIZE` when approved canonical endpoint SOW-detail evidence contains the antenna size.

**Architecture:** Add a small shared antenna-evidence resolver used by the ordinary MW antenna selection path. Preserve direct canonical antenna fields as first priority, use endpoint-specific SOW details only as deterministic fallback, retain existing PR-model matching, and leave unsupported/missing evidence fail-closed. Do not invent new EOS header fingerprints without approved repository evidence.

**Tech Stack:** Python 3, unittest, existing pandas/openpyxl generator fixtures, GitHub Actions.

## Global Constraints

- No site-specific hard-coding.
- No guessed/default antenna size.
- Direct antenna evidence has priority over SOW-detail fallback.
- Existing PR Model remains authoritative for PBOM selection.
- Do not bundle Issue #80 NLOS/dismantle scope into Issue #82.
- Keep unsupported/missing evidence fail-closed.

---

### Task 1: Lock the regression in tests

**Files:**
- Create: `tests/test_antenna_evidence_resolver.py`
- Modify: `tests/test_ti_sow_matching.py`
- Create: `.github/workflows/issue-82-regression.yml`

**Interfaces:**
- Consumes: existing generator CLI in `scripts/generate_tss_pr_ecc.py`.
- Produces: expected resolver interface `resolve_installation_antenna_evidence(row) -> dict` and failing MW Swap integration coverage.

- [ ] **Step 1: Write failing unit tests** for direct-priority, `0.6`/`0.6m`, endpoint SOW-detail fallback, largest-size decision, provenance, and missing evidence.
- [ ] **Step 2: Extend the generator fixture columns** with `NE SOW Details` and `FE SOW Details`, then add an `MW SWAP` row with blank direct antenna fields but valid endpoint detail evidence.
- [ ] **Step 3: Add an issue-specific GitHub Actions workflow** running the focused tests on pull request / branch updates.
- [ ] **Step 4: Open a draft PR and verify RED**: focused CI must fail because the resolver/fallback behavior is not implemented yet.

### Task 2: Implement the shared resolver

**Files:**
- Create: `scripts/antenna_evidence_resolver.py`
- Modify: `scripts/generate_tss_pr_ecc.py`

**Interfaces:**
- `resolve_installation_antenna_evidence(row: Mapping[str, Any]) -> dict`
- Result keys: `ne_size`, `fe_size`, `selected_size`, `ne_source`, `fe_source`, `status`.

- [ ] **Step 1: Reuse existing supported antenna parsing semantics** rather than introducing a second incompatible unit parser.
- [ ] **Step 2: Resolve each endpoint** from direct field first, endpoint SOW detail second.
- [ ] **Step 3: Return `selected_size=max(resolved endpoint sizes)`** when at least one supported endpoint value exists; retain source labels.
- [ ] **Step 4: Wire ordinary antenna-required TI selection** to the resolver before calling the existing PR-model group matcher.
- [ ] **Step 5: Preserve existing REVIEW_REQUIRED behavior** when resolver status is missing/unsupported.
- [ ] **Step 6: Run focused CI and verify GREEN.**

### Task 3: Verify canonical/EOS governance boundary

**Files:**
- Inspect: `config/du_profiles/mw_eos_swap_pr_v1.yaml`
- Inspect: discovery registries/docs containing the approved EOS header inventory.
- Modify profile only if exact approved fingerprints for `NE SOW Details` / `FE SOW Details` already exist in repository evidence.

**Interfaces:**
- Consumes: four-layer header fingerprint governance.
- Produces: either an evidence-backed profile mapping or an explicit no-profile-change decision documented in the PR.

- [ ] **Step 1: Search repository evidence for exact EOS endpoint SOW-detail fingerprints.**
- [ ] **Step 2: If exact approved fingerprints exist, add them with provenance and profile tests.**
- [ ] **Step 3: If they do not exist, leave the profile unchanged and document that the resolver is ready but production fallback requires approved source mapping.**

### Task 4: Current-head verification and review

**Files:**
- Modify tests/docs only if verification identifies a defect.

**Interfaces:**
- Produces: merge-ready PR with no actionable review blocker.

- [ ] **Step 1: Run focused issue-82 tests in GitHub Actions.**
- [ ] **Step 2: Run available repository governance/check workflows on current head.**
- [ ] **Step 3: Request Codex review.**
- [ ] **Step 4: Inspect PR conversation, inline threads, review submissions, mergeability, and current-head checks.**
- [ ] **Step 5: Resolve every actionable Codex blocker with regression coverage and rerun current-head validation.**
- [ ] **Step 6: Request a fresh Codex review when code changes after review.**
- [ ] **Step 7: Squash-merge only when current head is clean and no actionable blocker remains; confirm Issue #82 closes completed.**