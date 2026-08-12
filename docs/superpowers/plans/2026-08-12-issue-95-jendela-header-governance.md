# Issue #95 Jendela Header Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revalidate the 2026-08-11 Jendela iEPMS export and preserve governed header-revalidation errors through the standard Skill contract without weakening strict header validation.

**Architecture:** Keep iEPMS header governance entirely inside create-pr-cd. The new export remains blocked unless it matches an approved structure; the Skill contract only exposes a small allow-listed diagnostic envelope for the existing governed domain error.

**Tech Stack:** Python 3.11, unittest, openpyxl, Git/GitHub.

## Global Constraints

- Do not approve a new header hash merely because a production job encountered it.
- Do not weaken `header_hash_policy: strict`.
- Preserve generic redaction for unknown domain errors.
- Do not expose raw stderr, filesystem paths, workbook content, cookies, credentials, or unrestricted internal details.
- Codex is not used for development; Codex is reserved for final PR review only.

---

### Task 1: Capture governed revalidation evidence

**Files:**
- Create: `docs/issue-95-jendela-header-revalidation.md`

**Interfaces:**
- Consumes: approved profile `config/du_profiles/jendela_tx_migration_pr_v1.yaml`, approved profiler artifact hash `f45c209d...`, runtime export hash `af03e909...`.
- Produces: explicit classification of the 2026-08-11 export as wrong/different iEPMS View.

- [x] Record approved View ID `4026888666764910245` and runtime View ID `6638925130999114751`.
- [x] Record that runtime export omits approved `Tx SOW` and `Province/State` fingerprints.
- [x] Record that `SubCon - TI` and `Subcon PR - TI` retain stable field codes/display headers but move from approved RPM/PR-team WBS semantics to Installation.
- [x] Record that no production header-hash approval is added.

### Task 2: Add failing Skill-contract regression

**Files:**
- Modify: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `run_domain()` and `safe_domain_error()` behavior from `src/main.py`.
- Produces: regression test requiring governed propagation of `HEADER_HASH_REVALIDATION_REQUIRED`.

- [x] Add a test whose simulated domain error contains safe and unsafe details.
- [x] Assert the public error code remains `HEADER_HASH_REVALIDATION_REQUIRED`.
- [x] Assert only `profile_id`, `actual_header_hash`, `structural_header_hash`, `approval_basis`, and generated `exitCode` survive.
- [x] Run the single test and verify it fails because current code collapses the error to `CREATE_PR_FAILED`.

### Task 3: Implement minimal allow-list change

**Files:**
- Modify: `src/main.py`

**Interfaces:**
- Consumes: `SAFE_DOMAIN_ERROR_DETAIL_FIELDS`.
- Produces: safe propagation for one additional stable governed domain error.

- [x] Add `HEADER_HASH_REVALIDATION_REQUIRED` to the existing allow-list with exactly four raw detail fields.
- [x] Do not add Jendela-specific branching.
- [x] Run the new regression test and verify green.
- [x] Run existing unknown-domain-error test and verify raw details remain redacted.

### Task 4: Verify Jendela and contract regressions

**Files:**
- Test only.

**Interfaces:**
- Consumes: current Issue #95 branch HEAD.
- Produces: merge evidence.

- [x] Run `tests.test_skill_contract`.
- [x] Run Jendela profile/decision/header tests including issues 64, 67, 77, 84 and approved PR-model coverage.
- [x] Run repository-relevant create-pr entrypoint tests.
- [x] Confirm git diff contains only Issue #95 changes.

### Task 5: PR, review, and merge

**Files:**
- No additional production code unless review finds an actionable blocker.

**Interfaces:**
- Consumes: validated branch.
- Produces: merged PR closing Issue #95.

- [ ] Commit and push the Issue #95 branch.
- [ ] Create PR referencing/closes #95.
- [ ] Request Codex PR review only after implementation is complete.
- [ ] Resolve any actionable review blocker with local development and rerun verification.
- [ ] Squash-merge only when checks and review are clean.

