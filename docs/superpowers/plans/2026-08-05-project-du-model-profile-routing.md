# Project + DU Model Profile Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically discover iEPMS exports and resolve one DU Profile using canonical Project identity plus DU Model, while keeping View identity audit-only and preserving all existing PR/ECC safety controls.

**Architecture:** Add a focused iEPMS filename/source resolver that maps Project Code to Project Key and groups exports by Project + DU Model. Update the central DU resolver to use that route for normal iEPMS filenames, retain a fail-closed legacy fallback for synthetic/unlabelled fixtures, and add a v2 All-DU wrapper that converts source-root discovery into the existing proven batch engine input.

**Tech Stack:** Python 3.11, unittest, openpyxl, JSON-compatible YAML registries, GitHub Actions.

## Global Constraints

- Profile routing identity is Project Key + DU Model.
- File discovery identity is iEPMS Project Code + DU Model.
- View Name and View ID must not select the profile for a valid iEPMS filename.
- Approved Header Hash, DU Model ID, lifecycle, SOW, subcontractor, contract, duplicate, Cancel/Drop, SM, Huawei-owned, and renderer controls remain unchanged.
- Latest invalid export blocks processing; no fallback to older exports.
- No customer export or generated UAT artefact is committed.
- CD consolidation DRAFT duplicate identity remains fail-closed pending its separate business mapping consolidation.

---

### Task 1: Source identity parser and deterministic discovery

**Files:**
- Create: `scripts/iepms_export_source_resolver.py`
- Create: `tests/test_project_du_model_source_routing.py`

**Interfaces:**
- Produces: `parse_iepms_export_filename(path, registry)`, `resolve_profile_route(registry, project_key, du_model_name)`, `discover_latest_source_exports(source_roots, registry)`.

- [ ] Write tests for valid filename parsing, unknown project code, Project + DU Model routing independent of View, latest timestamp selection, and equal-timestamp ambiguity.
- [ ] Run targeted tests and confirm RED because the module does not exist.
- [ ] Implement the minimal parser/discovery module.
- [ ] Run targeted tests and confirm GREEN.

### Task 2: Central DU resolver routing

**Files:**
- Modify: `scripts/du_profile_resolver.py`
- Test: `tests/test_project_du_model_source_routing.py`

**Interfaces:**
- Consumes: parsed filename identity and registry route from Task 1.
- Produces: existing `resolve_du_profile(...)` result plus `project_code`, `project_key`, `du_model_name`, `view_name`, and `profile_selection_basis`.

- [ ] Write a failing resolver test using a valid iEPMS filename whose View Name is not registered.
- [ ] Confirm RED under the current model+View resolver.
- [ ] Route valid filenames by Project + DU Model and validate workbook DU Model ID/Header Hash afterward.
- [ ] Preserve the existing model+View fallback only for filenames without registered iEPMS identity.
- [ ] Confirm targeted resolver tests are GREEN.

### Task 3: Registry governance

**Files:**
- Modify: `config/registries/mw_du_profile_identity_registry.yaml`
- Test: `tests/test_project_du_model_source_routing.py`

**Interfaces:**
- Adds `projects[]` with Project Key, display name, and iEPMS Project Codes.
- Retains existing profile records and accepted View IDs as audit/legacy-fallback data.

- [ ] Add failing tests for duplicate Project + DU Model routes and unknown project codes.
- [ ] Add registered project aliases/codes.
- [ ] Enforce unique runnable Project + DU Model routes; fail closed on duplicates.
- [ ] Keep CD consolidation DRAFT duplicate identity explicitly blocked.

### Task 4: All-DU source-root wrapper

**Files:**
- Create: `scripts/run_all_du_ecc_uat_v2.py`
- Modify: `config/all_du_ecc_uat_manifest.template.json`
- Test: `tests/test_project_du_model_source_routing.py`

**Interfaces:**
- Accepts schema `2.0` manifest with `source_roots` and `selection_policy=LATEST_FILENAME_TIMESTAMP`.
- Produces an internal temporary schema `1.0` manifest for `all_du_uat_impl.run_batch` and writes `UAT_SOURCE_RESOLUTION.csv`.

- [ ] Write failing manifest/preflight tests.
- [ ] Implement source-root resolution without duplicating batch business logic.
- [ ] Record every candidate, selected export, timestamp, View, route, and error.
- [ ] Do not silently fall back to an older export.

### Task 5: Documentation and verification

**Files:**
- Modify: `docs/ALL_DU_ECC_UAT_RUNBOOK.md`
- Temporary: `.github/workflows/issue-58-verification.yml`

- [ ] Document schema 2.0, routing identity, source selection, errors, and legacy schema 1.0 compatibility.
- [ ] Run targeted identity/source tests.
- [ ] Run affected entrypoint and All-DU tests.
- [ ] Run the full repository test suite and record known environment-dependent failures separately.
- [ ] Remove the temporary workflow after final verification.
- [ ] Update Draft PR with exact evidence and link `Fixes #58`.
