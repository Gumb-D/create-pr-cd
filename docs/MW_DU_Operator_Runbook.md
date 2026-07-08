# MW DU Operator Runbook

This runbook describes the operator-facing workflow for profiling, mapping review, profile approval, controlled release, monitoring, and rollback of MW DU export onboarding.

It is intentionally aligned to the repository's current capabilities:

- discovery-only profiling and review artifacts are supported now
- fail-closed canonical validation and quarantine reporting are supported now
- production promotion, UAT sign-off, and runtime enablement remain approval-gated

## 1. Operating Principles

- Treat every new DU export as untrusted until its four-layer fingerprints, header hash, and mapping decisions are reviewed.
- Keep discovery artifacts separate from approval-bearing profile state.
- Never enable ECC generation from a `DRAFT` profile.
- Use repository evidence, not memory or spreadsheet screenshots, as the approval record.
- When in doubt, quarantine and review rather than infer.

## 2. Inputs And Evidence Sources

Operators should use these repository artifacts together:

- discovery inventory: [MW_DU_Discovery_Inventory.md](/C:/dev/create-pr-cd/docs/MW_DU_Discovery_Inventory.md)
- structure grouping review: [MW_DU_Structure_Grouping_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Structure_Grouping_Review.md)
- priority shortlist review: [MW_DU_Priority_Skill_Field_Shortlists.md](/C:/dev/create-pr-cd/docs/MW_DU_Priority_Skill_Field_Shortlists.md)
- unresolved review packet: [MW_DU_Unresolved_Skill_Field_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Unresolved_Skill_Field_Review.md)
- MW pair divergence review: [MW_DU_MW_Pair_Divergence_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_MW_Pair_Divergence_Review.md)
- missing-field bridge review: [MW_DU_Missing_Field_Bridge_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Missing_Field_Bridge_Review.md)
- profile action queue: [MW_DU_Profile_Action_Queue.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Action_Queue.md)
- profile review matrix: [MW_DU_Profile_Review_Matrix.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Review_Matrix.md)
- profile deprecation review: [MW_DU_Profile_Deprecation_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Deprecation_Review.md)
- profile rollback readiness review: [MW_DU_Profile_Rollback_Readiness.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Rollback_Readiness.md)
- profile traceability audit: [MW_DU_Profile_Traceability_Audit.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Traceability_Audit.md)
- DU export coverage review: [MW_DU_Export_Coverage_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Export_Coverage_Review.md)
- canonical output traceability report format: [MW_DU_Canonical_Output_Traceability_Report.md](/C:/dev/create-pr-cd/docs/MW_DU_Canonical_Output_Traceability_Report.md)
- quarantine packet format: [MW_DU_Quarantine_Report_Format.md](/C:/dev/create-pr-cd/docs/MW_DU_Quarantine_Report_Format.md)
- correction and resubmission workflow: [MW_DU_Manual_Correction_and_Resubmission_Workflow.md](/C:/dev/create-pr-cd/docs/MW_DU_Manual_Correction_and_Resubmission_Workflow.md)

## 3. Profiling Procedure

1. Receive a sanitized DU export from the approved business source.
2. Run the profiler in read-only mode to capture:
   - header inventory
   - header hash
   - canonical-field candidates
   - missing PR-critical fields
   - draft DU profile template
3. Confirm the output stays in discovery-only locations and does not overwrite approved profile state.
4. Refresh the model inventory and any review builders that depend on the new profile set.
5. Record the observed `header_hash`, `profile_id`, `profile_version`, and `mapping_version` in the review session notes.
6. When two exports share the same DU model name, keep the review keyed by `header_hash` and profile identity rather than by DU model name alone.

Current repository tools:

- `scripts/refresh_mw_du_discovery_packet.py`
- `scripts/profile_du_export.py`
- `scripts/build_du_discovery_registry.py`
- `scripts/build_skill_field_shortlists.py`
- `scripts/build_unresolved_skill_field_review.py`
- `scripts/build_du_structure_grouping.py`
- `scripts/build_missing_field_bridge_review.py`
- `scripts/build_mw_pair_divergence_review.py`
- `scripts/build_profile_action_queue.py`
- `scripts/build_profile_review_matrix.py`
- `scripts/build_profile_deprecation_review.py`
- `scripts/build_profile_rollback_readiness.py`
- `scripts/build_profile_traceability_audit.py`
- `scripts/build_du_export_coverage_review.py`
- `scripts/canonical_output_traceability_report.py`

Preferred refresh path:

- Run `scripts/refresh_mw_du_discovery_packet.py` to rebuild the tracked discovery registry, shortlist, unresolved review, grouping review, bridge review, MW pair divergence review, readiness review, action queue, review matrix, 10-export coverage review, transition review, deprecation review, rollback-readiness review, and traceability audit in one pass.
- The refresh script ends by running both `scripts/check_profile_status_consistency.py` and `scripts/check_discovery_packet_consistency.py`, so a stale or internally inconsistent packet fails immediately, including drift between the live discovery registry and the 10-export coverage review for tracked-profile, donor-review, backlog, summary-count, and missing-skill-field evidence.

## 4. Mapping Review Procedure

1. Start with the priority shortlist for skill-relevant fields only.
2. Confirm every selected source candidate by exact four-layer fingerprint, not by label similarity alone.
3. When the same DU model name appears in more than one export variant, confirm the shortlist and unresolved packet still point at the same `header_hash` and `source_file_name` as the target profile.
4. Use the unresolved review packet to identify:
   - missing required fields
   - competing shortlist candidates
   - unverified single-candidate selections
5. Use the profile review matrix to batch repeated blocker themes across the current DRAFT profiles before dropping into profile-specific review.
6. Use the profile action queue to decide review order within the current session once the shared blockers are understood.
7. Use the structure grouping and pair divergence reviews only as review aids.
8. Treat cross-model bridge suggestions as leads for manual inspection, not reusable approval.
9. Update the DU profile under version control only after the review session chooses one explicit mapping path.

Approval boundary:

- Discovery notes, shortlists, and bridge hints do not count as production approval.
- A required field is not approved merely because another DU model carries a similar display header.
- Runtime traceability reports document whether a guarded canonical record is audit-complete; they do not approve output by themselves.

## 5. Profile Approval Procedure

Before any profile can advance beyond discovery:

1. Confirm the DU model identity and `view_id`.
2. Confirm the observed `header_hash`.
3. Confirm the selected four-layer fingerprint for every required canonical field.
4. Confirm each controlled transform and normalization path.
5. Confirm that unresolved required fields are either:
   - solved from approved source evidence
   - formally blocked from release
6. Confirm regression coverage for the profile path.
7. Confirm business review and UAT evidence outside the discovery-only artifacts.

Required approval record:

- `profile_id`
- `profile_version`
- `mapping_version`
- approved header hash
- approver names or business sign-off reference
- release decision date

## 6. Profile-Change Authority

The repository should treat these responsibilities distinctly:

- Operator / analyst:
  - run profilers
  - refresh discovery registries
  - prepare shortlist and unresolved review packets
  - collect correction and resubmission evidence
- Technical maintainer:
  - edit DU profile files
  - update validation or reporting code
  - maintain regression tests
  - prepare release candidates
- Business approver:
  - approve source-field semantics
  - approve duplicate-prevention field interpretation
  - approve any model-specific business-rule difference
  - sign off on UAT and production release

No single operator should both infer an unreviewed mapping and approve it for production in the same step.

## 7. Release Sequence

The controlled release path is:

1. Profiling
2. Mapping review
3. DU profile update under version control
4. Regression verification
5. UAT with approved business scenarios
6. Controlled lifecycle advancement
7. Monitoring after enablement
8. Broader rollout only after stable evidence

Lifecycle guidance:

- `DRAFT`: discovery only
- `PROFILED` or `BUSINESS_VALIDATED`: controlled pre-production review state if the team adopts those lifecycle values later
- `PR_INPUT_READY` / `PRODUCTION`: only after approval, regression, and UAT evidence

Machine-checkable support:

- [MW_DU_Profile_Transition_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Transition_Review.md) is the repository's conservative lifecycle-promotion check for the current priority DRAFT profiles.
- [MW_DU_Profile_Deprecation_Review.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Deprecation_Review.md) records whether any tracked profile has entered a controlled deprecation path with successor, rollback, and superseded-header-hash evidence.
- [MW_DU_Profile_Rollback_Readiness.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Rollback_Readiness.md) records whether a tracked profile has an approved rollback baseline or remains fail-closed blocked pending approved release evidence.
- [MW_DU_Profile_Traceability_Audit.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Traceability_Audit.md) shows whether the current profile-centric review artifacts all carry the live `profile_version`, `mapping_version`, and observed header hash for each tracked profile.
- Treat any denied transition as a stop signal until the underlying evidence gap is resolved in version-controlled review artifacts.
- Run `scripts/check_profile_status_consistency.py` before any profile status change so a profile file cannot outrun the current transition evidence or claim `DEPRECATED` without a recorded deprecation review.
- Run `scripts/check_discovery_packet_consistency.py` after refreshing registries so the discovery, unresolved, bridge, readiness, transition, deprecation, and rollback-readiness packets cannot silently drift away from the live profile files.

## 8. Monitoring After Release

After any future profile enablement, review:

- quarantine count and reasons
- header-hash mismatch frequency
- duplicate-prevention behavior
- REVIEW_REQUIRED or blocked canonical-record trends
- any sign that a new export revision is producing unexpected field gaps

If a new header hash appears unexpectedly, stop release expansion and re-enter profiling.

## 9. Rollback Procedure

Rollback must be configuration-first:

1. Identify the last approved DU profile version and approved header hash set.
2. Revert the active profile state to the last approved version in source control.
3. Re-run profile loading, canonical validation checks, and repository regression tests.
4. Confirm that the rollback profile still matches the intended source export identity.
5. Review [MW_DU_Profile_Rollback_Readiness.md](/C:/dev/create-pr-cd/docs/MW_DU_Profile_Rollback_Readiness.md) before execution; if the target profile is still `ROLLBACK_BLOCKED`, stop and collect the missing approval evidence instead of forcing a rollback.
5. Continue quarantining records that only match the superseded or changed header revision.
6. Record the rollback reason, date, and restoring approver in the release notes.
7. If the superseded profile remains in repository history, record its successor, rollback target, and superseded header hashes in the deprecation review before claiming `DEPRECATED`.

Do not:

- silently keep processing with an unapproved new header hash
- backfill approval by editing discovery artifacts alone
- bypass the guard by forcing canonical records straight into the generator

## 10. Current Limits

The current repository still does not prove:

- golden parity for TX Mini canonical-path generation
- approved production mappings for TX Mini, MW EOS Swap, or ZTE TX MINI
- UAT completion for any newly profiled MW DU model
- production release authorization for the discovery-only DRAFT profiles

This runbook is therefore a safe operating procedure for continued rollout preparation, not a declaration that the rollout is complete.
