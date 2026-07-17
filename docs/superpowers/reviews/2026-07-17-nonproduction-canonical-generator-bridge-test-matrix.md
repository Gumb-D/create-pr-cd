# Bridge Verification Matrix

| Scenario | Expected result |
|---|---|
| Canonical record ready, SOW approved, scope PR status `NO_PR` | `UAT_CANDIDATE` |
| Scope PR status `PR_EXISTS` | `DUPLICATE_BLOCKED` |
| Scope PR status `NO_PR_REQUIRED` | `NO_PR_REQUIRED` |
| Canonical record incomplete or quarantined | `REVIEW_REQUIRED` |
| SOW normalization missing or unapproved | `REVIEW_REQUIRED` |
| Header Hash differs from approved profile | execution stops with `HEADER_HASH_REVALIDATION_REQUIRED` |
| Required mapping missing or ambiguous | execution stops before packet creation |
| Profile below `PR_INPUT_READY` | execution stops |
| Any emitted row | `ECC Allowed = false` |
| Customer export absent in clean clone | synthetic tests remain portable |
