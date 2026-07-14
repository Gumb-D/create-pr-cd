# MW DU All-DU Discovery Mapping Review

Discovery-only summary for the all-MW-DU mapping recommendation matrix generated for Issue `#19`.

- Export count: `10`
- Matrix rows: `180`

## Group Summary

### Structurally different but PR-critical fields appear present

- DU models: 2023 Celcomdigi BAU
- Reference files: A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx
- PR-critical blockers: subcontractor_planning
- Recommended next sequence: Start with the highest-confidence rows in this group, then review ambiguous PR-critical fields before any profile implementation.

### Duplicate or competing export variants

- DU models: CD consolidation 2023
- Reference files: A-P202202168750_D002-CD consolidation 2023-CD 2023 Decom Site-20260703160415.xlsx, A-P202202168750_D002-CD consolidation 2023-CD consolidation 2023 Rollout-20260703160351.xlsx
- PR-critical blockers: existing_ti_pr_status, existing_tss_pr_status, region, site_code, site_name, tx_sow_raw
- Recommended next sequence: Start with the highest-confidence rows in this group, then review ambiguous PR-critical fields before any profile implementation.

### Same or highly similar to TX Mini

- DU models: 2023 TX Rollout, 2024 Celcomdigi BAU, Celcomdigi USP, Jendela TX Migration, TX Mini Project
- Reference files: A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260703160446.xlsx, A-P202202168750_D002-2024 Celcomdigi BAU-2024 BAU Rollout (TX)-20260703160253.xlsx, A-P202202168750_D002-Celcomdigi USP-Celcomdigi USP (TX)-20260703160234.xlsx, A-P202202168750_D002-Jendela TX Migration-Migration Rollout (TX)-20260703160246.xlsx, A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx
- PR-critical blockers: site_name, subcontractor_planning
- Recommended next sequence: Start with the highest-confidence rows in this group, then review ambiguous PR-critical fields before any profile implementation.

### Similar to MW EOS Swap

- DU models: MW EOS Swap, ZTE TX MINI
- Reference files: A-P202211283695_D002-MW EOS Swap-MW EOS Swap Rollout-20260703160307.xlsx, A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx
- PR-critical blockers: site_code, site_name, subcontractor_planning, tx_sow_raw
- Recommended next sequence: Start with the highest-confidence rows in this group, then review ambiguous PR-critical fields before any profile implementation.

## Export Summary

| DU model | Group | High | Medium | Low | Missing | Ambiguous |
|---|---|---:|---:|---:|---:|---:|
| 2023 Celcomdigi BAU | Structurally different but PR-critical fields appear present | 0 | 0 | 8 | 1 | 9 |
| 2023 TX Rollout | Same or highly similar to TX Mini | 1 | 0 | 7 | 3 | 7 |
| 2024 Celcomdigi BAU | Same or highly similar to TX Mini | 0 | 0 | 9 | 0 | 9 |
| CD consolidation 2023 | Duplicate or competing export variants | 0 | 0 | 5 | 4 | 9 |
| CD consolidation 2023 | Duplicate or competing export variants | 0 | 0 | 3 | 8 | 7 |
| Celcomdigi USP | Same or highly similar to TX Mini | 0 | 0 | 7 | 0 | 11 |
| Jendela TX Migration | Same or highly similar to TX Mini | 0 | 0 | 7 | 2 | 9 |
| TX Mini Project | Same or highly similar to TX Mini | 8 | 0 | 2 | 0 | 8 |
| MW EOS Swap | Similar to MW EOS Swap | 1 | 0 | 7 | 1 | 9 |
| ZTE TX MINI | Similar to MW EOS Swap | 0 | 1 | 7 | 1 | 9 |

## Safety Notes

- This report is sanitized and metadata-only. It includes no raw customer rows or site lists.
- The full row-level matrix is written to ignored local `output/` artifacts for human review.
- No mapping approval, lifecycle promotion, or ECC enablement is performed by this artifact.
