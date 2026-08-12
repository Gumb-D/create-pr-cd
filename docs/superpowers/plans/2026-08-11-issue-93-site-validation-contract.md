# Issue #93 Site Validation Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve fail-closed requested-site validation through the standard `create-pr-cd` Skill contract and replace the retired platform fixture with explicit regression coverage at the current ownership boundary.

**Architecture:** Site parsing, normalization, duplicate removal, and missing-site validation remain owned by `create-pr-cd`. The standard contract wrapper must translate the structured domain error emitted by `scripts/create_pr.py` into `result.json` without weakening or reimplementing the domain rule. AI Worker Platform remains a generic transport/lifecycle wrapper.

**Tech Stack:** Python 3.11+, `unittest`, standard library `subprocess`/`json`, AI Worker Platform Skill Contract 1.0.

## Global Constraints

- Preserve fail-closed `SITE_CODES_NOT_FOUND` behavior.
- Preserve `missing_site_codes` exactly as domain error details.
- Do not silently ignore explicitly requested missing sites.
- Do not move site-selection business logic into AI Worker Platform.
- Do not expose raw stderr in the Skill result.
- Keep valid case-variant/duplicate requested-site behavior covered.

---

### Task 1: Lock the requested-site behavior with regression tests

**Files:**
- Create: `tests/test_issue_93_site_selection.py`
- Modify: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `_parse_site_codes(raw: str | None) -> list[str]`, `_select_records(records, site_codes, all_sites) -> list[dict]`, `run_domain(parsed, cancellation)`.
- Produces: regression expectations for normalized/deduplicated valid site requests and structured `SITE_CODES_NOT_FOUND` propagation through the contract boundary.

- [ ] **Step 1: Add a direct happy-path regression test**

Verify `a0001,A0001,b0002` normalizes to `A0001,B0002`, removes the duplicate case variant, and selects both valid canonical records.

- [ ] **Step 2: Add a direct fail-closed regression test**

Verify a request containing `A0001,QA15_UNMATCHED` raises `CreatePrError` with code `SITE_CODES_NOT_FOUND` and `details["missing_site_codes"] == ["QA15_UNMATCHED"]`.

- [ ] **Step 3: Add a failing Skill-contract propagation test**

Mock the domain subprocess to emit the structured JSON error produced by `scripts/create_pr.py`, return exit code `1`, and assert `run_domain()` raises `ContractError` with the same domain code and missing-site details.

- [ ] **Step 4: Run focused tests and verify RED**

Run:

```text
python -m unittest tests.test_skill_contract tests.test_issue_93_site_selection -v
```

Expected before production change: direct site-selection tests pass; the contract propagation test fails because current `run_domain()` returns generic `CREATE_PR_FAILED`.

### Task 2: Preserve structured domain errors through the Skill contract

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: structured stderr payload `{status, code, message, details}` from `scripts/create_pr.py`.
- Produces: `ContractError(code, message, "domain_processing", details)` for recognized structured domain errors; retains generic `CREATE_PR_FAILED` fallback for unstructured failures.

- [ ] **Step 1: Parse only recognized structured domain-error JSON**

Read the captured stderr after non-zero domain exit. Accept a JSON object only when it declares `status: ERROR` and a non-empty `code`. Copy object-valued `details`, add the subprocess `exitCode`, and never copy raw stderr into public result details.

- [ ] **Step 2: Raise the preserved domain error before generic fallback**

When parsing succeeds, raise the translated `ContractError`. When parsing fails or stderr is unstructured, retain the existing `CREATE_PR_FAILED` path.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```text
python -m unittest tests.test_skill_contract tests.test_issue_93_site_selection -v
```

Expected: all focused tests pass.

### Task 3: Validate, integrate, and close the platform issue

**Files:**
- Potential platform submodule/approval metadata only after upstream fix is merged and exact package identity is known.

**Interfaces:**
- Consumes: merged `create-pr-cd` commit and its verified package identity.
- Produces: AI Worker Platform pin that uses the corrected Skill contract while keeping generic platform behavior.

- [ ] **Step 1: Run relevant upstream regression suite**

Run the current contract tests plus the repository's relevant existing regression suite. Confirm no production site-validation behavior changed.

- [ ] **Step 2: Review changed files and whitespace**

Confirm the diff is limited to tests, contract error translation, and this plan. Run whitespace/diff validation.

- [ ] **Step 3: Merge the upstream fix after checks are clean**

Use the repository's normal PR flow without Codex review.

- [ ] **Step 4: Update AI Worker Platform only if its approved Skill pin must move**

Update the `skills/create-pr-cd` gitlink and exact package approval metadata together; do not add platform-side site-selection logic or restore `backend/scripts/integration-test.js`.

- [ ] **Step 5: Run current platform generic Skill tests**

Verify contract submission/execution, persisted failed result, and relevant backend suite on the exact platform head.

- [ ] **Step 6: Close DemonTweeks/ai-worker-platform Issue #93**

Document that PR #92 retired the old fixture and the replacement regression now lives at the Skill ownership boundary, with the platform consuming the structured result contract.
