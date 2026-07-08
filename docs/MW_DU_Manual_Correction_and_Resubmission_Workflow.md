# MW DU Manual Correction And Resubmission Workflow

This workflow defines how a blocked canonical PR input record can be corrected and resubmitted without bypassing the repository's fail-closed controls.

It applies to records reported through the quarantine review packet in [MW_DU_Quarantine_Report_Format.md](/C:/dev/create-pr-cd/docs/MW_DU_Quarantine_Report_Format.md).

## Workflow Goals

- keep blocked records out of ECC generation until the underlying issue is corrected
- preserve traceability across source export, DU profile version, mapping version, and resubmission attempt
- distinguish incomplete-data correction from model-identity quarantine
- keep all mapping approval and profile-promotion steps explicitly gated

## Decision Split

Use the validation result first:

- `PR_INPUT_INCOMPLETE`: the record is missing required business data or required audit metadata; correction may be possible within the same DU model/profile boundary
- `PR_INPUT_QUARANTINED`: the record hit a higher-risk block such as ambiguous mapping, unknown profile/model identity, unverified normalization, or non-production profile status; resubmission still requires the same guard path and may also require profile review rather than row-level correction

## Correction Sources

Only these correction sources are allowed:

1. A re-profiled or re-exported source file from the same approved business source.
2. A reviewed DU profile update that changes the selected four-layer fingerprint or transform under version control.
3. Approved reference-data correction for derived fields that are already part of the controlled pipeline.

Do not:

- edit the ECC output directly
- patch a blocked record into a ready state outside the profile/validator path
- invent missing PR status, subcontractor, SOW, or antenna values without approved source evidence
- promote a DRAFT profile as part of routine correction

## Resubmission Steps

1. Capture the blocked packet.
   Record the source export identity, `profile_id`, `profile_version`, `mapping_version`, `header_hash`, `blocking_reasons`, and `output_decision`. Prefer the guarded canonical record's `validation.output_decision` so the resubmission note preserves the exact runtime gate result.
2. Classify the blocker.
   Split blockers into source-data issues, mapping issues, audit-metadata issues, and lifecycle/approval issues.
3. Correct at the lowest safe layer.
   If source data is missing or malformed, obtain a corrected source export. If a mapping is wrong or incomplete, update the DU profile under review. If audit metadata is missing, regenerate the canonical record through the updated adapter/profile path.
4. Rebuild the canonical record.
   Re-run the adapter and validator so the record receives a fresh validation result rather than carrying a hand-edited status.
5. Re-run the quarantine review.
   Confirm whether the record remains blocked, moved from `PR_INPUT_QUARANTINED` to `PR_INPUT_INCOMPLETE`, or became `PR_INPUT_READY_WITH_REVIEW` / `PR_INPUT_READY` inside the allowed lifecycle boundary.
6. Preserve resubmission evidence.
   Store the new `mapping_version`, profile version, header hash, and blocking-reason delta in the review notes for the next approval session.

## Blocking-Reason Handling Guide

| Blocking reason family | Typical action | Resubmission expectation |
|---|---|---|
| `MISSING_PR_CRITICAL_FIELD:*` | obtain corrected source or approved upstream data | usually same profile, new source export |
| `MISSING_SOURCE_EVIDENCE:*` | rebuild through adapter/profile so provenance is populated | same profile or reviewed profile edit |
| `MISSING_MAPPING_VERSION` | regenerate with a profile that declares `mapping_version` | same source, refreshed canonical record |
| `AMBIGUOUS_HEADER_MAPPING:*` | review four-layer fingerprint selection in the DU profile | requires profile-review evidence |
| `UNKNOWN_DU_PROFILE` / `UNKNOWN_DU_MODEL_OR_VIEW` | profile or registry review | cannot be solved by row-only edits |
| `HEADER_HASH_REVALIDATION_REQUIRED` | re-profile and review header change | requires header review before any output |
| `UNVERIFIED_SOURCE_MAPPING:*` | keep blocked until mapping review advances | no output from DRAFT discovery state |
| `UNVERIFIED_NORMALIZATION:*` | add or approve the controlled normalization path | still blocked until verified |
| `DU_PROFILE_NOT_PRODUCTION` | lifecycle/approval gate only | correction alone does not enable output |

## Required Resubmission Evidence

Each resubmission attempt should capture:

- original source file name and hash
- original and resubmitted header hash
- original and resubmitted `profile_version`
- original and resubmitted `mapping_version`
- original and resubmitted blocking reasons
- reviewer notes on whether the change was source-driven, mapping-driven, or approval-gated

## Current Repository Boundaries

This workflow does not:

- approve any of the current DRAFT MW DU profiles
- replace business validation or UAT
- bypass `scripts/pr_input_guard.py`
- modify `scripts/generate_tss_pr_ecc.py`

The current repository state supports traceable review and safe resubmission preparation only.
