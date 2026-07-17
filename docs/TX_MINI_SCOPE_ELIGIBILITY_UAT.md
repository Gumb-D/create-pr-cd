# TX Mini Scope Eligibility UAT

## Objective
This document outlines the scope eligibility implementation for the TX Mini profile `tx_mini_pr_v1` along with instructions to run the local UAT packet generation. 
The implementation enforces Actual End date checks before candidates are marked for PR creation, preserving the existing non-production boundaries.

## Source Data
- **Approved Export**: `Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx`
- **Source SHA-256**: `81de6ba3673dad406e7824727c5c8492dd06b3ef60d088a6e9d680af6c35f8ab`
- **Approved Header Hash**: `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221`

## Scope Eligibility Fingerprints

### TSS Actual End Date
```json
{
  "field_code": "WP10400|AC0000111560|actual_end_date",
  "wbs_stage": "Survey&Design",
  "task_name": "Physical Survey",
  "display_header": "actual end time"
}
```

### TI Actual End Date
```json
{
  "field_code": "WP11100|AC0000111567|actual_end_date",
  "wbs_stage": "Telecom Installation",
  "task_name": "Equipment Installation",
  "display_header": "actual end time"
}
```

## Classification Rules and Precedence

The scope eligibility rules are enforced via a strictly ordered classification:

1. **REVIEW_REQUIRED**: Invalid or ambiguous scope fingerprint.
2. **REVIEW_REQUIRED**: Canonical record incomplete or required evidence unresolved.
3. **DUPLICATE_BLOCKED**: Corresponding existing PR reference exists.
4. **NO_PR_OR_IGNORED**: Corresponding Actual End Date is blank.
5. **REVIEW_REQUIRED**: Actual End Date cannot be parsed as a valid date.
6. **NO_PR_OR_IGNORED**: Tx SOW normalization is `NO_PR_TRIGGER`.
7. **REVIEW_REQUIRED**: Tx SOW, mapping or business evidence requires review.
8. **UAT_CANDIDATE**: All criteria met and eligible for UAT.

*Note: Scope eligibility acts independently. A TSS completion does not grant TI eligibility and vice versa.*

## Audited Baseline Counts

These counts have been independently verified against the canonical implementation.

### TSS
- **UAT_CANDIDATE**: 12
- **DUPLICATE_BLOCKED**: 1787
- **NO_PR_OR_IGNORED**: 406
- **REVIEW_REQUIRED**: 770

### TI
- **UAT_CANDIDATE**: 0
- **DUPLICATE_BLOCKED**: 1765
- **NO_PR_OR_IGNORED**: 406
- **REVIEW_REQUIRED**: 804

## Local UAT Command

Generate the UAT packet locally to review the candidates:

```powershell
python scripts/build_tx_mini_scope_uat.py `
  --input "Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx" `
  --profile "config/du_profiles/tx_mini_pr_v1.yaml" `
  --scope-config "config/scope_eligibility/tx_mini_pr_v1.json"
```

The output artifacts will be written to `output/tx-mini-scope-eligibility-uat/`.

## Non-Production Boundaries

- The profile `tx_mini_pr_v1` remains securely at `PR_INPUT_READY`.
- The `scope_eligibility` configuration enforces `status: UAT_ONLY`.
- All output candidates generated have `ECC Allowed = False`.
- The production gate continues to block and return `PROFILE_NOT_PRODUCTION`.

## Business Review Requirements

Business UAT is pending. The 12 TSS candidates generated need explicit business sign-off.
The generated workbooks do not automatically bypass the review process.

## Known Limitations and Blockers Before Production

- Completion of the current Business UAT review and sign-off on the generated candidates.
- Profiling lifecycle promotion to `PRODUCTION`.
- Production ECC remains strictly isolated. No automated merging or generator invocation should be initiated during UAT.
