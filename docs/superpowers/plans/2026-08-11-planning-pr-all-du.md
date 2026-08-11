# All-DU Planning PR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a production-safe `Planning` PR scope for all eight supported DU Models using approved `Subcon Planning` / `Subcon PR - Planning` fields and the deterministic PBOM decision matrix from Issue #34.

**Architecture:** Extend the canonical DU adapter with Planning-specific canonical fields, then add one isolated Planning selector that receives only canonical values and returns exactly one approved PBOM or a fail-closed reason. Reuse the existing contract, lifecycle, output, reconciliation and duplicate-prevention infrastructure instead of adding DU-specific Planning generators.

**Tech Stack:** Python 3, `openpyxl`, existing DU Profile YAML/JSON configuration, `unittest`/repository test harness, current ECC renderer and reconciliation utilities.

## Global Constraints

- Support exactly these DU Models initially: `2023 TX Rollout`, `TX Mini Project`, `2023 Celcomdigi BAU`, `2024 Celcomdigi BAU`, `Celcomdigi USP`, `Jendela TX Migration`, `MW EOS Swap`, `ZTE TX MINI`.
- `TX Planning Remarks` must not participate in Planning eligibility or line-item selection.
- `GCI_AA` and `GTSB_AA` map to contract identities `GCI` and `GTSB` respectively.
- `_AA` always selects only `350001042321`; never combine it with `350001143904` or `350001143905`.
- `GCI`/`GTSB` select `350001143904` for the five approved full-planning DU Models and `350001143905` for the remaining three supported DU Models.
- Quantity is `1` and unit is `Hop` for all Planning items.
- Contract and Purchasing Area remain governed by `Info/input/contract_info_reference.md`.
- No raw iEPMS export is committed.
- All unsafe or ambiguous cases fail closed; no partial ECC for a blocked site.
- Existing TSS/TI behavior must remain unchanged.
- No Codex review or Codex implementation workflow is used for Issue #34; implementation is performed in the current ChatGPT workflow.

---

### Task 1: Lock Planning business rules in governed knowledge and acceptance specs

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `knowledge_base/pr_creator/rules/pr_creator_rule_register.yaml`
- Modify: `knowledge_base/pr_creator/validation/acceptance_questions.yaml`
- Modify: `knowledge_base/pr_creator/governance/known_divergences.md`
- Reference: `docs/superpowers/specs/2026-08-11-planning-pr-all-du-design.md`

**Interfaces:**
- Consumes: Business-approved Issue #34 Planning decision matrix.
- Produces: Unambiguous documentation and machine-readable acceptance requirements for later runtime work.

- [ ] **Step 1: Replace stale Planning PBOM documentation**

Update the existing Planning section so it states:

```text
GCI/GTSB + {2023 TX Rollout, 2023 Celcomdigi BAU, 2024 Celcomdigi BAU, Celcomdigi USP, Jendela TX Migration}
-> 350001143904

GCI/GTSB + {TX Mini Project, MW EOS Swap, ZTE TX MINI}
-> 350001143905

GCI_AA/GTSB_AA + any supported DU
-> 350001042321 only
```

Delete the stale `350001000403` Planning rule.

- [ ] **Step 2: Record the `_AA` exception to the global optional-item rule**

The global rule must explicitly allow only this deterministic Planning exception:

```text
Planning GCI_AA/GTSB_AA -> optional PBOM 350001042321
```

All unrelated optional-item auto-selection remains prohibited.

- [ ] **Step 3: Record Planning acceptance questions**

Add deterministic scenarios covering:

```text
five-DU 350001143904 matrix
three-DU 350001143905 matrix
all-DU _AA 350001042321-only matrix
_AA contract normalization
TX Planning Remarks ignored
blank Planning subcon ignored
existing Planning PR prevents duplicate
unknown Planning subcon fails closed
```

- [ ] **Step 4: Keep runtime boundary explicit**

Documentation must continue to state that the CLI supports only TSS/TI until later tasks make Planning executable.

- [ ] **Step 5: Validate the governed documents**

Run repository YAML parsing/consistency tests plus a text search proving `350001000403` is no longer an active Planning rule.

- [ ] **Step 6: Commit**

```bash
git add SKILL.md README.md knowledge_base/pr_creator docs/superpowers/specs/2026-08-11-planning-pr-all-du-design.md docs/superpowers/plans/2026-08-11-planning-pr-all-du.md
git commit -m "docs(issue-34): define all-DU Planning PR rules"
```

---

### Task 2: Add canonical Planning fields to DU profiles and adapter

**Files:**
- Modify: `config/du_profiles/tx_rollout_2023_pr_v1.yaml`
- Modify: `config/du_profiles/tx_mini_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_bau_2024_pr_v1.yaml`
- Modify: `config/du_profiles/celcomdigi_usp_pr_v1.yaml`
- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml`
- Modify: `config/du_profiles/mw_eos_swap_pr_v1.yaml`
- Modify: `config/du_profiles/zte_tx_mini_pr_v1.yaml`
- Modify: `scripts/du_export_adapter.py`
- Modify: `scripts/canonical_site_validator.py`
- Test: `tests/test_issue_34_planning_profile_fields.py`

**Interfaces:**
- Produces canonical fields `subcontractor_planning` and `existing_planning_pr_status` with source evidence.
- Planning selector in Task 3 consumes these values plus canonical DU Model identity.

- [ ] **Step 1: Write failing profile-field tests**

For all eight production profiles, assert that Planning source candidates resolve uniquely against representative governed header evidence and that `TX Planning Remarks` is not declared as a required Planning selector input.

- [ ] **Step 2: Run targeted tests and verify failure**

```bash
python -m unittest tests.test_issue_34_planning_profile_fields -v
```

Expected: FAIL because Planning canonical mappings are incomplete/not enforced across all eight profiles.

- [ ] **Step 3: Add approved Planning mappings to profiles**

Use the four-layer Header Fingerprints evidenced by the local `Info/reference/planning-pr/` exports. Do not add view-based identity routing.

- [ ] **Step 4: Extend canonical adapter/validator minimally**

Add only the two Planning business fields needed for this scope. Preserve TSS/TI required-field behavior by making scope-specific validation explicit.

- [ ] **Step 5: Run targeted and existing DU adapter tests**

```bash
python -m unittest tests.test_issue_34_planning_profile_fields tests.test_du_export_adapter tests.test_du_profile_loader -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add config/du_profiles scripts/du_export_adapter.py scripts/canonical_site_validator.py tests/test_issue_34_planning_profile_fields.py
git commit -m "feat(issue-34): map Planning fields across supported DU profiles"
```

---

### Task 3: Implement isolated Planning line-item selector

**Files:**
- Create: `scripts/planning_pr_selector.py`
- Test: `tests/test_issue_34_planning_selector.py`

**Interfaces:**
- Consumes: `du_model_name: str`, `subcontractor_planning: str`.
- Produces a structured result containing `status`, `pbom_code`, `quantity`, `unit`, `contract_subcontractor`, and optional review reason.

- [ ] **Step 1: Write the failing decision-matrix tests**

Cover every supported DU in both standard and `_AA` modes, for example:

```python
result = select_planning_item("2023 TX Rollout", "GCI")
assert result.pbom_code == "350001143904"

result = select_planning_item("MW EOS Swap", "GTSB")
assert result.pbom_code == "350001143905"

result = select_planning_item("MW EOS Swap", "GCI_AA")
assert result.pbom_code == "350001042321"
assert result.contract_subcontractor == "GCI"
```

Also assert unknown DU/subcon fail closed.

- [ ] **Step 2: Run selector tests and verify failure**

```bash
python -m unittest tests.test_issue_34_planning_selector -v
```

Expected: FAIL because selector module does not exist.

- [ ] **Step 3: Implement the minimal pure selector**

Use explicit immutable DU sets; do not infer from SOW/remarks:

```python
FULL_PLANNING_DUS = frozenset({...five names...})
SINGLE_HOP_PLANNING_DUS = frozenset({...three names...})
```

Normalize only whitespace/case as needed; `_AA` must be an exact approved suffix/value branch, not fuzzy matching.

- [ ] **Step 4: Prove TX Planning Remarks cannot affect selection**

Keep the selector signature free of a Planning Remarks parameter and add a test at the caller boundary showing changed remarks yield the same result.

- [ ] **Step 5: Run selector tests**

```bash
python -m unittest tests.test_issue_34_planning_selector -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/planning_pr_selector.py tests/test_issue_34_planning_selector.py
git commit -m "feat(issue-34): add deterministic Planning item selector"
```

---

### Task 4: Add Planning eligibility and duplicate-prevention flow

**Files:**
- Modify: `scripts/create_pr.py`
- Modify: `scripts/create_pr_impl.py`
- Modify: `scripts/pr_input_guard.py`
- Test: `tests/test_issue_34_planning_eligibility.py`

**Interfaces:**
- Consumes canonical Planning fields from Task 2 and selector from Task 3.
- Produces terminal site outcomes: generated, ignored/skipped duplicate, or review-required.

- [ ] **Step 1: Write failing eligibility tests**

Cover:

```text
blank Planning subcon -> ignored/no output
GCI/GTSB + blank Planning PR status -> eligible
GCI_AA/GTSB_AA + blank Planning PR status -> eligible
nonblank Planning PR status/number -> duplicate skip/no output
unknown nonblank Planning subcon -> REVIEW_REQUIRED/no ECC
```

- [ ] **Step 2: Verify tests fail**

```bash
python -m unittest tests.test_issue_34_planning_eligibility -v
```

- [ ] **Step 3: Add `Planning` as an internal supported scope path**

Wire eligibility without altering TSS/TI conditions. Do not yet remove the production CLI enablement gate until the end-to-end path is proven.

- [ ] **Step 4: Reuse existing terminal reconciliation semantics**

Every requested Planning site must resolve to one terminal outcome with no silent loss.

- [ ] **Step 5: Run targeted safety tests**

```bash
python -m unittest tests.test_issue_34_planning_eligibility tests.test_create_pr_entrypoint tests.test_create_pr_safety_integration tests.test_issue_74_reconciliation -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/create_pr.py scripts/create_pr_impl.py scripts/pr_input_guard.py tests/test_issue_34_planning_eligibility.py
git commit -m "feat(issue-34): add Planning eligibility and duplicate guard"
```

---

### Task 5: Render Planning ECC using shared contract/output infrastructure

**Files:**
- Modify: `scripts/generate_tss_pr_ecc.py` or the current shared renderer boundary identified during implementation
- Modify: `scripts/create_pr_impl.py`
- Test: `tests/test_issue_34_planning_ecc.py`

**Interfaces:**
- Consumes resolved Planning item and normalized contract subcontractor.
- Produces ECC rows/files using existing template, grouping, mapping and reconciliation contracts.

- [ ] **Step 1: Write failing ECC tests**

Assert:

```text
PBOM is exactly selected Planning PBOM
quantity = 1
unit = Hop
contract lookup uses GCI/GTSB after _AA normalization
region/purchasing area uses existing controlled mapping
one Planning PBOM per site
no TSS/TI line is emitted as a side effect
```

- [ ] **Step 2: Run tests and verify failure**

```bash
python -m unittest tests.test_issue_34_planning_ecc -v
```

- [ ] **Step 3: Implement shared renderer integration**

Do not duplicate ECC workbook writing. Extend the existing row model/render path with Planning scope data.

- [ ] **Step 4: Add `_AA` optional-item safety assertion**

A generated `_AA` site must contain exactly `350001042321` and zero `350001143904`/`350001143905` rows.

- [ ] **Step 5: Run targeted renderer/reconciliation tests**

```bash
python -m unittest tests.test_issue_34_planning_ecc tests.test_create_pr_safety_integration tests.test_issue_74_reconciliation -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts tests/test_issue_34_planning_ecc.py
git commit -m "feat(issue-34): render Planning ECC through shared pipeline"
```

---

### Task 6: Enable CLI Planning scope only after end-to-end safety passes

**Files:**
- Modify: `scripts/create_pr.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `knowledge_base/pr_creator/rules/pr_creator_rule_register.yaml`
- Test: `tests/test_issue_34_planning_entrypoint.py`

**Interfaces:**
- Produces user-facing `--scope Planning` entrypoint with existing site-selection, lifecycle, UAT and production safety gates.

- [ ] **Step 1: Write failing CLI tests**

Assert `Planning` is accepted while unknown scopes remain rejected, and profile lifecycle gating works exactly as for TSS/TI.

- [ ] **Step 2: Verify failure before enabling**

```bash
python -m unittest tests.test_issue_34_planning_entrypoint -v
```

- [ ] **Step 3: Enable `Planning` in scope validation**

Keep `Operation Backoffice` unsupported.

- [ ] **Step 4: Update documentation/runtime status**

Only now change Planning from `DOCUMENTED_ONLY` to the appropriate implemented runtime status. Do not change Operation Backoffice status.

- [ ] **Step 5: Run all Issue #34 tests and broad regression**

```bash
python -m unittest \
  tests.test_issue_34_planning_profile_fields \
  tests.test_issue_34_planning_selector \
  tests.test_issue_34_planning_eligibility \
  tests.test_issue_34_planning_ecc \
  tests.test_issue_34_planning_entrypoint -v

python -m unittest discover -s tests -p "test_*.py"
```

Expected: all Issue #34 tests PASS; no existing TSS/TI regression introduced.

- [ ] **Step 6: Commit**

```bash
git add scripts/create_pr.py README.md SKILL.md knowledge_base/pr_creator tests/test_issue_34_planning_entrypoint.py
git commit -m "feat(issue-34): enable Planning PR scope"
```

---

### Task 7: Run controlled local UAT against the eight reference exports

**Files:**
- Local-only input: `Info/reference/planning-pr/*.xlsx`
- Generated: `output/NON_PRODUCTION_UAT/...`
- Do not commit raw iEPMS exports or generated UAT ECC files.

**Interfaces:**
- Consumes the business-provided Planning reference package.
- Produces auditable UAT summaries only.

- [ ] **Step 1: Run representative standard and `_AA` sites from every DU**

Verify the expected PBOM matrix and contract identities.

- [ ] **Step 2: Run negative cases**

Verify blank subcon, existing Planning PR value, and unknown Planning subcon behaviors.

- [ ] **Step 3: Check terminal reconciliation**

Every requested site must have exactly one terminal outcome.

- [ ] **Step 4: Do not commit UAT source/output files**

Only commit textual test evidence if needed and scrub site-sensitive/raw export data.

---

### Task 8: Final verification, PR and Issue #34 completion

**Files:**
- Review all changed files from the branch.

**Interfaces:**
- Produces merge-ready Issue #34 implementation.

- [ ] **Step 1: Verify branch diff is scoped to Planning**

Confirm no unrelated TSS/TI behavior or PR Model baseline changes.

- [ ] **Step 2: Run full verification again on the final head**

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m compileall scripts tests
```

- [ ] **Step 3: Inspect GitHub Actions/checks for the exact final head**

All required checks must be green or explicitly understood as unrelated infrastructure noise before merge.

- [ ] **Step 4: Open/update PR referencing `Fixes #34`**

PR summary must list the eight supported DU Models and the three-PBOM decision matrix.

- [ ] **Step 5: Merge only after final-head verification**

Use squash merge with expected head SHA.

- [ ] **Step 6: Confirm Issue #34 is closed completed**

Verify merged `main` contains the final implementation and documentation.
