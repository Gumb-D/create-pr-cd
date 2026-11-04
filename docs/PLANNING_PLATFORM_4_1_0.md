# Planning task type — MW platform integration v4.1.0

## Contract and scope boundary

MW PR Creator now declares three task types: TSS, TI and **Planning** (internal `PLANNING`). It uses the same `.xlsx` site export and single-site/all-sites controls. `src/main.py` invokes the existing `scripts/create_pr.py --scope PLANNING`; the existing Planning runtime, selector and ECC renderer continue to own all business rules. No Planning PBOM, quantity, subcontractor or source approval rules were invented or changed by this integration.

Existing Planning source mappings and profile approvals remain mandatory. Existing Planning PR references block generation; blank subcontractor receives the engine's approved ignored disposition, unknown subcontractor is reviewed, and missing/unapproved source fields cannot silently fall back to TSS/TI. All supported-profile coverage refers to existing Planning fixtures, not a claim that every arbitrary export format is approved. No source workbook is edited.

Outputs include Planning ECC workbooks, source traceability/domain reports, reconciliation and `CREATE_PR_DELIVERY_PLANNING.zip` with checksums. Cancellation follows the envelope sentinel. Invalid scopes such as BACKOFFICE remain rejected by the platform adapter although the standalone domain CLI has separate Backoffice support.

## Platform integration

Manifest-driven Task Type presents `[TSS] [TI] [Planning]`. Worker-aware scope metadata retains PLANNING for `create-pr-cd` only. Job creation, hydration from retained parameters, Job Detail, history/filtering, safe error/LLM context and retained-input reruns preserve it. Scope badge shows Planning; changing history to another worker clears an incompatible Planning filter.

This does **not** expose Planning in iEPMS PR Upload, RAN or Auditor. Their manifests are unchanged; uploader remains TSS/TI and auditor keeps its own nested TSS/TI generation. Existing legacy scopes remain supported. Creating a Planning ECC is not authorization to upload or submit it to iEPMS.

## Validation and release state (2026-11-04)

Release package: **4.1.0**, based on published v4.0.2 `0e08c63`. This release contains the Planning skill integration; its companion platform release records the new skill gitlink and matching approval fingerprint. Publish the skill before the platform commit. Tests and publication do not restart services: runtime activation and live catalog verification remain pending. No live Planning deployment is claimed.

- Combined Planning/public adapter/TSS/TI/reroute regressions: **117 tests passed, 68 subtests**, including the final unsupported-model identity negative test.
- Frontend unit suite: **101 passed** (Planning form using actual manifest and worker-aware history filter included).
- Backend generic contract: MW Planning accepted and persisted; list/detail/rerun retained scope; uploader Planning rejected; safe scope context checked.
- Engine integrity, normalized fingerprint, concurrent job control, durable queue, generic MW execution, frontend build and 12-route smoke passed.
- Public adapter fixtures exercise eight supported DU profiles, exact Planning PBOM/quantity, source checksums, per-file hashes and archive content; negative cases cover existing PRs, missing/unknown subcontractor, missing source mapping, unsupported model and cancellation.
- This is not a full 900+ test-suite rerun. Previously documented unrelated Windows/Python/rollback baseline failures remain pending. No live iEPMS mutations, tracker writes or Implementation Plan updates occurred.

Sources: skill.json; src/main.py; tests/test_planning_platform_contract.py; existing tests/test_issue_34_planning_*; platform backend/src/utils/prScope.js and scope consumers; frontend Task Type/history/badge tests.
