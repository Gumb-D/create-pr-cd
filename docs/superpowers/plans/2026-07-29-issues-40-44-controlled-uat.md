# Issues #40–#44 Controlled UAT Delivery Plan

## Goal

Complete the confirmed subcontractor policy, approved contract data, contract fail-closed validation, TX Rollout header revalidation, and consolidated all-DU UAT orchestration without promoting any DU Profile to `PRODUCTION`.

## Delivery order

1. **#40 — SM exclusion policy**
   - Add `config/subcontractor_pr_policy.json`.
   - Load it fail-closed.
   - Apply it before duplicate, canonical-readiness, and contract validation.
   - Preserve deterministic reason codes and summary counts.

2. **#41 — Approved contract mappings**
   - Add Nera and Perwira exactly as approved.
   - Preserve all existing mappings.
   - Test Nera, Perwira, and CCSMY.

3. **#42 — Missing contract fail-closed**
   - Parse the approved contract reference before renderer invocation.
   - Move unmapped candidates to `REVIEW_REQUIRED` with `CONTRACT_MAPPING_NOT_FOUND`.
   - Generate dedicated contract review evidence and summary fields.
   - Ensure SM is excluded before this check.

4. **#43 — TX Rollout compatible header**
   - Minimal profile diff only.
   - Keep `mapping_version` and `PR_INPUT_READY` unchanged.
   - Preserve the previous hash and add the 2026-07-28 hash.

5. **#44 — Consolidated UAT runner**
   - Add an explicit JSON input manifest and template.
   - Run the official `create_pr.run` interface in `NON_PRODUCTION_UAT` mode for TSS and TI.
   - Isolate profile/scope failures.
   - Produce deterministic Review Pack and Full Pack directories.
   - Generate `UAT_MASTER_MANIFEST.xlsx`, JSON summary, and blocked-profile CSV.
   - Record missing source exports explicitly; never guess paths or silently omit profiles.

## Safety constraints

- No profile lifecycle promotion.
- No automatic Header Hash approval.
- No `SM` record reaches contract validation or renderer input.
- No missing/blank/`UNKNOWN` contract reaches renderer input.
- No generated UAT workbook or customer export is committed.
- The batch runner reuses the official #39 UAT path and does not implement another lifecycle bypass.

## Verification

- TDD for policy, contract parsing, partitioning, review reports, summary fields, profile metadata, sampling, manifest reconciliation, and failure isolation.
- Targeted tests for all new modules and the official entrypoint.
- Full regression suite, with any pre-existing environment-only failure demonstrated against `main`.
- Syntax and `git diff --check`.
- Draft PR review before merge.

## Completion boundary

Code and automated fixture evidence can be completed in-repository. A real eight-profile business UAT run additionally requires the corresponding current raw iEPMS exports. Missing exports must be reported as `MISSING_SOURCE_EXPORT` and do not permit fabricated output.