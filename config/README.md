# PR Input Configuration

`du_profiles/` contains versioned four-header source profiles. A profile is not a PR rule engine and cannot introduce ECC logic.

Safety rules:

- Fingerprints contain all four iEPMS header layers. Excel column position is inventory-only metadata.
- Every production profile must have approved exact fingerprints and at least one approved Header Hash.
- `DRAFT`, `PROFILED`, and `BUSINESS_VALIDATED` profiles are not ECC-enabled.
- Profiles must never contain browser cookies, tokens, employee numbers, session IDs, or proxy credentials.
- Local iEPMS auth belongs only in the Git-ignored `scripts/api_auth.json` file.

## Current PR Model baseline

`pr_model_baseline.yaml` is the authoritative runtime identity for the single current production PR Model.

It owns:

- current model version;
- production workbook path;
- approved SHA-256;
- fail-closed mismatch policy.

Production keeps only one selectable workbook at `Info/input/pr_model.xlsx`. Historical PR Model versions may remain in Git/document history but must not be selectable runtime baselines.

The official `scripts/create_pr.py` entrypoint validates this baseline before DU processing or ECC rendering. A mismatch returns `PR_MODEL_BASELINE_MISMATCH` and stops execution.

Future candidate workbooks must be compared with `scripts/analyze_pr_model_change.py` and must pass compatibility/regression checks before the baseline is updated. Business-semantic removals, new SOWs, or new mandatory rows require review instead of silent promotion.

`promote_pr_model.py` is the controlled promotion entrypoint. A `COMPATIBLE` candidate still must pass the full regression suite before replacement. A `REVIEW_REQUIRED` candidate additionally requires JSON approval evidence bound to the exact candidate version and SHA-256, covering every reported compatibility reason code and recording at least one business-change reference. Approval evidence never bypasses regression.

Example after the business review issue is completed:

```text
python scripts/promote_pr_model.py candidate.xlsx --version 4.1 --approval path/to/approval.json
```

If compatibility, approval evidence, baseline validation, or regression fails, promotion is blocked/rolled back and the current production baseline remains unchanged.
