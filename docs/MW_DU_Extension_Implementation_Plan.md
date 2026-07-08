# MW DU Export Extension — Implementation Plan

**Repository:** `Gumb-D/create-pr-cd`  
**Current foundation PR:** Draft PR [#16](https://github.com/Gumb-D/create-pr-cd/pull/16)  
**Status:** Foundation implemented; discovery registry, DU inventory, 10 discovery-only DRAFT profiles, and manual-review scaffolding are now in place from the 10 local DU exports; rollout remains approval-gated.  
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
- [x] Run foundation-specific regression tests: **11 foundation tests passed inside the full suite on 2026-07-06**.
- [x] Run the complete repository test suite: **165 tests passed on 2026-07-07** via `python -m unittest discover -s tests -p "test_*.py" -v`.
- [x] Run Python compilation check for scripts via `python -m compileall -q scripts`.
- [x] Restore the authoritative architecture and implementation-plan documents onto the foundation branch so the live checklist travels with the work.

### 4.2 Current Constraints

- [x] Draft PR #16 has not changed the existing ECC generation runtime path.
- [x] `scripts/generate_tss_pr_ecc.py` has no branch diff relative to the working tree review performed on 2026-07-06.
- [x] No new MW DU model is active.
- [x] TX Mini profile remains `DRAFT`.
- [x] No production Header Hash has been approved.
- [x] No customer source export or credential has been committed in the foundation branch diff.
- [x] Full existing repository regression suite has run in the actual local repository checkout.
- [ ] PR #16 still requires human code review before it can be made ready for merge.

Blocker:
Human review and merge authorization are still required; Phase 0 can verify readiness but cannot self-approve the PR.

---

## 5. Implementation Phases

## Phase 0 — Foundation Review and Merge Readiness

**Purpose:** Validate the architecture foundation before any live DU-profile work begins.

### Activities

- [x] Check out Draft PR #16 in `C:\dev\create-pr-cd`.
- [x] Run the complete existing repository test suite, not only the foundation tests.
- [x] Verify there is no behaviour change in `scripts/generate_tss_pr_ecc.py`.
- [x] Review fail-closed decisions and error messages.
- [x] Confirm `.gitignore` covers local authentication/session files.
- [x] Perform secret and customer-data scan of the PR diff.
- [x] Review module boundaries: profiler, profile loader, adapter, validator, and gate.
- [ ] Decide whether to squash the foundation branch’s granular commits before ready-for-review status.

Blocker:
Do not rewrite branch history without explicit instruction. Commit-squash choice remains a maintainer decision.

### Acceptance Criteria

- [x] Full repository tests pass.
- [x] No production PR/ECC output behaviour changes are introduced.
- [x] Raw source exports cannot bypass the guard.
- [x] No customer data, credentials, tokens, cookies, or browser-session data exist in the current PR diff.
- [ ] PR #16 is approved for merge as an architecture-only foundation.

Blocker:
Approval for merge is a human review outcome and is not yet evidenced in the repository state.

### Phase 0 Evidence

- Full suite command: `python -m unittest discover -s tests -p "test_*.py" -v`
- Full suite result: `Ran 165 tests in 7.165s` and `OK`
- Compile command: `python -m compileall -q scripts`
- ECC generator change check: `git diff -- scripts/generate_tss_pr_ecc.py` returned no diff on the foundation branch
- Current foundation branch delta from `origin/main`: `.gitignore`, `config/`, `Info/DU_EXPORT_ADAPTER_FOUNDATION.md`, the new adapter scripts, the new tests, and the restored `docs/` files; no customer export fixture or credential file is present
- Secret/data scan evidence:
  - `.gitignore` ignores `scripts/api_auth.json`
  - `config/README.md`, `config/registries/README.md`, and `tests/fixtures/README.md` explicitly forbid committed credentials, cookies, tokens, employee IDs, session material, and customer exports
  - The foundation tests use synthetic fixtures only

### Phase 0 Readiness Assessment

- Technical readiness: **Ready for human review as an architecture-only foundation**
- Remaining non-code risks:
  - Human reviewers still need to confirm whether the current granular commit stack should remain as-is or be reorganized later
  - No sanitized original TX Mini iEPMS export is yet available, so Phase 1 golden-parity work remains blocked by external artifact availability
  - Later-phase discovery and governance scaffolding have expanded the repository footprint, so human reviewers should keep the foundation-only boundary in mind when deciding whether to review this work as one stream or as smaller stacked follow-up diffs

---

## Phase 1 — TX Mini Golden-Parity Validation

**Purpose:** Prove that the new intake architecture can reproduce the current TX Mini result before enabling any new DU model.

### Activities

- [ ] Obtain an approved, sanitized TX Mini iEPMS export fixture.
  Local discovery note:
  On 2026-07-06, a local external folder containing 10 DU exports was profiled in read-only mode under `output/du-20260706-profile/`, including a TX Mini export and an MW EOS Swap export. These source files remain external and uncommitted; business approval/sanitization status still needs confirmation before they can serve as formal repository evidence.
- [x] Run the profiler against the approved fixture.
  Evidence note:
  A discovery-only profiler pass has already been executed locally against the available TX Mini export and the other nine DU exports. Result artifacts include `header_inventory.json`, `header_inventory.md`, `header_hash.txt`, `canonical_field_candidates.json`, `missing_pr_critical_fields.md`, and `draft_du_profile.yaml` per file under `output/du-20260706-profile/`.
- [x] Perform keyword-discovery mapping review across the available DU exports.
  Evidence note:
  A consolidated local review has been written to `output/du-20260706-profile/KEYWORD_DISCOVERY_MAPPING_REVIEW.md`. The review is now limited to the skill-relevant fields defined by `SKILL.md` and keeps every DU in discovery-only status because PR-status and some SOW/subcontractor fields remain ambiguous.
- [x] Build manual-review-ready skill-field shortlists for the highest-priority DU exports.
  Evidence note:
  Discovery-only shortlist artifacts now exist at `config/registries/mw_du_priority_skill_field_shortlists.yaml` and `docs/MW_DU_Priority_Skill_Field_Shortlists.md` for TX Mini Project, MW EOS Swap, 2023 TX Rollout, and ZTE TX MINI. These shortlists rank the direct field candidates above supporting detail or PR-oriented variants without claiming approval.
- [x] Seed the `tx_mini_pr_v1` DRAFT profile with discovery-only source candidates and the observed header hash.
  Evidence note:
  `config/du_profiles/tx_mini_pr_v1.yaml` now carries the observed TX Mini header hash `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221` plus UNVERIFIED source candidates for the strongest skill-scoped fields. The profile remains explicitly non-production and still blocks ECC output.
- [x] Generate a local-only TX Mini mapping-decision review package for human approval.
  Evidence note:
  `scripts/build_mapping_decision_workbook.py` now builds a reviewer-ready decision package from the profiler artifacts, the priority shortlist registry, and the DRAFT profile, using the local external TX Mini export in read-only mode (the source-file SHA-256 is verified against the profiled export before the package is built). The generated local-only artifacts are `output/du-20260706-profile/tx-mini-mapping-review/TX_MINI_MAPPING_DECISION_WORKBOOK.xlsx` and `TX_MINI_MAPPING_DECISION_SUMMARY.md` (2026-07-07, gitignored under `output/`). The workbook covers the 15 review-scoped canonical fields with exact four-layer fingerprint candidates, per-field candidate ranks from the shortlist registry, non-authoritative source-column positions, at least five masked sample values per plausible candidate, proposed transformations, and blank reviewer decision columns limited to `APPROVE`/`REJECT`/`NEEDS_BUSINESS_DECISION`/`NO_SOURCE_FIELD`. Person names, employee IDs, PR references, site codes/names, coordinates, and subcontractor identities are masked; no approval is inferred; `tx_mini_pr_v1` stays `DRAFT`; no source-export data was committed. `tests/test_mapping_decision_workbook.py` covers requirement classification, fingerprint-based column resolution, masking and site-token scrubbing, candidate ranking, flagging, empty decision columns, and the fail-closed source-hash mismatch path. Full repository suite after this addition: `Ran 184 tests` with `OK` on 2026-07-07, plus `python -m compileall -q scripts` passing.
- [x] Capture the four-layer fingerprint inventory and Header Hash.
  Evidence note:
  The TX Mini fingerprint inventory has existed under `output/du-20260706-profile/` since 2026-07-06; on 2026-07-07 JJ confirmed the TX Mini export (`A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx`, by filename) as approved development evidence, and the observed header hash `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221` is now recorded in `approved_header_hashes` of `tx_mini_pr_v1`. Approval of the other nine exports is explicitly deferred ("others will need to implement later").
- [x] Review every required canonical PR field against the source export.
  Evidence note:
  JJ completed the field-by-field mapping review on 2026-07-07 across two ruling rounds; the local TX Mini decision workbook's `Decision_Log` now carries a recorded ruling for all 16 rows. Round 2 recorded: `site_code`, `site_name`, `du_key`, `tx_upgrade_scope_raw`, `antenna_size_ne`, and `antenna_size_fe` APPROVE rank 1; `tx_sow_raw` APPROVE rank 1 selecting `docata|ZDCSZ00815532 | Installation | Microwave | Tx SOW` as the authoritative PR trigger, with `TX SOW Details` explicitly rejected as trigger and retained as evidence-only for `tx_sow_details`; `existing_tss_pr_status` / `existing_ti_pr_status` additionally received the reference-presence normalization ruling (non-blank PR reference => `PR_EXISTS`, explicit `No PR required...` => `NO_PR_REQUIRED`, blank => `NO_PR`); and `tx_sow_normalized` is recorded `NEEDS_BUSINESS_DECISION` pending the normalization value map. These rulings live in the local decision package and this plan; they are not yet written to `tx_mini_pr_v1.yaml`.
  Decision update (2026-07-07):
  JJ ruled on eight fields by source-column position; each ruling was resolved to its exact four-layer fingerprint on the `data` sheet before recording, so the fingerprint — not the position — is the recorded decision: `latitude` → `site|fix00013 | Site Basic Info | Site Basic Info | Latitude (North Plus South Minus)` (col F); `longitude` → `site|fix00010 | ... | Longitude (East Plus West Minus)` (col G); `region` confirmed → `site|region_name | ... | region` (col D); `state` → `site|fix00008 | ... | Province/State` (col E); `subcontractor_ti` → `docata|ZDCSZ0657771 | Installation | Wireless RAN | SubCon - TI Team` (col AE); `existing_tss_pr_status` → `docata|ZDCSZ641766 | Installation | Wireless RAN | Subcon PR - TSS` (col AD); `existing_ti_pr_status` → `docata|ZDCSZ641765 | Installation | Wireless RAN | Subcon PR - TI` (col AF); plus a new `subcontractor_tss` ruling → `docata|ZDCSZ0657770 | Installation | Wireless RAN | SubCon - TSS Team` (col AC), which is recorded as `NEEDS_BUSINESS_DECISION` because the Canonical PR Site Record v1 has no `subcontractor_tss` field and a schema/validator extension is a separate controlled change. The `existing_*_pr_status` selections carry an open transformation question: the source values are PR references, not status enums, so a controlled normalization transform still needs definition and approval. These decisions live in the local decision package only and have not been written to `tx_mini_pr_v1.yaml`; the profile stays `DRAFT`.
- [x] Approve the TX Mini source mappings and controlled transformations.
  Evidence note:
  All four approval gates closed on 2026-07-07 and the write-back is complete: `config/du_profiles/tx_mini_pr_v1.yaml` is now `profile_version` `0.2.0` / `mapping_version` `approved-2026-07-07-tx-mini-v1` with every Decision_Log-approved fingerprint recorded as an `APPROVED` source candidate (including the new `state`, `latitude`, `longitude`, `tx_upgrade_scope_raw`, `subcontractor_tss`, and the `existing_*_pr_status` mappings with the `normalize_pr_reference_status` transform), the approved header hash, and the `canonical_sow_registry.yaml` normalization reference. `subcontractor_planning` and `tx_sow_details` remain intentionally `UNVERIFIED` optional evidence fields. The discovery packet was regenerated through `scripts/refresh_mw_du_discovery_packet.py` with all consistency guards passing, and the profiler/grouping builders now skip non-profiler folders under the output root. Full suite: `Ran 203 tests` `OK` on 2026-07-07.
  Gate history:
  Source-column rulings completed first, then the four gates closed in sequence: (1) closed on 2026-07-07 (round 4) — JJ approved identity normalization for the 11 PR-model-matching raw Tx SOW values, completing the value map; it is now controlled configuration in `config/registries/canonical_sow_registry.yaml` (11 `PR_TRIGGER` identity entries, `Cancel / Drop` => `NO_PR_TRIGGER`, `MW Remote Upgrade` / `New Starlink` / `Under NIC` / `Existing TX` => `REVIEW_REQUIRED`, unknown values => `REVIEW_REQUIRED`), implemented fail-closed by `scripts/sow_normalization.py` with `tests/test_sow_normalization.py`; (2) implemented on 2026-07-07 — the Canonical PR Site Record now carries an optional `subcontractor_tss` field (`scripts/canonical_site_validator.py` FIELD_PATHS + record shape) with adapter provenance, without changing any scope-required rule; (3) implemented on 2026-07-07 — `scripts/du_export_adapter.py` now provides the controlled `normalize_pr_reference_status` transform (non-blank reference => `PR_EXISTS`, `No PR required...` => `NO_PR_REQUIRED`, blank => `NO_PR`), covered by `tests/test_du_export_adapter.py`; and (4) closed on 2026-07-07 — JJ confirmed the TX Mini export as approved development evidence by filename, with the other nine exports deferred to later implementation.
  Cross-profile guidance (JJ, 2026-07-07):
  The remaining profiled DU exports carry similar column semantics to TX Mini with different column positions. The TX Mini approved semantic pattern is therefore the donor review template for the other DRAFT profiles; because all mappings are fingerprint-based rather than positional, each profile still requires its own four-layer fingerprint confirmation before any mapping approval.
- [x] Identify and document fields that are not present in source data.
  Evidence note:
  The completed field review found every required TX Mini canonical field present in the source export — including the PR-status duplicate-prevention fields, which resolve from the `Subcon PR - TSS` / `Subcon PR - TI` reference columns via the approved transform. Only optional evidence fields (`boq_configuration`, `ne_sow_details`, `fe_sow_details`) remain unmapped, and `subcontractor_planning` stays `UNVERIFIED`; none of these block the TSS/TI scopes.
- [ ] Update `tx_mini_pr_v1` from `DRAFT` to a controlled validation profile only after review.
  Blocker:
  The unresolved-review builder now recognizes human approval (2026-07-08): an `APPROVED` profile selection resolves its shortlist competition and is recorded as `RESOLVED_BY_APPROVED_MAPPING` with the rejected alternates kept for traceability, while `UNVERIFIED` selections with alternates still flag `REVIEW_REQUIRED_COMPETING_CANDIDATES` and approved-but-shortlist-mismatched selections stay flagged as a typo safety net (`tests/test_unresolved_skill_field_review.py` covers both directions). After the packet refresh, TX Mini is now transition-eligible for `PROFILED`, and exactly one blocker keeps `BUSINESS_VALIDATED` / `PR_INPUT_READY` denied: the optional `subcontractor_planning` field was never ruled in the mapping review (competing candidates `Subcon - Planning` vs `Subcon PR - Planning`) and awaits JJ's decision. Lifecycle stays `DRAFT` and fail-closed meanwhile; any promotion is a separate explicit change after the transition review permits it.
- [ ] Build Canonical PR Site Records from the TX Mini export.
- [ ] Compare canonical records against the present normalized input contract, `site_pr_po_view.xlsx`.
- [ ] Run the existing PR/ECC generator with legacy and canonical-path inputs.
- [ ] Compare ECC output content, line count, quantities, and key formatting.

### Acceptance Criteria

- [x] All required TX Mini canonical fields are mapped with approved status.
- [x] TX Mini Header Hash is registered as approved for the profile version.
- [ ] No unverified transform or source mapping remains in the production candidate path.
- [ ] Legacy and canonical-path ECC outputs are identical, except for explicitly approved non-functional metadata.
- [ ] Negative tests block changed headers, missing required fields, and ambiguous source mappings.
- [ ] TX Mini is approved as the first controlled canonical-input model.

Blocker:
Formal approval/sanitization status for the external TX Mini export still needs confirmation. `Info/input/site_pr_po_view.xlsx` remains a normalized downstream file and is not sufficient evidence by itself for Phase 1 golden parity.

---

## Phase 2 — First New DU Model: MW EOS Swap

**Purpose:** Use one new MW DU model to prove that the profile-based extension works beyond TX Mini.

### Activities

- [ ] Select and obtain representative sanitized MW EOS Swap exports.
- [x] Profile each export and identify whether one stable export structure exists.
  Evidence note:
  A local discovery-only profile was generated for the available MW EOS Swap export on 2026-07-06 with header hash `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`. The current keyword pass still shows ambiguity for several PR-critical fields, so this artifact supports profiling progress but not production readiness.
- [ ] Compare the four-layer headers with TX Mini.
- [x] Build manual-review-ready skill-field shortlists for the first non-TX-Mini candidate.
  Evidence note:
  MW EOS Swap is included in `config/registries/mw_du_priority_skill_field_shortlists.yaml` and `docs/MW_DU_Priority_Skill_Field_Shortlists.md`, with direct shortlist candidates for `Site ID`, `Site Name`, `DU Code`, `Region`, `Tx SOW`, antenna fields, and scope-based subcon fields.
- [x] Create an MW EOS Swap DU Profile.
  Evidence note:
  `config/du_profiles/mw_eos_swap_pr_v1.yaml` now exists as a DRAFT-only profile with observed header hash `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a` and UNVERIFIED source candidates for the strongest skill-scoped fields discovered from the local profiler output.
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

Blocker:
Representative MW EOS Swap source evidence is now available locally for discovery, but approval/sanitization status and business validation artifacts are not yet recorded in the repository.

---

## Phase 3 — Scale to Remaining MW DU Models

**Purpose:** Extend through repeatable profile onboarding rather than custom code forks.

### Activities

- [x] Build a complete MW DU model inventory.
  Evidence note:
  A discovery-only inventory has been written to `docs/MW_DU_Discovery_Inventory.md` and covers the 10 locally profiled DU exports with DU model IDs, view IDs, and observed header hashes.
- [x] Prioritise models by delivery volume, urgency, and similarity to already-approved profiles.
  Evidence note:
  The current discovery sequence is now supported by `config/registries/mw_du_structure_grouping_review.yaml` and `docs/MW_DU_Structure_Grouping_Review.md`, which show TX Mini, the BAU models, USP, Jendela, and 2023 TX Rollout as one high-overlap family, while MW EOS Swap and ZTE TX MINI form a lower-overlap MW pair. This is still discovery-only prioritisation guidance, not an approval to reuse profiles.
- [x] Group models that share an identical source structure and can reuse one profile.
  Evidence note:
  No exact structure reuse has been proven yet because all 10 observed header hashes are unique, so no shared production profile can be claimed from hash identity alone. The new grouping review instead records similarity-based reuse hypotheses that still require four-layer field review before any profile reuse decision.
- [ ] Create separate profiles for materially different source structures.
- [x] Create separate discovery-only DRAFT profiles for materially different source structures where the strongest evidence already exists.
  Evidence note:
  The repository now contains 10 tracked DRAFT-only profiles: `tx_mini_pr_v1`, `mw_eos_swap_pr_v1`, `tx_rollout_2023_pr_v1`, `zte_tx_mini_pr_v1`, `jendela_tx_migration_pr_v1`, `celcomdigi_bau_2023_pr_v1`, `celcomdigi_bau_2024_pr_v1`, `celcomdigi_usp_pr_v1`, `cd_consolidation_2023_decom_pr_v1`, and `cd_consolidation_2023_rollout_pr_v1`. `docs/MW_DU_Discovery_Inventory.md` and `config/registries/mw_du_model_discovery_registry.yaml` now surface all 10 profile IDs from the live profile files, while still keeping every one of them in quarantined discovery status.
- [x] Maintain a registry of model/view identifiers, profile IDs, versions, approved Header Hashes, and lifecycle status.
  Evidence note:
  A discovery-only registry has been generated at `config/registries/mw_du_model_discovery_registry.yaml` from profiler outputs using `scripts/build_du_discovery_registry.py`. Entries remain quarantined and do not claim approved mappings or production header hashes.
- [ ] Add representative synthetic and sanitized regression fixtures for every approved profile.
- [ ] Add model-specific validation rules only where necessary.
- [x] Document each source-to-canonical mapping decision.
  Evidence note:
  Skill-scoped keyword-discovery mapping decisions for the 10 local DU exports are documented in `output/du-20260706-profile/KEYWORD_DISCOVERY_MAPPING_REVIEW.md`. These are discovery shortlists only and not approved four-layer mappings.
- [x] Generate an unresolved-field manual-review packet for the highest-priority DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_unresolved_skill_field_review.yaml` and `docs/MW_DU_Unresolved_Skill_Field_Review.md` now compare the tracked DRAFT profiles against the shortlist evidence, flagging missing required PR-status fields and fields that still have competing shortlist candidates. The shortlist join is now keyed by observed header hash so two exports that share the same DU model name, such as the `CD consolidation 2023` Decom and Rollout variants, cannot silently borrow each other's review packet source identity.
- [x] Generate a structure-grouping review for the 10 profiled DU exports.
  Evidence note:
  `config/registries/mw_du_structure_grouping_review.yaml` and `docs/MW_DU_Structure_Grouping_Review.md` now score exact four-layer fingerprint overlap across the 10 local exports. The results show that the TX-family exports form a high-overlap review cluster, while MW EOS Swap and ZTE TX MINI form a smaller MW review pair that is structurally distinct from the TX-family exports.
- [x] Generate a 10-export coverage review that separates tracked profiles, donor-review candidates, and backlog discovery-only exports.
  Evidence note:
  `config/registries/mw_du_export_coverage_review.yaml` and `docs/MW_DU_Export_Coverage_Review.md` now summarize the current evidence position across all 10 profiled exports. The live review now shows `10` tracked DRAFT profile exports, `0` donor-review candidates, and `0` backlog discovery-only exports. `CD consolidation 2023` has now been fully brought into the tracked discovery packet via `cd_consolidation_2023_decom_pr_v1` and `cd_consolidation_2023_rollout_pr_v1`, while still remaining fail-closed because both exports keep competing shortlist candidates for core fields and still lack approved PR-status mappings. The coverage statuses are intentionally discovery-only planning guidance and do not approve any reusable mapping source.
- [x] Generate an MW-pair divergence review for the two MW-family DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_mw_pair_divergence_review.yaml` and `docs/MW_DU_MW_Pair_Divergence_Review.md` now compare `mw_eos_swap_pr_v1` and `zte_tx_mini_pr_v1` field by field. The review shows that some canonical fields already select the same exact fingerprints, while others such as `tx_sow_raw`, `site_code`, `subcontractor_ti`, and the antenna fields still diverge despite similar display labels. The pair review now also records left/right `profile_version`, `mapping_version`, and `observed_header_hash` values for direct artifact traceability.
- [x] Generate a missing-field bridge review for the required PR-status gaps in the priority DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_missing_field_bridge_review.yaml` and `docs/MW_DU_Missing_Field_Bridge_Review.md` now cover all 10 tracked DRAFT profiles. They continue to identify `2023 TX Rollout` as the best currently profiled donor reference for `existing_tss_pr_status` and `existing_ti_pr_status` on the other blocked profiles, including the two `CD consolidation 2023` variants. The tracked `tx_rollout_2023_pr_v1` bridge entry intentionally remains empty because it no longer needs cross-model donor fields for those duplicate-prevention statuses. The bridge entries now carry `profile_version`, `mapping_version`, and `observed_header_hash` for the blocked target profile so the donor-review packet itself stays traceable.
- [x] Generate a profile-readiness review for the current priority DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_profile_readiness_review.yaml` and `docs/MW_DU_Profile_Readiness_Review.md` now summarize why all 10 tracked DRAFT profiles remain discovery-only blocked. The packet makes the blocking set explicit per profile: DRAFT lifecycle status, zero approved header hashes, missing required PR-status fields where still applicable, unapproved required mappings, competing shortlist candidates, and bridge-only donor suggestions where required.
- [x] Generate a prioritized manual action queue for the current priority DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_profile_action_queue.yaml` and `docs/MW_DU_Profile_Action_Queue.md` now convert the current discovery blockers into a review sequence per profile: missing required fields first where they still exist, then competing candidates, then single-candidate verification, then header-hash approval, followed by an explicit hold on lifecycle promotion.
- [x] Generate a cross-profile review matrix for the current priority DRAFT profiles.
  Evidence note:
  `config/registries/mw_du_profile_review_matrix.yaml` and `docs/MW_DU_Profile_Review_Matrix.md` now batch repeated blocker themes across all 10 tracked DRAFT profiles, including the two `CD consolidation 2023` variants. The matrix shows that the first shared review wave is still the two missing PR-status fields for the nine profiles that lack them, followed by larger cross-profile batches such as `region`, `site_code`, and `tx_sow_raw`. The profile summaries now also carry `profile_version`, `mapping_version`, and `observed_header_hash` so the batched review output stays traceable to the live profile identity.
- [x] Add a controlled deprecation path for superseded Header Hashes and profile versions.
  Evidence note:
  `scripts/build_profile_deprecation_review.py` now generates `config/registries/mw_du_profile_deprecation_review.yaml` and `docs/MW_DU_Profile_Deprecation_Review.md` as the repository's deprecation evidence packet. The review stays fail-closed: no profile can claim `DEPRECATED` without recorded successor and rollback references plus superseded header hashes, and `scripts/check_profile_status_consistency.py` now rejects an unreviewed `DEPRECATED` status.
- [x] Add a profile traceability audit for the current priority DRAFT profiles.
  Evidence note:
  `scripts/build_profile_traceability_audit.py` now generates `config/registries/mw_du_profile_traceability_audit.yaml` and `docs/MW_DU_Profile_Traceability_Audit.md`. The audit checks whether the generated profile-centric artifacts carry the live `profile_version`, `mapping_version`, and `observed_header_hash` for each tracked profile. The current audit marks all 10 tracked DRAFT profiles, including `cd_consolidation_2023_decom_pr_v1` and `cd_consolidation_2023_rollout_pr_v1`, as `TRACEABLE` across discovery, unresolved, bridge, readiness, action queue, review matrix, tracked-profile coverage, transition, deprecation, and rollback-readiness artifacts.

### Phase 3 Supporting Verification

- [x] Add automated verification for the discovery-registry builder.
  Evidence note:
  `tests/test_du_discovery_registry.py` now covers filename parsing, DU identity extraction, project-key inference, TX Mini entry generation, and inventory rendering.
- [x] Add automated verification for the priority shortlist builder, DRAFT profile loading, and unresolved review packet.
  Evidence note:
  `tests/test_skill_field_shortlists.py`, `tests/test_du_profile_loader.py`, and `tests/test_unresolved_skill_field_review.py` now cover shortlist ranking choices, observed header-hash preservation in DRAFT profiles, MW EOS profile loading, and unresolved-field review generation. They now also verify that the two `CD consolidation 2023` exports keep distinct header-hash identities all the way through shortlist and unresolved-review generation. The current full repository suite passes with `165` tests on 2026-07-07.
- [x] Add automated verification for the structure-grouping review builder.
  Evidence note:
  `tests/test_du_structure_grouping.py` now covers Jaccard fingerprint similarity, closest-neighbor ranking, and markdown rendering for similarity-based reuse guidance.
- [x] Add automated verification for the 10-export coverage review builder.
  Evidence note:
  `tests/test_du_export_coverage_review.py` now verifies the tracked-profile, donor-review, and backlog classification logic, markdown rendering, and output writing for the 10-export coverage artifact. `tests/test_refresh_mw_du_discovery_packet.py` now also verifies that the coverage review stays inside the single refresh path.
- [x] Add automated verification for the missing-field bridge review builder.
  Evidence note:
  `tests/test_missing_field_bridge_review.py` now covers donor-export selection for missing PR-status fields, including the stronger TX Mini to `2023 TX Rollout` bridge and the weaker MW EOS Swap case. It now also verifies that bridge entries expose `profile_version`, `mapping_version`, and `observed_header_hash` for the blocked profile.
- [x] Add automated verification for generic profile recognition in the discovery registry and for the ZTE TX MINI DRAFT profile.
  Evidence note:
  `tests/test_du_discovery_registry.py` now verifies that the registry builder discovers `mw_eos_swap_pr_v1` from the live profile files rather than from a hardcoded special case, and `tests/test_du_profile_loader.py` now covers `zte_tx_mini_pr_v1` plus the corrected TX Mini identity view ID.
- [x] Add automated verification for the MW-pair divergence review builder.
  Evidence note:
  `tests/test_mw_pair_divergence_review.py` now covers matching selections, differing selections, shared missing required fields, traceable profile/header-hash identity, and markdown rendering for the MW EOS vs ZTE comparison.
- [x] Extend shortlist and unresolved-review verification to the ZTE TX MINI DRAFT profile.
  Evidence note:
  `tests/test_skill_field_shortlists.py` now verifies that the generated shortlist registry includes the ZTE TX MINI priority entry, and `tests/test_unresolved_skill_field_review.py` now covers the ZTE DRAFT profile’s missing required PR-status fields and competing shortlist candidates.
- [x] Extend missing-field bridge verification to the ZTE TX MINI DRAFT profile and then to the full five-profile bridge registry.
  Evidence note:
  `tests/test_missing_field_bridge_review.py` now verifies the ZTE donor-review path and confirms that the bridge registry carries all 10 tracked DRAFT profiles together, including `cd_consolidation_2023_decom_pr_v1` and `cd_consolidation_2023_rollout_pr_v1`.
- [x] Add automated verification for the profile-readiness review builder.
  Evidence note:
  `tests/test_profile_readiness_review.py` now verifies that the readiness review keeps TX Mini discovery-only blocked, records the MW EOS Swap required-but-unapproved fields, and renders mapping-version plus blocker context in the markdown output.
- [x] Add automated verification for the deprecation review path.
  Evidence note:
  `tests/test_profile_deprecation_review.py` now verifies both the synthetic happy path for a controlled deprecation record and the live `NO_DEPRECATION_PLAN` state for the current DRAFT profiles. `tests/test_du_profile_loader.py` now rejects a `DEPRECATED` profile without deprecation metadata, and `tests/test_profile_status_consistency.py` rejects a claimed `DEPRECATED` status unless the deprecation review is recorded.
- [x] Add automated verification for the profile traceability audit.
  Evidence note:
  `tests/test_profile_traceability_audit.py` now verifies that the live priority DRAFT profiles are marked `TRACEABLE` across the tracked profile-centric artifacts, including tracked-profile coverage and rollback-readiness, that a synthetic registry mismatch downgrades the result to `TRACEABILITY_REVIEW_REQUIRED`, and that the markdown output surfaces the traceability status clearly.

### Acceptance Criteria

- [ ] Every enabled DU model resolves to one approved profile and profile version.
- [ ] Unknown model/view combinations are quarantined.
- [ ] Header changes require re-profiling and re-approval.
- [ ] Each production profile has passing positive and negative regression tests.
- [ ] Shared generator logic remains common unless a formally approved business difference requires a model-specific rule.

Blocker:
The registry and inventory now exist, but the entries remain discovery-only because approved mappings, approved header hashes, and production-ready profile versions do not yet exist for the newly profiled DUs.

---

## Phase 4 — Integration, Operations, and Release Governance

**Purpose:** Make profile onboarding repeatable, auditable, and safe for operational use.

### Activities

- [ ] Integrate approved Canonical PR Site Records into the existing PR generation path.
- [ ] Retain the existing generator as the final output engine until replacement is explicitly approved.
- [x] Define a quarantine report format for blocked records.
- Evidence note:
  `docs/MW_DU_Quarantine_Report_Format.md` now defines a structured review packet for blocked canonical PR input records, and `scripts/quarantine_report.py` implements the reporting shape using only the skill-relevant fields from `SKILL.md`. The report now also self-validates `entry_count`, `decision_counts`, the `allow_output` to `output_decision` relationship, and the exact `skill_field_review` field set so a stale summary or truncated field-review section cannot look trustworthy. `tests/test_quarantine_report.py` verifies the audit payload, the limited field set, the explicit `mapping_version`, the no-output decision rendering, representative report-consistency failures, and the builder's fail-closed behavior when an inconsistent entry is supplied.
- [x] Define manual correction and resubmission workflow for incomplete records.
- Evidence note:
  `docs/MW_DU_Manual_Correction_and_Resubmission_Workflow.md` now defines the correction path for `PR_INPUT_INCOMPLETE` and `PR_INPUT_QUARANTINED` records using the live blocking reasons emitted by `scripts/canonical_site_validator.py` and `scripts/pr_input_guard.py`. The workflow requires resubmission through the same adapter/validator path, preserves `profile_version` and `mapping_version`, and explicitly keeps lifecycle approvals out of routine correction.
- [x] Add operator documentation for profiling, mapping review, profile approval, release, and rollback.
- Evidence note:
  `docs/MW_DU_Operator_Runbook.md` now documents the operator procedure for profiling, shortlist-led mapping review, profile approval evidence, controlled release progression, monitoring, and configuration-first rollback. The runbook references the live discovery reviews, quarantine packet, and resubmission workflow, while keeping DRAFT profiles and UAT approval explicitly blocked from runtime enablement.
- [x] Add audit fields: source export identity, DU Profile ID/version, Header Hash, mapping version, field provenance, validation result, and output decision.
- Evidence note:
  The canonical record contract in `scripts/canonical_site_validator.py` now requires `validation.mapping_version` and carries a fail-closed `validation.output_decision`, `scripts/du_export_adapter.py` propagates the profile identity and mapping version from the loaded DU profile, `scripts/pr_input_guard.py` stamps the final runtime output decision onto the guarded canonical record, and `scripts/quarantine_report.py` exposes source export identity, DU profile ID/version, Header Hash, mapping version, field provenance, validation result, and output decision in the review packet. Coverage now lives in `tests/test_du_export_adapter.py`, `tests/test_canonical_site_validator.py`, and `tests/test_quarantine_report.py`.
- [x] Add a runtime traceability review for guarded canonical records.
- Evidence note:
  `scripts/canonical_output_traceability_report.py` now builds a reporting-only runtime traceability packet for guarded canonical records. The review checks that `profile_id`, `profile_version`, `mapping_version`, `header_hash`, `source_file_hash`, and `output_decision` are present before an entry can be marked `TRACEABLE`; otherwise it stays `TRACEABILITY_REVIEW_REQUIRED`. The report now also self-validates its `entry_count`, `traceability_counts`, and entry status-to-gap consistency, and it recomputes the expected gap set from the embedded profile/identity/audit fields so a stale entry cannot quietly omit a required gap code. `docs/MW_DU_Canonical_Output_Traceability_Report.md` records the packet shape and fail-closed rule, and `tests/test_canonical_output_traceability_report.py` covers both the traceable happy path, representative consistency failures, and the builder's fail-closed behavior when an inconsistent entry is supplied.
- [x] Define profile-change authority and approval responsibilities.
- Evidence note:
  `docs/MW_DU_Operator_Runbook.md` now separates operator/analyst, technical maintainer, and business approver responsibilities so mapping inference, profile editing, and production approval are not collapsed into one undocumented step.
- [x] Define release sequence: test → UAT → controlled production → monitoring → broader rollout.
- Evidence note:
  `docs/MW_DU_Operator_Runbook.md` now captures the controlled release path from profiling through regression verification, UAT, lifecycle advancement, monitoring, and broader rollout, while preserving the current approval gates.
- [x] Add a machine-checkable lifecycle transition review for priority DU profiles.
- Evidence note:
  `config/registries/mw_du_profile_transition_review.yaml` and `docs/MW_DU_Profile_Transition_Review.md` now evaluate the current DRAFT profiles against the repository lifecycle targets `PROFILED`, `BUSINESS_VALIDATED`, `PR_INPUT_READY`, and `PRODUCTION`. The review stays fail-closed: intermediate promotions are denied for concrete evidence gaps such as missing required fields or unapproved mappings, while `PRODUCTION` remains additionally blocked by the explicit non-production lifecycle state.
- [x] Add a profile-status consistency guard so profile files cannot outrun the transition review.
- Evidence note:
  `scripts/check_profile_status_consistency.py` now compares each DU profile's declared status with the generated transition review and fails closed when a profile claims a lifecycle stage that its evidence does not support. It now also rejects a `DEPRECATED` status unless the deprecation review is recorded. `tests/test_profile_status_consistency.py` verifies that the current DRAFT profiles pass, that a synthetic premature promotion is rejected, that a synthetic unreviewed deprecation is rejected, and that missing transition-review coverage also fails closed.
- [x] Add a cross-artifact discovery-packet consistency guard for the priority DRAFT profiles.
- Evidence note:
  `scripts/check_discovery_packet_consistency.py` now verifies that the live DU profiles agree with the discovery registry, unresolved review, bridge review, readiness review, transition review, deprecation review, traceability audit, rollback-readiness review, and 10-export coverage review on status, mapping version, observed header hash, and missing-required-field bridge coverage. The bridge, traceability, rollback, and tracked-profile coverage entries are also checked for `profile_version` consistency where applicable, the traceability audit must now also contain the full expected artifact set for each tracked profile, and the untracked exports are fail-closed checked for donor-review versus backlog classification drift, summary-count drift, and `missing_skill_fields` drift. `tests/test_discovery_packet_consistency.py` verifies the live happy path and fails closed on representative registry drift, including deprecation-review status drift, traceability-audit drift, missing traceability-artifact coverage, bridge traceability-field drift, rollback header-hash drift, tracked-profile coverage drift, donor/backlog coverage drift, summary-count drift, and missing-skill-field drift.
- [x] Add a single refresh path for the tracked MW DU discovery packet.
- Evidence note:
  `scripts/refresh_mw_du_discovery_packet.py` now rebuilds the discovery registry, shortlist, unresolved review, grouping review, bridge review, MW pair divergence review, readiness review, action queue, review matrix, 10-export coverage review, transition review, deprecation review, rollback-readiness review, and traceability audit in one pass, then runs the status and packet consistency guards. The traceability audit is intentionally regenerated after rollback-readiness so it covers the full live profile-centric packet. `tests/test_refresh_mw_du_discovery_packet.py` verifies the orchestrated call order so the refresh path remains repeatable.
- [x] Add a fail-closed rollback-readiness review for tracked DU profiles.
- Evidence note:
  `scripts/build_profile_rollback_readiness.py` now generates `config/registries/mw_du_profile_rollback_readiness.yaml` and `docs/MW_DU_Profile_Rollback_Readiness.md`. The review records whether a tracked profile has an approved rollback baseline and blocks release-time rollback claims when approved header hashes or a released lifecycle state do not yet exist. `tests/test_profile_rollback_readiness.py` covers both the blocked live DRAFT state and a synthetic released-profile baseline case.
- [ ] Conduct end-to-end UAT using real approved project scenarios.

### Acceptance Criteria

- [ ] Every output is traceable to a profile version and Header Hash.
- [x] Quarantined records contain actionable reasons and no ECC output is produced.
- [x] Profile changes follow an approved review process.
- [ ] Rollback to a previous approved profile version is documented and tested.
- [ ] End-to-end UAT is signed off before each new model enters production.

Blocker:
Runtime traceability reporting now exists for guarded canonical records, but the repository still does not have approved production-enabled DU profiles or end-to-end generator-path integration for new MW DU models, so the full output-traceability acceptance claim remains intentionally unproven.

Blocker:
Rollback readiness is now documented and machine-checked, but the current tracked profiles remain `ROLLBACK_BLOCKED` because they are still `DRAFT` and do not yet have approved header-hash baselines or approved released profile versions to roll back to.

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

1. Confirm whether the 10 external DU exports in `C:\Users\Win11-JJ\Downloads\du-20260706` are approved sanitized fixtures for development evidence.
2. Review the generated profiler outputs under `output/du-20260706-profile/`, starting with TX Mini and MW EOS Swap, to convert the keyword-discovery shortlist and unresolved review packet into explicit four-layer source-field decisions. For TX Mini this review input now exists as the local-only mapping-decision package under `output/du-20260706-profile/tx-mini-mapping-review/`; JJ's `Decision_Log` entries there are the next required input before any mapping can be written back to `tx_mini_pr_v1`.
3. Use `scripts/build_du_discovery_registry.py` as the repeatable path for refreshing `config/registries/mw_du_model_discovery_registry.yaml` and `docs/MW_DU_Discovery_Inventory.md` whenever new DU exports are profiled.
4. Use `scripts/build_skill_field_shortlists.py`, `scripts/build_unresolved_skill_field_review.py`, `scripts/build_du_structure_grouping.py`, and `scripts/build_missing_field_bridge_review.py` with their companion docs as the review starting point for TX Mini, MW EOS Swap, 2023 TX Rollout, Jendela TX Migration, ZTE TX MINI, and the next reuse-candidate DU validation sessions.
5. Review `2023 TX Rollout` as the first donor-reference export for missing PR-status fields on TX Mini, MW EOS Swap, Jendela TX Migration, and ZTE TX MINI, while keeping cross-model reuse explicitly unapproved until four-layer field confirmation and business validation exist.
6. Use `docs/MW_DU_MW_Pair_Divergence_Review.md` as the review checklist for MW EOS Swap vs ZTE TX MINI before attempting any shared-profile or shared-rule claim, especially around `tx_sow_raw`, `site_code`, `subcontractor_ti`, and the antenna fields.
7. Keep `tx_mini_pr_v1`, `mw_eos_swap_pr_v1`, `tx_rollout_2023_pr_v1`, `jendela_tx_migration_pr_v1`, `zte_tx_mini_pr_v1`, `celcomdigi_bau_2023_pr_v1`, `celcomdigi_bau_2024_pr_v1`, `celcomdigi_usp_pr_v1`, `cd_consolidation_2023_decom_pr_v1`, and `cd_consolidation_2023_rollout_pr_v1` in `DRAFT` and preserve fail-closed blocking tests until approved source evidence exists for validation work.

---

## 10. Definition of Done

The extension is complete only when:

- [ ] TX Mini runs through the canonical-input path with proven golden parity.
- [ ] At least one new MW DU model, proposed as MW EOS Swap, is enabled through an approved profile.
- [ ] Every enabled MW DU model is routed through a controlled DU Profile.
- [ ] All enabled profiles have approved Header Hashes, mapping traceability, and regression tests.
- [ ] Unknown, changed, incomplete, ambiguous, and unverified inputs fail closed.
- [x] Existing PR/ECC business logic remains controlled and regression-protected.
- [x] The operational team has documented procedures for profile onboarding, approval, change management, quarantine handling, and rollback.
