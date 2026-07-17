# Non-Production Canonical-to-Generator Bridge

The bridge converts an approved four-header iEPMS export into a local-only UAT workbook compatible with the existing generator input column contract.

It does not import, invoke, or enable the ECC generator. Every output row contains:

```text
ECC Allowed = false
```

## ZTE TX MINI example

```powershell
python scripts\canonical_generator_bridge.py `
  --input "Info\reference\du_exports\A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx" `
  --profile "config\du_profiles\zte_tx_mini_pr_v1.yaml" `
  --scope TSS `
  --sow-registry "config\registries\canonical_sow_registry.yaml" `
  --output "output\canonical_generator_uat\zte_tx_mini\tss"

python scripts\canonical_generator_bridge.py `
  --input "Info\reference\du_exports\A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx" `
  --profile "config\du_profiles\zte_tx_mini_pr_v1.yaml" `
  --scope TI `
  --sow-registry "config\registries\canonical_sow_registry.yaml" `
  --output "output\canonical_generator_uat\zte_tx_mini\ti"
```

## Workbook sheets

- `summary`
- `generator_input`
- `uat_candidates`
- `duplicate_blocked`
- `no_pr_required`
- `review_required`
- `traceability`

## Safety behavior

- Strict approved Header Hash.
- Exact four-layer fingerprint mappings only.
- `PR_INPUT_READY` or `PRODUCTION` profile required for bridge execution.
- Missing or ambiguous approved required mappings stop execution.
- Canonical validation and SOW normalization remain fail-closed.
- Existing PR references are separated into `duplicate_blocked`.
- `NO_PR_REQUIRED` records are separated from candidates.
- No ECC file is generated.
