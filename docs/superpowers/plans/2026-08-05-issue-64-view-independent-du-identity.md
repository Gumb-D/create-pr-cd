# Issue 64 View-Independent DU Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and execute each task in RED/GREEN order.

**Goal:** Remove View ID from DU Profile routing and output gating while preserving exact runtime audit evidence and strict structural validation.

**Architecture:** Keep raw header fingerprints and raw hashes unchanged for audit. Add a narrowly scoped structural normalization that replaces only the final View ID segment of `site|fix00012|<du_model_id>|<view_id>` before mapping comparison and structural hash validation. Route by Project + DU Model when filename identity is available, otherwise by a unique DU Model ID.

**Tech Stack:** Python 3.11, unittest, openpyxl, JSON-compatible YAML profile files.

## Global Constraints

- View ID is audit/layout evidence only and must never select, disambiguate, approve, or reject a DU Profile.
- Preserve DU Model ID, sheet name, column count/order, WBS stage, task name, display header, and every non-site field code exactly.
- Do not change profile lifecycle status, PR eligibility, SOW, subcontractor, contract, scope, duplicate, or renderer business rules.
- Do not add the reported View ID to an allowlist.
- Do not disable Header Hash validation or auto-approve arbitrary runtime hashes.

---

### Task 1: Add RED regression coverage

**Files:**
- Modify: `tests/test_project_du_model_source_routing.py`
- Modify: `tests/test_create_pr_entrypoint.py`
- Modify: `tests/test_du_export_profiler.py`
- Modify: `tests/test_du_export_adapter.py`
- Modify: `tests/test_tx_mini_negative_acceptance.py`

**Interfaces:**
- Consumes existing `resolve_du_profile`, `fingerprint_key`, `calculate_header_hash`, `resolve_profile_field_mappings`, and `evaluate_record`.
- Defines desired APIs `structural_fingerprint_key`, `calculate_structural_header_hash`, and runtime identity propagation.

- [ ] Add a worker-renamed-file test proving unseen View ID resolves by unique DU Model ID.
- [ ] Add an ambiguity test proving View ID cannot disambiguate duplicate DU Model IDs.
- [ ] Add raw-versus-structural hash tests.
- [ ] Add mapping tests proving only the site identity View suffix is normalized.
- [ ] Replace tests that expect `DU_PROFILE_VIEW_NOT_APPROVED` or `UNKNOWN_DU_MODEL_OR_VIEW`.
- [ ] Run affected tests and record expected RED failures before production changes.

### Task 2: Correct routing and shared identity parsing

**Files:**
- Modify: `scripts/profile_du_export.py`
- Modify: `scripts/du_profile_resolver.py`
- Modify: `scripts/build_du_discovery_registry.py`

**Interfaces:**
- Produce `parse_site_identity_field_code(field_code) -> dict[str, str] | None`.
- Produce `structural_fingerprint(fingerprint) -> dict[str, str]`.
- Produce `structural_fingerprint_key(fingerprint) -> str`.
- Produce `calculate_structural_header_hash(inventory) -> str`.

- [ ] Implement one strict parser for `site|fix00012|<numeric_model_id>|<numeric_view_id>`.
- [ ] Replace model+view fallback with unique-model-ID fallback.
- [ ] Fail duplicate Model ID fallback with `DU_PROFILE_IDENTITY_AMBIGUOUS`.
- [ ] Remove resolver View ID revalidation.
- [ ] Preserve detected runtime View ID in resolver output.
- [ ] Run Task 1 routing/hash tests to GREEN.

### Task 3: Correct mapping, canonical identity propagation, and PR gate

**Files:**
- Modify: `scripts/du_export_adapter.py`
- Modify: `scripts/canonical_input_pipeline.py`
- Modify: `scripts/canonical_generator_bridge_impl.py`
- Modify: `scripts/canonical_generator_bridge.py`
- Modify: `scripts/create_pr_impl.py`
- Modify: `scripts/pr_input_guard.py`

**Interfaces:**
- Mapping comparison uses `structural_fingerprint_key` while raw row lookup continues using `fingerprint_key`.
- Canonical pipelines accept detected runtime identity from resolver output.

- [ ] Match approved source candidates by structural fingerprint.
- [ ] Preserve actual workbook fingerprint in source evidence.
- [ ] Pass runtime `du_model_id` and `view_id` into canonical record construction.
- [ ] Remove View ID from `_same_model` and rename its diagnostic to model/identity-specific wording.
- [ ] Run Task 1 mapping/pipeline/guard tests to GREEN.

### Task 4: Structural hash compatibility, governance, and verification

**Files:**
- Modify: `scripts/du_profile_loader.py`
- Modify: `config/du_profiles/*.yaml` only where required for structural-hash compatibility.
- Modify: `config/registries/mw_du_profile_identity_registry.yaml` only to clarify View IDs as layout evidence.
- Modify: `tests/test_du_profile_identity_governance.py`
- Modify: relevant identity documentation.

**Interfaces:**
- Profiles may retain legacy `approved_header_hashes` while supporting controlled structural hash approval without lifecycle changes.

- [ ] Add backward-compatible structural hash configuration and validation.
- [ ] Ensure every existing approved raw layout remains accepted.
- [ ] Ensure a View-only suffix change is accepted only when its structural hash matches an approved structure.
- [ ] Run affected tests, broad repository regression, and All-DU regression.
- [ ] Open a Draft PR linked to Issue #64 with exact verification evidence and unresolved limitations.
