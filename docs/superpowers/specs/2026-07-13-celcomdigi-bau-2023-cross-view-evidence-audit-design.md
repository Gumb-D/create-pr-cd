# 2023 Celcomdigi BAU Cross-View Evidence Audit Design

## 1. Purpose

Define a read-only, local-only evidence audit for the `2023 Celcomdigi BAU` DU identity. The audit determines whether direct source evidence exists for all seven PR-input mappings required to prepare a later `PR_INPUT_READY` onboarding design.

The audit itself must not approve mappings, modify the tracked DU profile, create PR or ECC output, or commit customer exports.

## 2. Identity and Scope

The authoritative identity is:

- Project: `Malaysia_CelcomDigi_Project`
- DU Model: `2023 Celcomdigi BAU`
- DU Model ID: `8296022438223590261`
- Current profile: `celcomdigi_bau_2023_pr_v1`
- Current lifecycle: `DRAFT`

The audit scans every local reference export under `Info/reference` that can be attributed to this Project + DU Model identity. View ID is evidence metadata, not an identity boundary. Multiple exports, versions, and Views may be included when they represent the same Project + DU Model.

Files from other DU Models may be used only to improve search keywords or explain field semantics. They must not be used as approval evidence or as a substitute for direct 2023 BAU evidence.

## 3. Target Runtime Fields

The audit must assess these seven fields:

1. `site_code`
2. `tx_sow_raw`
3. `region`
4. `subcontractor_tss`
5. `subcontractor_ti`
6. `existing_tss_pr_status`
7. `existing_ti_pr_status`

The currently tracked evidence suggests credible candidates for the first five fields. The two existing-PR duplicate-prevention fields remain the primary blockers and require a full-header search beyond the current shortlist.

## 4. Source Discovery

The audit must inventory local files before profiling them.

A file is in scope when available metadata, filename structure, profiler output, or embedded identity evidence supports all of the following:

- Project is `Malaysia_CelcomDigi_Project`;
- DU Model is `2023 Celcomdigi BAU`;
- DU Model ID is `8296022438223590261`, when the ID is present;
- the file is an original iEPMS-style export or a faithful local reference copy.

Each included file must record:

- local relative path;
- source filename;
- file SHA-256;
- export format;
- detected View ID, when available;
- detected DU Model ID, when available;
- Header Hash;
- sheet names;
- inclusion rationale.

Files with conflicting identity evidence must be excluded and recorded with the reason.

## 5. Read-Only Profiling

Use the repository's existing four-header profiler wherever possible. Profiling must:

- read the first four header layers;
- preserve exact raw and normalized header values;
- calculate deterministic Header Hashes;
- identify columns by exact four-layer fingerprint rather than index;
- produce only discovery evidence marked `UNVERIFIED`;
- never generate PR or ECC output.

The audit may add a local-only helper under `output/` when existing scripts cannot aggregate multiple exports, but it must not modify tracked generator behavior during this evidence phase.

## 6. Full-Header Candidate Search

The audit must search the complete four-layer inventory, not only the tracked shortlist.

Search terms must cover, at minimum:

- `Subcon PR - TSS`
- `Subcon PR - TI`
- `PR TSS Status`
- `PR TI Status`
- `TSS PR`
- `TI PR`
- `TSS status`
- `TI status`
- `PR reference`
- `PR status`
- `SQ`
- equivalent abbreviations or field codes discovered in the same DU Model

Candidate ranking must consider all four header layers and reject semantic false positives such as:

- milestone planned or actual timestamps;
- TSSR approval dates;
- planning PR fields used as TI PR evidence;
- rectification milestones that are not duplicate-prevention references;
- fields from another DU Model.

## 7. Data Evidence Statistics

For every candidate relevant to the seven target fields, collect safe summary statistics from the source column:

- total data rows;
- non-empty rows;
- blank rows;
- unique non-empty value count;
- normalized value categories;
- a bounded set of redacted or pattern-level examples;
- apparent value type, such as free text, status, reference number, date, Boolean-like marker, or mixed;
- consistency across files and Header Hashes.

The audit must not write complete site-level rows or unrestricted raw values into the output packet. Examples must be redacted, summarized, or represented as patterns sufficient for human review.

## 8. Cross-View Comparison

For each target field, build a matrix across all included exports and Header Hashes showing:

- exact fingerprint;
- View ID;
- Header Hash;
- presence or absence;
- non-empty count;
- candidate classification;
- whether the same fingerprint is reusable across Views;
- whether one profile could safely support all proposed Header Hashes.

Different Views may use different fingerprints. This is acceptable only when every fingerprint is directly evidenced, unambiguous within its Header Hash, and explicitly represented in the later profile design.

## 9. Candidate Classification

Each candidate must receive one of these classifications:

- `DIRECT_APPROVAL_CANDIDATE`: exact business meaning and value evidence align with the canonical field;
- `HUMAN_REVIEW_REQUIRED`: plausible but ambiguous, inconsistent, or insufficiently populated;
- `REJECTED_SEMANTIC_MISMATCH`: name or value semantics do not match the canonical field;
- `REJECTED_CROSS_DU_EVIDENCE`: evidence belongs to another DU Model;
- `MISSING`: no candidate found within the audited identity.

The audit does not change `mapping_status` to `APPROVED`. Final approval remains a separate human decision.

## 10. Audit Decision

The local `decision.json` must use exactly one of these results.

### `ONBOARDING_DESIGN_READY`

Use only when all conditions hold:

- direct same-DU evidence exists for all seven target fields;
- each required mapping resolves uniquely for every proposed Header Hash;
- existing TSS and TI PR fields clearly support duplicate prevention;
- value evidence is non-empty and business-meaningful;
- cross-View differences can be represented safely by one profile;
- no mapping relies on column position or approval inherited from another DU Model.

### `HUMAN_REVIEW_REQUIRED`

Use when evidence exists but a human must choose among candidates, resolve View-specific semantics, or confirm value meaning.

### `KEEP_DRAFT_QUARANTINED`

Use when either duplicate-prevention field remains missing, only cross-DU evidence exists, or the available candidate is a semantic mismatch.

## 11. Local Output Packet

Write all outputs under:

```text
output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/
```

Required files:

- `audit_summary.md`
- `export_inventory.json`
- `header_hash_matrix.md`
- `pr_field_candidate_review.md`
- `non_empty_statistics.json`
- `rejected_candidates.md`
- `decision.json`

When and only when `decision.json` is `ONBOARDING_DESIGN_READY`, also generate:

- `onboarding_design_draft.md`

The packet must be reproducible and deterministic for the same source files.

## 12. Conditional Onboarding Design Draft

The local onboarding design draft must contain:

- proposed profile version and mapping version;
- retained profile ID `celcomdigi_bau_2023_pr_v1`;
- Project + DU Model identity;
- proposed accepted View IDs;
- proposed approved Header Hashes;
- exact four-layer fingerprints for all seven fields;
- transforms, including `normalize_pr_reference_status` for both existing-PR fields when supported by evidence;
- required fail-closed tests for changed Header Hash, missing source evidence, ambiguous mapping, and blank scope-specific subcontractor values;
- governance refresh scope;
- rollback baseline;
- confirmation that lifecycle would stop at non-production `PR_INPUT_READY`;
- confirmation that ECC remains blocked until separate `PRODUCTION` approval and golden-output evidence.

The draft is evidence-derived but not approved. It must remain under ignored `output/` until the user reviews it.

## 13. Verification

The audit execution must verify:

- repository working tree was clean before the audit;
- tracked files are unchanged after the audit;
- no file under `Info/reference` or `output/` became tracked;
- every included export matches the intended Project + DU Model identity;
- every fingerprint contains all four header layers;
- output counts reconcile across inventory, statistics, matrix, and decision files;
- rerunning against the same inputs produces the same Header Hashes and decision;
- no PR or ECC artifact was generated.

## 14. Safety Boundaries

The audit must not:

- modify `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml`;
- modify any other DU profile;
- approve a Header Hash or field mapping;
- modify generator, adapter, ECC template, PR model, or SOW rules;
- commit raw exports or anything under `Info/reference`;
- commit local audit outputs under `output/`;
- create a pull request for onboarding;
- infer approval from `2023 TX Rollout`, `2024 Celcomdigi BAU`, Jendela, or any other profile;
- promote any profile to `PR_INPUT_READY` or `PRODUCTION`;
- enable ECC output.

## 15. Acceptance Criteria

The audit is complete when:

- all local exports attributable to the target Project + DU Model have been inventoried;
- the seven target fields have a documented evidence classification across all relevant Header Hashes;
- non-empty statistics and safe examples are available for every candidate;
- rejected false positives are documented;
- `decision.json` is supported by the evidence packet;
- `onboarding_design_draft.md` exists only when the decision is `ONBOARDING_DESIGN_READY`;
- the Git working tree remains clean and no local reference or output file is tracked.
