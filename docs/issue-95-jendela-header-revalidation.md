# Issue #95 — Jendela Header Revalidation Evidence

Date: 2026-08-12

## Classification

The 2026-08-11 runtime export is classified as an **incorrect/different iEPMS View for the current production Jendela PR profile**, not as a legitimate replacement structure to approve.

No new production header hash is approved by this issue.

## Approved production baseline

- Profile: `jendela_tx_migration_pr_v1`
- Profile version: `0.5.0`
- Approved View ID embedded in the approved site-code fingerprint: `4026888666764910245`
- Approved raw header hash: `f45c209df5ca75b333f9b590ebc01c05c097e44231d22433290f8078e57c9056`
- Header policy: `strict`

The approved profiler artifact contains 209 authoritative `data` columns and includes the TI-critical fingerprints for Customer Site Code, Tx SOW, TX Before Migration, MW Config, Region, Province/State, SubCon - TI, and Subcon PR - TI.

## 2026-08-11 runtime export

Input: `A-P202202168750_D002-Jendela TX Migration-Migration Rollout-20260811085443.xlsx`

- Runtime site-code View ID: `6638925130999114751`
- Raw header hash: `af03e909ff0476a91396efd0f4d735ed85a2af37b1c308bf5849d38d7e629149`
- Structural header hash: `f9a30138c3d7ac088ad19d73aac66cf64d7dda7b337b8da48bebb52b1ae02e9f`
- Governance result: `UNAPPROVED_STRUCTURE`
- Authoritative `data` columns: 50

## TI-critical mapping comparison

| Canonical field | Approved production fingerprint | 2026-08-11 export | Result |
|---|---|---|---|
| Customer Site Code | Site Basic Info / Site Basic Info / `customer site code`, View `4026888666764910245` | Same stable site field but View `6638925130999114751` | Different View evidence |
| Tx SOW | Planner / Microwave / `Tx SOW` / `docata|ZDCSZ00815532` | Not present | Blocking difference |
| TX Before Migration | Installation / Wireless RAN / `TX Before Migration` / `docata|ZDCSZ01016454` | Exact match | Compatible field |
| MW Config (before-MW evidence) | Installation / Wireless RAN / `MW Config` / `docata|ZDCSZ01022277` | Exact match | Compatible field |
| Region | Site Basic Info / Site Basic Info / `region` / `site|region_name` | Exact match | Compatible field |
| Province/State | Site Basic Info / Site Basic Info / `Province/State` / `site|fix00008` | Not present | Blocking difference |
| SubCon - TI | RPM / Wireless RAN / `SubCon - TI` / `docata|ZDCSZ640242` | Installation / Wireless RAN with same field code/display header | Semantic/WBS drift; not exact approved fingerprint |
| Subcon PR - TI | PR team / Wireless RAN / `Subcon PR - TI` / `docata|ZDCSZ641765` | Installation / Wireless RAN with same field code/display header | Semantic/WBS drift; not exact approved fingerprint |

## Decision

The runtime file is not the approved Jendela PR export shape. It omits PR-critical business fields and changes the WBS identity of duplicate-prevention/subcontractor fields. Therefore:

1. `af03e909ff0476a91396efd0f4d735ed85a2af37b1c308bf5849d38d7e629149` must **not** be added to `approved_header_hashes`.
2. `header_hash_policy: strict` remains unchanged.
3. The runtime export must continue to fail closed with `HEADER_HASH_REVALIDATION_REQUIRED`.
4. The only software change in Issue #95 is to preserve that governed error through the standard Skill result contract using a safe detail allow-list.

## Rollback protection

The existing production profile/header approval remains untouched. Reverting the Skill-contract allow-list change restores the previous public error-envelope behavior without changing Jendela header acceptance or PR business logic.
