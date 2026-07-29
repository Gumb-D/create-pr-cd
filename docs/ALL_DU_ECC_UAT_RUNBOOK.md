# All-DU ECC NON_PRODUCTION_UAT Runbook

## Purpose

Generate controlled TSS and TI ECC verification packs for every registered DU Profile without promoting any profile to `PRODUCTION`.

This workflow is for business verification only. It does not create formal production ECC permission.

## Prerequisites

1. Sync the repository `main` branch.
2. Obtain the current raw four-header iEPMS export for each DU Profile to be tested.
3. Keep the exports outside Git-tracked folders.
4. Copy the manifest template:

```powershell
Copy-Item `
  .\config\all_du_ecc_uat_manifest.template.json `
  .\config\all_du_ecc_uat_manifest.local.json
```

5. In `all_du_ecc_uat_manifest.local.json`, enter one explicit `source_export` path per profile.

Example:

```json
{
  "profile_id": "tx_rollout_2023_pr_v1",
  "source_export": "D:\\Downloads\\A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260728172643.xlsx"
}
```

An optional `expected_source_sha256` may be added to lock a manifest entry to an approved source file.

## Execute

```powershell
python .\scripts\run_all_du_ecc_uat.py `
  --manifest .\config\all_du_ecc_uat_manifest.local.json `
  --output .\output
```

The command returns:

- exit code `0` only when every eligible profile/scope completed and all generated ECC files reconcile with the manifest;
- exit code `2` when the controlled run completed with blocked profiles or failed scopes;
- exit code `1` for an invalid manifest or fatal batch error.

## Output

```text
output\NON_PRODUCTION_UAT\<Run ID>\
├─ UAT_MASTER_MANIFEST.xlsx
├─ UAT_MASTER_SUMMARY.json
├─ UAT_BLOCKED_PROFILES.csv
└─ <profile_id>\
   ├─ FULL_PACK\
   │  ├─ TSS\
   │  └─ TI\
   └─ REVIEW_PACK\
      ├─ TSS\
      └─ TI\
```

Every generated workbook filename includes:

```text
FULL_PACK or REVIEW_PACK
NON_PRODUCTION_UAT
Run ID
```

## Fail-closed controls

- `DRAFT` profiles produce no ECC.
- Missing, disabled, unknown, or identity-mismatched source exports produce no ECC.
- Header Hash failures produce no ECC.
- `SM` TSS and TI records are classified `IGNORED` with reason code `PR_NOT_REQUIRED_OUTSOURCED_TO_OTHER_VENDOR`.
- Missing, blank, placeholder, or `UNKNOWN` contract mappings are moved to `REVIEW_REQUIRED` with reason code `CONTRACT_MAPPING_NOT_FOUND`.
- A source SHA mismatch produces no ECC.
- An existing Run ID is never overwritten.

## Business verification

Open `UAT_MASTER_MANIFEST.xlsx` and review each generated ECC row. Set `Verification Status` to one of:

- `PENDING`
- `PASS`
- `FAIL`
- `WAIVED_WITH_ACCEPTED_RISK`

Record findings in `Reviewer Comment`.

A `PASS` or accepted-risk entry is UAT evidence only. Profile promotion to `PRODUCTION` requires a separate, explicit lifecycle decision and change.