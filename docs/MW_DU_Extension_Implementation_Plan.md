# MW DU Export Extension — Implementation Plan

**Repository:** `Gumb-D/create-pr-cd`  
**Current foundation PR:** Draft PR [#16](https://github.com/Gumb-D/create-pr-cd/pull/16)  
**Status:** Foundation implemented; validation and rollout remain pending.  
**Primary objective:** Extend PR creation from the current TX Mini DU input model to multiple MW-related DU models without weakening existing PR and ECC output controls.

---

## 1. Objective and Target Architecture

### 1.1 Objective

Support multiple MW DU export structures while preserving one controlled PR-generation path. Each DU model may differ in column headers, source content, or field availability; those differences must be resolved before the existing PR/ECC logic is invoked.

### 1.2 Target Flow

```text
iEPMS Export
  → DU Export Profile
  → Canonical PR Site Record
  → Shared PR Rules and Existing ECC Generator
  → ECC PR Output
```

### 1.3 Design Principles

- Use the four-layer source-header fingerprint, not a spreadsheet column index.
- Require a stable Header Hash for every approved export structure.
- Keep source-model adapters separate from shared PR business logic.
- Preserve field-level provenance, transformations, and mapping status.
- Fail closed: unknown, changed, incomplete, ambiguous, or unverified inputs cannot generate ECC output.
- Introduce new DU models only after profile approval, regression testing, and UAT.
- Do not commit iEPMS authentication, browser-session, customer-source, or production data.

---

## 2. Four-Layer Source Header Fingerprint

Every source column is identified by the complete ordered fingerprint below:

| Layer | Purpose |
|---|---|
| Field code / ID | iEPMS technical identifier |
| WBS stage | Relevant WBS or milestone context |
| Task name | Task-level business meaning |
| Display header | Exported user-facing column label |

A field mapping must not depend only on column position, a partial label, or an inferred synonym.

---

## 3. Delivery Scope and Non-Goals

### 3.1 In Scope

- Profile and classify iEPMS export structures.
- Define controlled DU Profiles per materially different export structure.
- Convert approved source data into a Canonical PR Site Record.
- Validate canonical records before PR and ECC generation.
- Establish test fixtures, regression controls, profile approval, and audit traceability.
- Extend iteratively from TX Mini parity to MW EOS Swap and other MW DU models.

### 3.2 Out of Scope for the Foundation

- Direct raw iEPMS export to ECC output generation.
- Enabling MW EOS Swap or any new DU model in production.
- Replacing or rewriting existing PR business rules.
- Changing `scripts/generate_tss_pr_ecc.py` before parity is proven.
- Planning, Backoffice, or unrelated workflow automation.
- Committing iEPMS credentials, cookies, tokens, browser sessions, or source data.

---

## 4. Current Baseline — Draft PR #16

### 4.1 Completed Foundation Items

- [x] Define target architecture: **DU Export → DU Profile → Canonical PR Site Record → shared PR logic → ECC output**.
- [x] Define fail-closed handling for unknown models, changed headers, missing critical fields, ambiguous mappings, and unverified mappings.
- [x] Add support for four-layer source-header fingerprints.
- [x] Add deterministic Header Hash generation.
- [x] Add DU export profiler for `.xlsx`, `.xlsm`, and `.csv` files.
- [x] Generate profiler outputs:
  - [x] Header inventory in JSON.
  - [x] Header inventory in Markdown.
  - [x] Header Hash.
  - [x] Canonical-field candidate report.
  - [x] Missing PR-critical-fields report.
  - [x] Draft DU Profile template.
- [x] Add DU Profile loader and lifecycle validation.
- [x] Add canonical PR site-record validator.
- [x] Add four-layer fingerprint adapter.
- [x] Preserve field-level provenance, source evidence, transformation, and mapping status.
- [x] Add input guard to block raw source exports from direct ECC generation.
- [x] Block output for DRAFT profiles, changed headers, unknown model/view, ambiguous mappings, and unverified mappings.
- [x] Add local iEPMS authentication-file protection to `.gitignore`.
- [x] Add synthetic foundation tests.
- [x] Run synthetic foundation test suite: **11 tests passed**.
- [x] Run Python compilation check for new foundation modules.

### 4.2 Current Constraints

- [x] Draft PR #16 has not changed the existing ECC generation runtime path.
- [x] No new MW DU model is active.
- [x] TX Mini profile remains `DRAFT`.
- [x] No production Header Hash has been approved.
- [x] No customer source export or credential has been committed.
- [ ] Full existing repository regression suite must still run in the actual local repository checkout.
- [ ] PR #16 requires code review before it can be made ready for merge.

---

## 5. Implementation Phases

## Phase 0 — Foundation Review and Merge Readiness

**Purpose:** Validate the architecture foundation before any live DU-profile work begins.

### Activities

- [ ] Check out Draft PR #16 in `C:\dev\create-pr-cd`.
- [ ] Run the complete existing repository test suite, not only the foundation tests.
- [ ] Verify there is no behaviour change in `scripts/generate_tss_pr_ecc.py`.
- [ ] Review fail-closed decisions and error messages.
- [ ] Confirm `.gitignore` covers local authentication/session files.
- [ ] Perform secret and customer-data scan of the PR diff.
- [ ] Review module boundaries: profiler, profile loader, adapter, validator, and gate.
- [ ] Decide whether to squash the foundation branch’s granular commits before ready-for-review status.

### Acceptance Criteria

- [ ] Full repository tests pass.
- [ ] No production PR/ECC output behaviour changes are introduced.
- [ ] Raw source exports cannot bypass the guard.
- [ ] No customer data, credentials, tokens, cookies, or browser-session data exist in Git history or the PR diff.
- [ ] PR #16 is approved for merge as an architecture-only foundation.

---

## Phase 1 — TX Mini Golden-Parity Validation

**Purpose:** Prove that the new intake architecture can reproduce the current TX Mini result before enabling any new DU model.

### Activities

- [ ] Obtain an approved, sanitized TX Mini iEPMS export fixture.
- [ ] Run the profiler against the approved fixture.
- [ ] Capture the four-layer fingerprint inventory and Header Hash.
- [ ] Review every required canonical PR field against the source export.
- [ ] Approve the TX Mini source mappings and controlled transformations.
- [ ] Identify and document fields that are not present in source data.
- [ ] Update `tx_mini_pr_v1` from `DRAFT` to a controlled validation profile only after review.
- [ ] Build Canonical PR Site Records from the TX Mini export.
- [ ] Compare canonical records against the present normalized input contract, `site_pr_po_view.xlsx`.
- [ ] Run the existing PR/ECC generator with legacy and canonical-path inputs.
- [ ] Compare ECC output content, line count, quantities, and key formatting.

### Acceptance Criteria

- [ ] All required TX Mini canonical fields are mapped with approved status.
- [ ] TX Mini Header Hash is registered as approved for the profile version.
- [ ] No unverified transform or source mapping remains in the production candidate path.
- [ ] Legacy and canonical-path ECC outputs are identical, except for explicitly approved non-functional metadata.
- [ ] Negative tests block changed headers, missing required fields, and ambiguous source mappings.
- [ ] TX Mini is approved as the first controlled canonical-input model.

---

## Phase 2 — First New DU Model: MW EOS Swap

**Purpose:** Use one new MW DU model to prove that the profile-based extension works beyond TX Mini.

### Activities

- [ ] Select and obtain representative sanitized MW EOS Swap exports.
- [ ] Profile each export and identify whether one stable export structure exists.
- [ ] Compare the four-layer headers with TX Mini.
- [ ] Create an MW EOS Swap DU Profile.
- [ ] Map source fields to the Canonical PR Site Record.
- [ ] Define controlled transformations where source semantics differ from TX Mini.
- [ ] Identify unsupported or missing business inputs.
- [ ] Decide each missing-field treatment: derived, supplied by approved reference data, manually resolved, or blocking.
- [ ] Add positive, missing-field, changed-header, and ambiguity fixtures.
- [ ] Execute PR/ECC output validation with approved business owners.
- [ ] Record output differences as explicit model-specific rules rather than hidden exceptions.

### Acceptance Criteria

- [ ] MW EOS Swap profile contains approved source fingerprints and Header Hashes.
- [ ] Each required field has traceable provenance.
- [ ] Unsupported or unresolved fields quarantine the record rather than producing partial ECC output.
- [ ] UAT confirms valid PR/ECC output for representative MW EOS Swap scenarios.
- [ ] MW EOS Swap is released only after profile approval and regression coverage are complete.

---

## Phase 3 — Scale to Remaining MW DU Models

**Purpose:** Extend through repeatable profile onboarding rather than custom code forks.

### Activities

- [ ] Build a complete MW DU model inventory.
- [ ] Prioritise models by delivery volume, urgency, and similarity to already-approved profiles.
- [ ] Group models that share an identical source structure and can reuse one profile.
- [ ] Create separate profiles for materially different source structures.
- [ ] Maintain a registry of model/view identifiers, profile IDs, versions, approved Header Hashes, and lifecycle status.
- [ ] Add representative synthetic and sanitized regression fixtures for every approved profile.
- [ ] Add model-specific validation rules only where necessary.
- [ ] Document each source-to-canonical mapping decision.
- [ ] Add a controlled deprecation path for superseded Header Hashes and profile versions.

### Acceptance Criteria

- [ ] Every enabled DU model resolves to one approved profile and profile version.
- [ ] Unknown model/view combinations are quarantined.
- [ ] Header changes require re-profiling and re-approval.
- [ ] Each production profile has passing positive and negative regression tests.
- [ ] Shared generator logic remains common unless a formally approved business difference requires a model-specific rule.

---

## Phase 4 — Integration, Operations, and Release Governance

**Purpose:** Make profile onboarding repeatable, auditable, and safe for operational use.

### Activities

- [ ] Integrate approved Canonical PR Site Records into the existing PR generation path.
- [ ] Retain the existing generator as the final output engine until replacement is explicitly approved.
- [ ] Define a quarantine report format for blocked records.
- [ ] Define manual correction and resubmission workflow for incomplete records.
- [ ] Add operator documentation for profiling, mapping review, profile approval, release, and rollback.
- [ ] Add audit fields: source export identity, DU Profile ID/version, Header Hash, mapping version, field provenance, validation result, and output decision.
- [ ] Define profile-change authority and approval responsibilities.
- [ ] Define release sequence: test → UAT → controlled production → monitoring → broader rollout.
- [ ] Conduct end-to-end UAT using real approved project scenarios.

### Acceptance Criteria

- [ ] Every output is traceable to a profile version and Header Hash.
- [ ] Quarantined records contain actionable reasons and no ECC output is produced.
- [ ] Profile changes follow an approved review process.
- [ ] Rollback to a previous approved profile version is documented and tested.
- [ ] End-to-end UAT is signed off before each new model enters production.

---

## 6. Required Controls

| Control | Required Behaviour |
|---|---|
| Unknown DU model or view | Quarantine; no PR/ECC output |
| Changed Header Hash | Quarantine; re-profile and re-approve |
| Missing required canonical field | Incomplete/quarantine; no output |
| Ambiguous source fingerprint | Quarantine; no automatic selection |
| Unverified source mapping | Block production output |
| Unverified transformation | Block production output |
| DRAFT DU Profile | Permit discovery/testing only; block production output |
| Raw iEPMS export | Cannot directly reach ECC generator |
| Credentials/session data | Local only; ignored by Git |

---

## 7. Suggested DU Profile Lifecycle

```text
DRAFT
  → VALIDATION
  → UAT_APPROVED
  → PRODUCTION
  → DEPRECATED
```

### Lifecycle Rules

- **DRAFT:** Profiling and mapping preparation only; no production output.
- **VALIDATION:** Mapping and Header Hash are under controlled testing; output is non-production.
- **UAT_APPROVED:** Business validation completed; pending controlled release.
- **PRODUCTION:** Approved model/profile/Header Hash combination may generate output.
- **DEPRECATED:** Retained for historical traceability but blocked for new processing.

---

## 8. Minimum Test Matrix per DU Profile

| Test Case | Expected Result |
|---|---|
| Approved source structure and complete data | Canonical record accepted; eligible for downstream processing |
| Unknown DU model/view | Quarantined |
| Changed Header Hash | Quarantined |
| Missing PR-critical source field | Incomplete or quarantined |
| Duplicate/ambiguous source fingerprint | Quarantined |
| Unverified mapping | Output blocked |
| Unverified transformation | Output blocked |
| Invalid required canonical value | Incomplete or quarantined |
| Legacy TX Mini parity scenario | Same approved ECC output |

---

## 9. Immediate Next Actions

1. Complete Phase 0 review and full regression testing for Draft PR #16.
2. Prepare an approved, sanitized TX Mini source export fixture.
3. Start Phase 1 and establish TX Mini golden-output parity.
4. After TX Mini parity is accepted, onboard MW EOS Swap as the first new DU Profile.
5. Use the proven onboarding process for the remaining MW DU model inventory.

---

## 10. Definition of Done

The extension is complete only when:

- [ ] TX Mini runs through the canonical-input path with proven golden parity.
- [ ] At least one new MW DU model, proposed as MW EOS Swap, is enabled through an approved profile.
- [ ] Every enabled MW DU model is routed through a controlled DU Profile.
- [ ] All enabled profiles have approved Header Hashes, mapping traceability, and regression tests.
- [ ] Unknown, changed, incomplete, ambiguous, and unverified inputs fail closed.
- [ ] Existing PR/ECC business logic remains controlled and regression-protected.
- [ ] The operational team has documented procedures for profile onboarding, approval, change management, quarantine handling, and rollback.
