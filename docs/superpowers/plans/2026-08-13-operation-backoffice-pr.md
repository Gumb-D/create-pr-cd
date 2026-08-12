# Operation Backoffice PR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add governed Operation Backoffice PR generation for all approved DU Models with milestone-based entitlement, monthly tier freezing, external-tracker duplicate prevention, supplementary support, and terminal reconciliation.

**Architecture:** Add a Backoffice-specific trigger/entitlement layer, a tracker reader, monthly tier resolver and renderer behind the official `create_pr.py` entrypoint. Reuse Project + DU Model profile routing, four-layer fingerprint governance, PR Model baseline validation, purchasing-area mapping and terminal reconciliation infrastructure without reusing Planning-specific business decisions.

**Tech Stack:** Python 3, `unittest`, `openpyxl`, existing PR Creator canonical adapter/profile system, current PR Model v4.1 governance. Legacy `.xls` tracker reading must use an explicitly supported dependency or a deterministic adapter with tests; never silently convert the authoritative tracker in place.

## Global Constraints

- Issue #94 only; Planning remains #34 / PR #86 scope.
- Production PR Model remains `Info/input/pr_model.xlsx`, version v4.1 controlled by `config/pr_model_baseline.yaml`.
- `1 eligible DU = 1 Hop`.
- Billing month is trigger Actual End Date month.
- All supported DU Models aggregate together per calendar month.
- `<=800` -> `350000592793`; `>800` -> `350000592794`.
- Main PR is issued in the following month and freezes the billing-month tier.
- Supplementary PR is allowed and reuses the frozen Main PR tier.
- Duplicate identity is `Delivery Unit Code + Canonical Backoffice Event`.
- Unknown TX Rollout SOW defaults to TX Integrated with warning `BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED`.
- Current Backoffice vendor/contract is configurable; do not hard-code it as immutable behavior.
- No partial ECC output for blocked candidate sets.
- TDD required: every production behavior begins with a failing test that is observed before implementation.
- Local reference exports/tracker are not committed.

---

### Task 1: Backoffice business selector and trigger resolver

**Files:**
- Create: `scripts/backoffice_pr_rules.py`
- Test: `tests/test_issue_94_backoffice_rules.py`

**Interfaces:**
- Produces `resolve_backoffice_trigger(du_model_name: str, tx_sow: str) -> BackofficeTriggerDecision`.
- `BackofficeTriggerDecision` carries `status`, `event_code`, `trigger_field`, `warning_codes`, and `reason_code`.
- Produces constants for supported DU Models, event codes, PBOMs and the 800-hop boundary.

- [ ] **Step 1: Write failing tests** for all fixed DU triggers, TX Rollout Decom/Integration groups, TX unknown-SOW and unavailable-L1 Integrated fallback warning, CD consolidation MOCN/Decom groups, unknown CD SOW review, and exact-800 PBOM selection.
- [ ] **Step 2: Run** `python -m unittest tests.test_issue_94_backoffice_rules -v` and verify failures are feature-missing failures.
- [ ] **Step 3: Implement minimal pure rule module** with dataclasses/constants and deterministic normalization.
- [ ] **Step 4: Re-run targeted tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(backoffice): add governed trigger and tier rules`.

### Task 2: Canonical Backoffice fields and DU Profile mappings

**Files:**
- Modify: `scripts/canonical_site_validator.py`
- Modify: `scripts/du_export_adapter.py`
- Modify: `scripts/canonical_input_pipeline.py`
- Modify: `scripts/du_profile_resolver.py`
- Modify: `config/du_profiles/*.yaml` only for approved Backoffice fields/fingerprints
- Test: `tests/test_issue_94_backoffice_profile_fields.py`
- Test: `tests/test_issue_94_backoffice_canonical.py`

**Interfaces:**
- Canonical record exposes raw SOW, Delivery Unit Code and governed Backoffice trigger actual-date evidence required by `backoffice_pr_runtime.py`.
- Scope name is `BACKOFFICE`.

- [ ] **Step 1: Profile the local nine DU reference exports read-only** and record exact four-layer fingerprints for required trigger fields/SOW/DU code; do not commit raw exports.
- [ ] **Step 2: Write failing tests** proving each production profile resolves only the approved Backoffice fingerprints and that missing/ambiguous required evidence fails closed.
- [ ] **Step 3: Run profile/canonical tests** and observe expected failures.
- [ ] **Step 4: Implement minimum canonical/profile changes** following existing Planning/TSS/TI patterns without changing their required-field semantics.
- [ ] **Step 5: Re-run tests** and verify PASS.
- [ ] **Step 6: Commit** `feat(backoffice): add governed canonical trigger evidence`.

### Task 3: External tracker adapter and duplicate identity

**Files:**
- Create: `scripts/backoffice_tracker.py`
- Modify: `requirements.txt` only if a maintained legacy `.xls` reader is required
- Test: `tests/test_issue_94_backoffice_tracker.py`

**Interfaces:**
- Produces `load_backoffice_tracker(path: Path) -> BackofficeTrackerSnapshot`.
- Snapshot exposes issued entitlement keys `(delivery_unit_code, event_code)` and billing-month Main PR PBOM evidence.
- Reader consumes `TX Outsource Details` only; `TX NOC Details` is ignored.

- [ ] **Step 1: Inspect the real local tracker read-only** to confirm sheet/header positions and historical SOW/File Name/PBOM conventions.
- [ ] **Step 2: Write failing fixture-based tests** for historical SOW-to-event mapping, DU+event duplicate identity, NOC exclusion, unreadable/missing tracker fail-closed behavior, and Main-PR PBOM evidence extraction.
- [ ] **Step 3: Run tests** and observe expected failures.
- [ ] **Step 4: Implement the minimum deterministic tracker reader**. If `.xls` support needs `xlrd`, pin an appropriate dependency and test it; never mutate/convert the source tracker in place.
- [ ] **Step 5: Re-run tests** and verify PASS.
- [ ] **Step 6: Commit** `feat(backoffice): add external tracker duplicate guard`.

### Task 4: Entitlement, monthly tier freeze and supplementary runtime

**Files:**
- Create: `scripts/backoffice_pr_runtime.py`
- Create: `config/backoffice_service_registry.yaml`
- Test: `tests/test_issue_94_backoffice_runtime.py`

**Interfaces:**
- Produces `build_backoffice_entitlements(records, billing_month, tracker_snapshot, service_registry)`.
- Produces partitions `candidates`, `duplicates`, `ignored`, `review_required` plus monthly summary metadata.
- Candidate records carry `backoffice_selection` with event, trigger date, billing month, PBOM, quantity=1, unit=`Hop`, subcontractor and contract.

- [ ] **Step 1: Write failing tests** for eligibility, blank trigger normal ignore, duplicate tracker block, main-month tier calculation at 800/801, supplementary frozen-tier reuse, effective-dated vendor/contract lookup, and invalid contract review.
- [ ] **Step 2: Run runtime tests** and observe expected failures.
- [ ] **Step 3: Implement minimal runtime** using pure rules + tracker snapshot; Main vs Supplementary is determined from tracker Main-PR evidence.
- [ ] **Step 4: Re-run tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(backoffice): add monthly entitlement runtime`.

### Task 5: Operation Backoffice ECC renderer

**Files:**
- Create: `scripts/backoffice_ecc_renderer.py`
- Test: `tests/test_issue_94_backoffice_renderer.py`

**Interfaces:**
- Accepts already-gated canonical Backoffice candidates.
- Revalidates governed Backoffice selection at renderer boundary.
- Generates one Main or Supplementary Backoffice ECC batch for the requested billing month with the frozen/calculated monthly PBOM.

- [ ] **Step 1: Write failing renderer tests** for ECC column values, Allstar/current configured contract, PBOM/Qty/Unit, no mixed monthly PBOM, supplementary naming/audit marker, and atomic no-output on invalid row.
- [ ] **Step 2: Run renderer tests** and observe expected failures.
- [ ] **Step 3: Implement minimal deterministic renderer** using current repository output conventions and xlsx output.
- [ ] **Step 4: Re-run tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(backoffice): render monthly operation backoffice ECC`.

### Task 6: Official entrypoint and reconciliation integration

**Files:**
- Modify: `scripts/create_pr.py`
- Modify: `scripts/create_pr_impl.py` only where shared invocation arguments are unavoidable
- Modify: `scripts/renderer_reconciliation.py` only if Backoffice artifact naming needs governed recognition
- Test: `tests/test_issue_94_backoffice_entrypoint.py`
- Test: `tests/test_issue_94_backoffice_reconciliation.py`

**Interfaces:**
- `scripts/create_pr.py --scope Backoffice` is the only governed production entrypoint.
- Adds explicit tracker/billing-month inputs required for Backoffice, without making them required for TSS/TI/Planning.

- [ ] **Step 1: Write failing CLI/integration tests** for scope choice, required tracker + closed billing month, following-month Main cadence, supplementary allowance, renderer routing and terminal reconciliation.
- [ ] **Step 2: Run tests** and observe expected failures.
- [ ] **Step 3: Implement minimum wrapper integration** while leaving existing scope routing unchanged.
- [ ] **Step 4: Re-run tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(backoffice): enable governed official entrypoint`.

### Task 7: Real-reference UAT and regression hardening

**Files:**
- Create: `tests/test_issue_94_backoffice_end_to_end.py`
- Create: `scripts/run_backoffice_uat.py` if a reusable local-only UAT harness is needed
- Modify documentation only after tests pass.

**Interfaces:**
- Uses local files under `Info/reference/backoffice-pr` or explicitly supplied absolute reference paths.
- Produces local-only UAT evidence; raw customer/reference data is not committed.

- [ ] **Step 1: Add failing end-to-end tests/fixtures** that cover all 11 trigger scenarios across the 9 DU Models, tracker duplicate suppression, exact-800/801 Main PR, unknown TX SOW warning, CD unknown SOW review and supplementary tier freeze.
- [ ] **Step 2: Run targeted E2E** and observe failures before any fixes.
- [ ] **Step 3: Fix only behavior exposed by failing tests** and re-run until PASS.
- [ ] **Step 4: Run all Issue #94 tests**: `python -m unittest discover -s tests -p "test_issue_94_*.py"`.
- [ ] **Step 5: Run existing Planning targeted tests** and TSS/TI regression suites.
- [ ] **Step 6: Run full repository test suite**. Record the pre-existing Windows-only PR Model promotion path-separator assertion separately if still present and verify GitHub/Linux CI as authoritative for that baseline defect.
- [ ] **Step 7: Commit** `test(backoffice): add all-DU UAT and regression coverage`.

### Task 8: Documentation, issue evidence and PR

**Files:**
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `knowledge_base/*` only where current scope/status documentation requires it
- Modify: `docs/superpowers/specs/2026-08-13-operation-backoffice-pr-design.md` only for implementation-verified clarifications

**Interfaces:**
- Documentation reflects implemented behavior exactly and keeps Planning/TSS/TI boundaries explicit.

- [ ] **Step 1: Update docs** with Backoffice CLI, monthly cadence, tier freeze, supplementary rules, tracker requirement and warning/review semantics.
- [ ] **Step 2: Run documentation/governance tests** relevant to README/SKILL/KB consistency.
- [ ] **Step 3: Commit** `docs(backoffice): document operation backoffice workflow`.
- [ ] **Step 4: Push branch and open PR** referencing `Closes #94`.
- [ ] **Step 5: Inspect GitHub Actions, PR conversation, reviews and mergeability**; fix every actionable blocker test-first.
- [ ] **Step 6: Re-run current-head validation** after any review changes.
- [ ] **Step 7: Squash merge with expected head SHA** only when current-head checks are clean and no actionable review blocker remains.
- [ ] **Step 8: Confirm Issue #94 is closed completed and main contains the merge commit**.

