# Non-Production Canonical-to-Generator Bridge

The bridge converts an approved four-header iEPMS export into a local-only UAT workbook compatible with the existing generator input contract.

For standard iEPMS export filenames, the bridge automatically selects the DU Profile using:

```text
Project Code -> Canonical Project Key
Canonical Project Key + DU Model -> DU Profile
```

View Name and View ID are retained for traceability but do not select the profile. The selected workbook must still pass DU Model ID, approved Header Hash, required four-layer fingerprint, lifecycle, and canonical safety validation.

It does not import, invoke, or enable the ECC generator. Every output row contains:

```text
ECC Allowed = false
```

## ZTE TX MINI example

```powershell
python scripts\canonical_generator_bridge.py `
  --input "Info\reference\du_exports\A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx" `
  --scope TSS `
  --sow-registry "config\registries\canonical_sow_registry.yaml" `
  --output "output\canonical_generator_uat\zte_tx_mini\tss"

python scripts\canonical_generator_bridge.py `
  --input "Info\reference\du_exports\A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx" `
  --scope TI `
  --sow-registry "config\registries\canonical_sow_registry.yaml" `
  --output "output\canonical_generator_uat\zte_tx_mini\ti"
```

## Optional profile assertion

`--profile` remains available for controlled replay or operator verification, but it cannot override automatic routing:

```powershell
python scripts\canonical_generator_bridge.py `
  --input "Info\reference\du_exports\A-P202211283695_D002-ZTE TX MINI-ZTE TX MINI v1-20260703160312.xlsx" `
  --profile "config\du_profiles\zte_tx_mini_pr_v1.yaml" `
  --scope TSS `
  --sow-registry "config\registries\canonical_sow_registry.yaml" `
  --output "output\canonical_generator_uat\zte_tx_mini\tss"
```

When the asserted profile differs from the automatically resolved profile, execution fails with:

```text
DU_PROFILE_IDENTITY_MISMATCH
```

## Workbook sheets

- `data` — direct generator-compatible sheet. Rows 1–3 are UAT notices, row 4 contains the exact legacy Header names, and only `UAT_CANDIDATE` records are included.
- `summary`
- `uat_candidates`
- `duplicate_blocked`
- `no_pr_required`
- `review_required`
- `traceability`

The current generator can read the bridge workbook through its existing `sheet_name='data', header=3` contract. The bridge itself never invokes the generator.

## Safety behavior

- Profile selection uses Project + DU Model for standard iEPMS filenames.
- View identity cannot reroute a standard iEPMS export.
- Filename identity and workbook DU Model ID must agree.
- Strict approved Header Hash.
- Exact four-layer fingerprint mappings only.
- `PR_INPUT_READY` or `PRODUCTION` profile required for bridge execution.
- Missing or ambiguous approved required mappings stop execution.
- Canonical validation and SOW normalization remain fail-closed.
- Existing PR references are separated into `duplicate_blocked` and excluded from `data`.
- `NO_PR_REQUIRED` records are separated and excluded from `data`.
- No ECC file is generated.
