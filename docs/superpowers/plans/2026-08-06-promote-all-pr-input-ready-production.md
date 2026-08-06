# Promote All Current PR_INPUT_READY Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the seven currently approved `PR_INPUT_READY` DU Profiles to explicit `PRODUCTION` while preserving every existing fail-closed business and data-integrity control.

**Architecture:** Keep lifecycle permission inside each Profile's explicit `status` field. Synchronize generated governance registries and Markdown evidence using the repository's existing refresh builders. Extend production-gate tests to cover the full promoted set and retain `DRAFT` blocking for CD Consolidation.

**Tech Stack:** Python 3.11+, JSON-formatted YAML configuration, unittest/pytest-compatible tests, GitHub Actions or local PowerShell verification.

## Global Constraints

- Promote exactly seven named Profiles; do not auto-promote future `PR_INPUT_READY` Profiles.
- Keep `tx_mini_pr_v1` as `PRODUCTION`.
- Keep `celcomdigi_cd_consolidation_2023_pr_v1` as `DRAFT`.
- Do not require non-production UAT evidence for this release.
- Do not weaken routing, required-field, Header Hash, mapping, duplicate, contract, Cancel/Drop, SM, Huawei-owned, partial-output, renderer, or ECC checks.
- Do not commit customer exports, generated ECC files, or UAT output.

---

### Task 1: Lock the intended lifecycle matrix

**Files:**
- Modify: `tests/test_du_profile_identity_governance.py`
- Modify: `tests/test_du_profile_loader.py`
- Modify: `tests/test_profile_status_consistency.py`
- Modify: `tests/test_profile_transition_review.py`

**Interfaces:**
- Consumes: `load_du_profile(path)` and `validate_profile_status_consistency(profile, transition_entry)`.
- Produces: Regression expectations for eight production Profiles and one DRAFT Profile.

- [ ] **Step 1: Update the lifecycle expectation test**

Assert the following exact status map:

```python
expected = {
    "tx_mini_pr_v1": "PRODUCTION",
    "tx_rollout_2023_pr_v1": "PRODUCTION",
    "mw_eos_swap_pr_v1": "PRODUCTION",
    "celcomdigi_bau_2023_pr_v1": "PRODUCTION",
    "celcomdigi_bau_2024_pr_v1": "PRODUCTION",
    "celcomdigi_usp_pr_v1": "PRODUCTION",
    "jendela_tx_migration_pr_v1": "PRODUCTION",
    "zte_tx_mini_pr_v1": "PRODUCTION",
    "celcomdigi_cd_consolidation_2023_pr_v1": "DRAFT",
}
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
python -m pytest tests/test_du_profile_identity_governance.py tests/test_du_profile_loader.py tests/test_profile_status_consistency.py tests/test_profile_transition_review.py -q
```

Expected: failures showing the seven Profiles still report `PR_INPUT_READY` and their production transitions remain denied.

- [ ] **Step 3: Commit the RED tests**

```powershell
git add tests/test_du_profile_identity_governance.py tests/test_du_profile_loader.py tests/test_profile_status_consistency.py tests/test_profile_transition_review.py
git commit -m "test(profile): require all approved profiles in production"
```

### Task 2: Promote the seven Profile files

**Files:**
- Modify: `config/du_profiles/tx_rollout_2023_pr_v1.yaml`
- Modify: `config/du_profiles/mw_eos_swap_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_bau_2024_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_usp_pr_v1.yaml`
- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml`
- Modify: `config/du_profiles/zte_tx_mini_pr_v1.yaml`

**Interfaces:**
- Consumes: Existing approved mappings, approved Header Hashes, and Project + DU Model identities.
- Produces: Explicit `status: PRODUCTION` for formal ECC gating.

- [ ] **Step 1: Change only lifecycle status and production note**

For each named Profile, replace:

```json
"status": "PR_INPUT_READY"
```

with:

```json
"status": "PRODUCTION"
```

Add a governance note recording JJ's 2026-08-06 decision that production jobs are the validation surface and non-production UAT is not a release prerequisite. Do not alter mapping versions, fingerprints, transforms, Header Hashes, or business rules.

- [ ] **Step 2: Load every Profile**

Run:

```powershell
python -m pytest tests/test_du_profile_loader.py tests/test_du_profile_identity_governance.py -q
```

Expected: status assertions pass; any remaining failure must be governance-registry drift only.

- [ ] **Step 3: Commit Profile promotion**

```powershell
git add config/du_profiles
git commit -m "feat(profile): promote all approved DU profiles to production"
```

### Task 3: Synchronize lifecycle governance

**Files:**
- Modify: `config/registries/mw_du_model_discovery_registry.yaml`
- Modify: `config/registries/mw_du_profile_deprecation_review.yaml`
- Modify: `config/registries/mw_du_profile_identity_registry.yaml`
- Modify: `config/registries/mw_du_profile_readiness_review.yaml`
- Modify: `config/registries/mw_du_profile_rollback_readiness.yaml`
- Modify: `config/registries/mw_du_profile_transition_review.yaml`
- Modify: `config/registries/mw_du_unresolved_skill_field_review.yaml`
- Modify: generated Profile readiness/transition Markdown and any other deterministic refresh output.

**Interfaces:**
- Consumes: Live Profile status and existing approved configuration.
- Produces: Registries where the seven Profiles report `PRODUCTION`, readiness is `PRODUCTION_READY` when no required blockers exist, and the `PRODUCTION` transition target is eligible.

- [ ] **Step 1: Refresh deterministic governance output**

Run:

```powershell
python scripts/refresh_mw_du_discovery_packet.py
```

- [ ] **Step 2: Verify exact lifecycle outcomes**

Run:

```powershell
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
```

Expected: both commands exit 0. Each promoted transition entry has:

```json
{
  "target_status": "PRODUCTION",
  "eligible": true,
  "denied_reasons": []
}
```

CD Consolidation remains `DRAFT` and non-production.

- [ ] **Step 3: Commit synchronized governance**

```powershell
git add config/registries docs/MW_DU_*.md
git commit -m "chore(governance): synchronize bulk production lifecycle"
```

### Task 4: Verify formal production gating

**Files:**
- Modify: `tests/test_create_pr_entrypoint.py`
- Modify: any profile-specific production-gate test that assumes only TX Mini is production.

**Interfaces:**
- Consumes: `_resolve_run_mode(status, non_production_uat)` and formal `create_pr.py` CLI.
- Produces: Proof that promoted Profiles use production mode without `--non-production-uat`, while DRAFT remains blocked.

- [ ] **Step 1: Add parameterized production lifecycle coverage**

For all eight production Profile IDs, assert their loaded status is `PRODUCTION` and `_resolve_run_mode("PRODUCTION", False)` returns `PRODUCTION`. Retain explicit assertions that `_resolve_run_mode("DRAFT", False)` and formal CD Consolidation execution are blocked.

- [ ] **Step 2: Run affected production-gate suite**

```powershell
python -m pytest tests/test_create_pr_entrypoint.py tests/test_profile_status_consistency.py tests/test_profile_transition_review.py tests/test_profile_readiness_review.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit production-gate coverage**

```powershell
git add tests
git commit -m "test(gate): cover all promoted production profiles"
```

### Task 5: Final verification and PR

**Files:**
- Verify all changed files.

**Interfaces:**
- Consumes: Completed configuration, registries, docs, and tests.
- Produces: Reviewable PR with no UAT release gate.

- [ ] **Step 1: Run targeted verification**

```powershell
python -m pytest tests/test_create_pr_entrypoint.py tests/test_du_profile_identity_governance.py tests/test_du_profile_loader.py tests/test_profile_status_consistency.py tests/test_profile_transition_review.py tests/test_profile_readiness_review.py -q
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
python -m compileall -q scripts tests
```

- [ ] **Step 2: Run broad regression**

```powershell
python -m pytest -q
```

Document any failure that reproduces on unchanged `main`; do not classify a new failure as baseline without reproducing it.

- [ ] **Step 3: Validate repository hygiene**

```powershell
git diff --check
git ls-files "Info/reference/du_exports/**"
git ls-files "output/**"
git status --short
```

Expected: no customer exports or generated ECC/UAT output tracked.

- [ ] **Step 4: Open PR**

Use title:

```text
feat(profile): promote all approved DU profiles to production
```

The PR body must list the seven promoted Profiles, state that CD Consolidation remains DRAFT, state that UAT is not a release prerequisite by business decision, and enumerate the unchanged fail-closed controls.
