# PR Model Production History

This file is audit metadata only. Runtime selection is controlled exclusively by `config/pr_model_baseline.yaml`.

| Version | SHA-256 | Production status | Notes |
|---|---|---|---|
| v3.0 | historical | RETIRED | Historical reference only. Must not drive current runtime decisions. |
| v3.2 | historical | RETIRED | Historical reference only. Must not drive current runtime decisions. |
| v4.0 | `d3cc64664fc147f8c560688e41264753592eb0b8cdc513d7ebe2d9b989e8aefd` | CURRENT | Current approved production workbook at `Info/input/pr_model.xlsx`. |
| v4.1 | `6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f` | CANDIDATE / REVIEW_REQUIRED | Supplied 2026-08-10. Compatibility review blocks promotion because current Jendela-specific PR Model rows are removed. See Issue #77. |

## Operating standard

1. Production keeps exactly one current workbook at `Info/input/pr_model.xlsx`.
2. A candidate never replaces the current workbook before compatibility and regression gates pass.
3. Historical workbooks are not retained as selectable runtime assets; Git history is the historical source.
4. SHA-256 is calculated from workbook bytes and recorded in the authoritative baseline config.
5. A mismatch fails closed with `PR_MODEL_BASELINE_MISMATCH`.
6. Automated compatibility/regression is the default validation method.
7. Human review is required only when the candidate introduces, removes, or changes business meaning that cannot be safely resolved by existing approved rules.
