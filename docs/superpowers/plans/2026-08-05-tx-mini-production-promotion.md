# TX Mini Production Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `tx_mini_pr_v1` from `PR_INPUT_READY` to `PRODUCTION` without weakening the lifecycle gate or allowing blocked records into formal ECC output.

**Architecture:** Keep `scripts/create_pr.py` unchanged. The profile lifecycle declaration becomes the single production-enablement change; existing runtime gates, contract checks, mapping checks, SM exclusions, and record partitions continue to enforce fail-closed behavior. Update tests and generated lifecycle-review evidence so repository declarations remain internally consistent.

**Tech Stack:** Python 3.11, `unittest`, JSON-formatted DU profile and governance registries, GitHub Actions.

## Global Constraints

- Promote only `config/du_profiles/tx_mini_pr_v1.yaml`.
- Do not weaken or bypass the production gate from issue #39.
- Preserve both approved Header Hashes and every existing field mapping.
- Preserve UAT mode and its visibly isolated output path.
- Do not add contract mappings or modify source/customer data.
- Do not commit generated Excel or UAT output.

---

### Task 1: Add production-promotion regression expectations

**Files:**
- Modify: `tests/test_create_pr_entrypoint.py`
- Modify: `tests/test_profile_status_consistency.py`
- Modify: `tests/test_profile_readiness_review.py`

**Interfaces:**
- Consumes: `create_pr._resolve_run_mode(profile_status, non_production_uat)` and the repository TX Mini fixture/profile.
- Produces: Regression coverage proving formal TX Mini CLI output is permitted only because the resolved profile is `PRODUCTION`, while generic `PR_INPUT_READY` lifecycle calls remain blocked.

- [ ] **Step 1: Replace the TX Mini fixture formal-block test with a formal-production success test**

Assert that the official CLI succeeds without `--non-production-uat`, writes the normal production summary/output path, reports `profile_status == "PRODUCTION"`, and creates no marker-bearing UAT filenames.

- [ ] **Step 2: Update explicit UAT expectations for the same production profile**

Keep proving that `--non-production-uat` remains available and isolated, but expect `profile_status == "PRODUCTION"` because UAT mode is valid for both `PR_INPUT_READY` and `PRODUCTION` profiles.

- [ ] **Step 3: Update lifecycle consistency expectations**

Assert that the repository transition entry permits `PRODUCTION` for `tx_mini_pr_v1`; retain the existing unit test that a generic `PR_INPUT_READY` status is blocked by `_resolve_run_mode(..., False)`.

- [ ] **Step 4: Update readiness-review expectations**

Assert that TX Mini has no lifecycle blockers after promotion and that other profiles remain non-production blocked.

- [ ] **Step 5: Run the targeted tests and confirm the new expectations fail before the profile/registry implementation**

Run:

```powershell
python -m unittest `
  tests.test_create_pr_entrypoint `
  tests.test_profile_status_consistency `
  tests.test_profile_readiness_review
```

Expected: failures that show TX Mini still reports `PR_INPUT_READY` and its transition review still denies `PRODUCTION`.

### Task 2: Promote TX Mini and refresh lifecycle evidence

**Files:**
- Modify: `config/du_profiles/tx_mini_pr_v1.yaml`
- Modify: `config/registries/mw_du_profile_readiness_review.yaml`
- Modify: `config/registries/mw_du_profile_transition_review.yaml`
- Modify: `docs/MW_DU_Profile_Readiness_Review.md`
- Modify: `docs/MW_DU_Profile_Transition_Review.md`

**Interfaces:**
- Consumes: existing approved TX Mini profile mappings and Header Hashes.
- Produces: a `PRODUCTION` TX Mini profile and matching generated governance declarations.

- [ ] **Step 1: Apply the minimal profile promotion**

Change only the lifecycle status and add one concise profile note recording issue #62, the 2026-08-05 UAT, fail-closed exclusions, and business-owner production approval. Do not change mappings or Header Hashes.

- [ ] **Step 2: Regenerate readiness evidence**

Run:

```powershell
python scripts/build_profile_readiness_review.py
```

Expected for `tx_mini_pr_v1`: `profile_status == "PRODUCTION"`, no `PROFILE_NOT_PRODUCTION` blocker, and no mapping/header blockers.

- [ ] **Step 3: Regenerate transition evidence**

Run:

```powershell
python scripts/build_profile_transition_review.py
```

Expected for `tx_mini_pr_v1`: current status `PRODUCTION`; target `PRODUCTION` is eligible with no denied reasons. Other profiles retain their existing lifecycle blocks.

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m unittest `
  tests.test_create_pr_entrypoint `
  tests.test_profile_status_consistency `
  tests.test_profile_readiness_review
```

Expected: PASS.

### Task 3: Verify regression safety and open the focused PR

**Files:**
- Verify all changed files only.

**Interfaces:**
- Consumes: completed profile/test/governance changes.
- Produces: reviewed PR that closes issue #62.

- [ ] **Step 1: Run generated-packet consistency checks**

```powershell
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
```

Expected: PASS.

- [ ] **Step 2: Run the full regression suite**

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: PASS with no committed output artefacts.

- [ ] **Step 3: Review the diff**

Confirm no mapping, Header Hash, contract, policy, renderer, source export, or generated Excel changes are present.

- [ ] **Step 4: Create a focused PR**

The PR body must link `Closes #62`, report targeted/full test evidence, and state that the lifecycle gate remains unchanged for every other non-production profile.
