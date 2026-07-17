# TX Mini Scope Eligibility UAT

## Objective
This document outlines the scope eligibility implementation for the TX Mini profile `tx_mini_pr_v1` along with instructions to run the local UAT packet generation. 
The implementation enforces Actual End date checks before candidates are marked for PR creation, preserving the existing non-production boundaries.

## Final Scope Configuration
The definitive Actual End Date fingerprints used for eligibility checking are:
- TSS: `WP10400|AC0000111560|actual_end_date` (Survey&Design / Physical Survey)
- TI: `WP11100|AC0000111567|actual_end_date` (Telecom Installation / Equipment Installation)

## Precedence Rules
The final evaluation precedence is:
1. Invalid global scope configuration ? Fail the run.
2. Existing scope-specific PR ? `DUPLICATE_BLOCKED`.
3. Scope Actual End blank ? `NO_PR_OR_IGNORED`.
4. Scope Actual End malformed ? `REVIEW_REQUIRED`.
5. Approved `NO_PR_TRIGGER` SOW ? `NO_PR_OR_IGNORED`.
6. Completed scope with incomplete candidate-required evidence ? `REVIEW_REQUIRED`.
7. Completed scope with unverified SOW/mapping ? `REVIEW_REQUIRED`.
8. Otherwise ? `UAT_CANDIDATE`.

## Final Verified Classification Counts

### TSS
- UAT_CANDIDATE: 12
- DUPLICATE_BLOCKED: 1794
- NO_PR_OR_IGNORED: 1168
- REVIEW_REQUIRED: 1
- TOTAL: 2975

### TI
- UAT_CANDIDATE: 0
- DUPLICATE_BLOCKED: 1765
- NO_PR_OR_IGNORED: 1208
- REVIEW_REQUIRED: 2
- TOTAL: 2975

## How to generate the UAT Packet
To generate the latest UAT packet:
`python scripts/build_tx_mini_scope_uat.py --input "Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx" --profile config/du_profiles/tx_mini_pr_v1.yaml --scope-config config/scope_eligibility/tx_mini_pr_v1.json --output output/tx-mini-scope-eligibility-uat`

