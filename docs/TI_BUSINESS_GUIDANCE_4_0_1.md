# TI business guidance - v4.0.1

## Scope and baseline

Fix branch starts at MW skill main `237ee81`, retaining the newer Backoffice work.
Platform remains on its existing XLS/XLSX uploader branch. No live iEPMS records,
tracker workbooks, PR Model workbook, unrelated skills, or account state changed.

## PostMOCN

PostMOCN is not introduced as a Tx SOW or aliased to another SOW. Existing
`Post MOCN TX SOW (LLD)` column fingerprint/precedence remains unchanged.
Terminal site-ID aliases `_POSTMOCN`, `_Post MOCN`, `_POST-MOCN`, `_Post_MOCN`
(and `-` separator) render as `_POSTMOCN`. A trailing instance number remains:
`S1_Post MOCN_2` -> `S1_POSTMOCN2`, NOT `S1_POSTMOCN`.
Source Project + Site Code stays unchanged and renderer reconciliation records
both source and rendered codes. Unknown suffixes remain untouched; colliding
source IDs fail closed with `RENDERED_SITE_ID_COLLISION`.
Planning/Backoffice selection is not intentionally renamed.

## Starlink

Only the approved Starlink dismantle work item (`Starlink Dismanle`, spelling
retained from approved model) is explicitly MW-antenna NOT_APPLICABLE.
Its fixed items remain loaded from the approved model. A separate MW new-link,
swap or dismantle component still requires MW antenna evidence. Existing atomic
migration handling prevents delivery of only the Starlink component when MW fails.
No new `New Starlink` or mixed-scope SOW/model alias is invented.

## NLOS

Issue #50 Human UAT Batch 2 / #80 already approve deterministic NLOS evidence
from BOQ Configuration / TX SOW Details. Canonical production rows require an
APPROVED mapping. Existing TX Rollout TX/NE/FE SOW Details fingerprints now carry
that approval; no direct antenna or missing BOQ column mapping is invented, no
header gate relaxed, no profile lifecycle promotion. Profile version is 0.1.2.

Approved NLOS resolves installation and reroute dismantle antenna size to 0.3 m.
No site-name inference, substring lookalike, or universal missing-size fallback.
Explicit contradictory/invalid values or negated/uncertain NLOS evidence produce
`NLOS_ANTENNA_EVIDENCE_CONFLICT` rather than overwriting source data.
Selected size and source provenance appear in the resolver and runtime logs.

The approved reroute dismantle model separately distinguishes 2 and 4 antennas.
Size 0.3 m alone cannot select between them: unresolved count continues to produce
`MW_REROUTE_DISMANTLE_ITEM_NOT_MATCHED`. This patch does not claim to solve the
entire reroute scope/count decision or every seven-site report. No PBOM guessed.

## Validation

New offline tests cover suffix identity/collision, approved/unapproved NLOS,
positive and negative/conflicting evidence, exact TX Rollout wiring, real model
MW Swap and Starlink generation, reroute size resolution, and mixed migration
atomicity. Source workbooks for the seven reported cases are still unavailable.
Full-suite and platform validation logs are kept in the AIDA conversation folder.
Five full-suite failures reproduce on unchanged `237ee81`: Windows long-path
mock signature, Windows path separators, and immutable rollback Git object/tree
identity. These unrelated failures are not silently fixed by this change.

### Final validation on this Windows machine

- Full MW suite: 858 passed, 20 skipped, 380 subtests passed, 5 pre-existing failures.
- The same five failing test names were reproduced in a detached `237ee81` checkout.
- TX Rollout discovery consistency, historical header acceptance, and profile traceability pass after synchronizing only the affected version metadata.
- Platform fingerprint normalization, generic skill catalog/submission/result contracts, and offline Python job runner pass.
- Seven reported production site workbooks have not been replayed; no live PR submitted.


## Superseded reroute behavior in v4.0.2

The earlier NLOS-to-reroute-dismantle-size behavior above is historical. v4.0.2 requires explicit old-antenna size and count for actual reroutes; NLOS remains governed installation evidence only. See [production split](TI_NEW_LINK_REROUTE_4_0_2.md). No historical PR was automatically rerun.
