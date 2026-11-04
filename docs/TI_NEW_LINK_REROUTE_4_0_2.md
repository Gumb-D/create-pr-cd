# TI New Link / Reroute production split — v4.0.2

## Approval and boundary

User approved this production rule: (1) clear new-link-only requires installation evidence and no dismantling item; (2) actual reroute requires installation plus old-antenna dismantling evidence; (3) an unclear combined label remains REVIEW_REQUIRED. This is not blanket review bypass or approval of missing source mappings. TSS selection and Jendela's already-separated MW New Link migration work item retain their existing routing.

## Deterministic classification

- Explicit MW New Link / MW New Link Only selects the new-link path unless approved evidence contradicts it.
- Explicit MW Reroute, or approved positive MW/antenna dismantle scope, selects reroute.
- Combined MW New Link / Reroute alone is unresolved. New antenna sizes, NLOS alone, a repeated dropdown label or lack of dismantle text do not establish new-link-only.
- Approved explicit new-link-only / no-dismantling evidence can resolve the combined label. Negated, uncertain or contradictory scope remains review-required.
- Canonical rows consume only APPROVED scope/detail/direct evidence. The renderer now carries TX Upgrade Scope mapping status across the workbook boundary. Legacy direct renderer callers keep their existing input trust boundary; they do not silently approve canonical source mappings.

## Model/evidence gates

- Installation uses the existing governed resolver; incomplete endpoint evidence is not sufficient. NLOS may resolve governed installation size to 0.3 m, not an unknown old/dismantled antenna.
- Actual reroute requires explicit old/dismantle antenna diameter AND an unambiguous 2 or 4 antenna count. New config sizes, retained/reused gear, cable lengths or an NLOS label do not supply old diameter/count. Unsupported/complex phrasing remains review rather than guessed.
- New-link selects one approved inbound transportation item plus the appropriate new-MW installation item from the packaged model. Reroute adds return transportation plus dismantling selected with old size/count. No PR-model workbook or PBOM quantity is modified.
- A missing/ambiguous mandatory selection produces zero ECC rows for this record; a migration decision failure also removes its linked work-item rows. No partial installation is delivered while old dismantling is unresolved.
- New reasons: MW_LINK_SCOPE_UNRESOLVED and MW_REROUTE_DECOM_ANTENNA_COUNT_UNRESOLVED. Existing size/item reasons remain.
- Existing PR references, profile/header checks, contract/governance and geographic routing remain enforced. Existing historical sites are not automatically rerun or cleared by this release.

## Regression coverage

Tests exercise real packaged model generation (new-link inbound/install; reroute inbound/install/return/dismantle), 2-vs-4 count, old/new distinction, incomplete endpoint, provenance, conflicting/negated scope, unresolved combined/NLOS, no partial ECC, duplicate guard and transport ambiguity. Tests also cover unchanged TSS and migration routes. Test commands/results are recorded in platform release handover; no live iEPMS submission is part of implementation testing.

Sources: scripts/mw_link_scope.py; scripts/pr_helpers.py; scripts/create_pr.py; scripts/generate_tss_pr_ecc.py; tests/test_mw_link_scope.py; tests/test_ti_business_guidance.py.


## Release validation — 2026-11-04

The expanded routing/bridge/entrypoint/safety/model regression selection passed 133 tests (6 subtests); final focused scope/guidance/TSS-reroute regression passed 70 tests (4 subtests), followed by a final targeted run for negated-new-link wording. Platform integrity, generic skill contract and cross-platform fingerprint checks passed.

The full MW suite reported **880 passed, 20 skipped, 5 failed** (380 subtests). All five failures were reproduced on an untouched Git worktree at the prior production pin dc7cb77: Python3.14 long-path test mock keyword compatibility; Windows slash-vs-backslash promotion assertion; Jendela rollback artifact SHA/readiness expectations (three tests). No source/profile artifact or test was modified to hide them. This is not an all-green full-suite claim; failures remain follow-up work.

Preserved evidence on this host: C:/Development/aida-chrome/aida-temp-script/conversation-c-mumi1ss1-kgnh/mw-4.0.2-full-pytest.log and mw-baseline-failure-comparison.log. Baseline Git worktree/archive remain alongside these files. Historical source cases were not rerun into live PR uploads. The user authorized publishing, repinning and deployment of this scoped production change; no automatic external submission is authorized.
