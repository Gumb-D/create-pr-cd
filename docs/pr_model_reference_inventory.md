# PR Model Reference Inventory — Issue #75 / Issue #77

This inventory classifies PR Model version/path/hash references audited for Issue #75 and records the Issue #77 v4.1 promotion outcome. It is governance evidence, not a runtime selector.

| Location / Reference | Classification | Runtime impact | Required handling |
|---|---|---|---|
| `Info/input/pr_model.xlsx` | `RUNTIME_BINDING` | Critical | The only current production workbook. Identity is governed by `config/pr_model_baseline.yaml`. |
| `config/pr_model_baseline.yaml` | `VALIDATION_BINDING` | Critical | Authoritative current version/path/SHA and fail-closed policy. |
| `scripts/create_pr.py` | `RUNTIME_BINDING` | Critical | Must validate the authoritative baseline before engine/renderer execution. |
| `scripts/generate_tss_pr_ecc.py` approved SHA constant | `VALIDATION_BINDING` legacy mirror | High | Transitional renderer mirror; drift test must equal the authoritative baseline. It is not allowed to define a different baseline. |
| `scripts/run_tx_mini_ecc_parity.py` approved SHA constant | `TEST_BASELINE` legacy mirror | Medium | Transitional parity mirror; drift test must equal the authoritative baseline. |
| `tests/test_jendela_approved_pr_model.py` approved SHA assertion | `TEST_BASELINE` | Test only | Tracks the exact current production PR Model used by the Jendela renderer regression. |
| `docs/MW_DU_PR_Extension_Architecture_and_Implementation_Plan.md` examples `tx_pr_model_v3_0.yaml` / `tx_pr_model_v3_2.yaml` | `HISTORICAL_DOCUMENTATION` | None | Historical architecture examples only. They must not be treated as current production profiles or runtime selectors. |
| Historical workbook names containing `v3.0` / `v3.2` | `HISTORICAL_DOCUMENTATION` | None | Retained only where needed for audit/history; never selected by runtime. |
| `docs/pr_model_history.md` | `HISTORICAL_DOCUMENTATION` | None | Records retired/current identities without making historical models selectable. |
| `config/registries/canonical_sow_registry.yaml` current-model evidence text | `VALIDATION_BINDING` business evidence | Indirect | May describe current model evidence but must not own version/path/SHA selection; its current-model wording must track the authoritative baseline. |

## Current production invariant

```text
config/pr_model_baseline.yaml
        ↓
version = 4.1
path = Info/input/pr_model.xlsx
sha256 = 6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f
        ↓
scripts/create_pr.py validates before execution
```

Any mismatch fails closed with `PR_MODEL_BASELINE_MISMATCH`.

## v4.1 production status

PR Model v4.1 was promoted on 2026-08-10 after Issue #77 redesigned/revalidated Jendela TX Migration against the candidate and the official promotion gate passed.

Exact production SHA-256:

```text
6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f
```

Reviewed compatibility reason codes were `REMOVED_BUSINESS_ROWS`, `NEW_SOW`, and `ADDED_MANDATORY_ROWS`. Approval evidence is stored in `config/pr_model_approvals/issue_77_v4_1.json` and is bound to the exact version/SHA above. The temporary candidate copy was retired after promotion; `Info/input/pr_model.xlsx` is the sole runtime workbook and Git history is the historical source.

The approval did not bypass regression. `promote_pr_model.py` accepted the exact-SHA approval, replaced the authoritative baseline, synchronized its validation mirrors, and passed its rollback-protected full regression gate before the promotion was retained.

## Historical isolation rule

Historical version strings such as `v3.0`, `v3.2`, or retired v4.0 evidence are not bulk-replaced. Their classification determines handling. Historical documents remain historical; active runtime/validation bindings and current-model evidence must resolve or describe the single current baseline.
