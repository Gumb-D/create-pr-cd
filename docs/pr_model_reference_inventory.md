# PR Model Reference Inventory — Issue #75

This inventory classifies PR Model version/path/hash references audited for Issue #75. It is governance evidence, not a runtime selector.

| Location / Reference | Classification | Runtime impact | Required handling |
|---|---|---|---|
| `Info/input/pr_model.xlsx` | `RUNTIME_BINDING` | Critical | The only current production workbook. Identity is governed by `config/pr_model_baseline.yaml`. |
| `config/pr_model_baseline.yaml` | `VALIDATION_BINDING` | Critical | Authoritative current version/path/SHA and fail-closed policy. |
| `scripts/create_pr.py` | `RUNTIME_BINDING` | Critical | Must validate the authoritative baseline before engine/renderer execution. |
| `scripts/generate_tss_pr_ecc.py` approved SHA constant | `VALIDATION_BINDING` legacy mirror | High | Transitional renderer mirror; drift test must equal the authoritative baseline. It is not allowed to define a different baseline. |
| `scripts/run_tx_mini_ecc_parity.py` approved SHA constant | `TEST_BASELINE` legacy mirror | Medium | Transitional parity mirror; drift test must equal the authoritative baseline. |
| `tests/test_jendela_approved_pr_model.py` v4 SHA assertion | `TEST_BASELINE` | Test only | Existing Jendela regression remains unchanged by Issue #75. Jendela redesign belongs to Issue #77. |
| `docs/MW_DU_PR_Extension_Architecture_and_Implementation_Plan.md` examples `tx_pr_model_v3_0.yaml` / `tx_pr_model_v3_2.yaml` | `HISTORICAL_DOCUMENTATION` | None | Historical architecture examples only. They must not be treated as current production profiles or runtime selectors. |
| Historical workbook names containing `v3.0` / `v3.2` | `HISTORICAL_DOCUMENTATION` | None | Retained only where needed for audit/history; never selected by runtime. |
| `docs/pr_model_history.md` | `HISTORICAL_DOCUMENTATION` | None | Records retired/current/candidate identities without making historical models selectable. |
| `config/registries/canonical_sow_registry.yaml` current-v4 evidence text | `VALIDATION_BINDING` business evidence | Indirect | May describe current model evidence but must not own version/path/SHA selection. |

## Current production invariant

```text
config/pr_model_baseline.yaml
        ↓
version = 4.0
path = Info/input/pr_model.xlsx
sha256 = d3cc64664fc147f8c560688e41264753592eb0b8cdc513d7ebe2d9b989e8aefd
        ↓
scripts/create_pr.py validates before execution
```

Any mismatch fails closed with `PR_MODEL_BASELINE_MISMATCH`.

## v4.1 candidate status

Candidate SHA-256:

```text
6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f
```

Issue #75 does **not** promote v4.1. The candidate removes business rows that the current Jendela implementation depends on, so it remains `REVIEW_REQUIRED` until Issue #77 redesigns/revalidates Jendela against the new model.

After #77 is complete, reviewed compatibility changes may be unlocked only with explicit JSON promotion approval evidence that matches the exact candidate version and SHA above, covers every analyzer reason code, and records at least one business-change reference. The approval does not change runtime selection and cannot bypass the full regression gate. Only after that evidence and regression pass may `promote_pr_model.py` replace the current production baseline.

## Historical isolation rule

Historical version strings such as `v3.0` or `v3.2` are not bulk-replaced. Their classification determines handling. Historical documents remain historical; active runtime/validation bindings must always resolve the single current baseline.
