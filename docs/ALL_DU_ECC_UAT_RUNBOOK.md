# All-DU ECC NON_PRODUCTION_UAT Runbook

## Purpose

Generate controlled TSS and TI ECC verification packs for every registered DU Profile without promoting any profile to `PRODUCTION`.

This workflow is for business verification only. It does not create formal production ECC permission.

## Identity and source-selection rules

The automatic workflow uses these fixed rules:

```text
File discovery identity = iEPMS Project Code + DU Model
DU Profile routing identity = Canonical Project Key + DU Model
View Name / View ID = audit information only
Source selection = latest 14-digit export timestamp in the filename
```

The selected workbook must still pass DU Model ID, approved Header Hash, required four-layer fingerprint, lifecycle, contract, SOW, subcontractor, duplicate, and renderer controls.

The system never falls back to an older export when the latest selected export fails validation.

## Prerequisites

1. Sync the repository `main` branch.
2. Place the current raw four-header iEPMS exports under a controlled local source directory. The standard repository-local location is:

```text
Info\reference\du_exports
```

3. Keep all exports excluded from Git.
4. Copy the manifest template:

```powershell
Copy-Item `
  .\config\all_du_ecc_uat_manifest.template.json `
  .\config\all_du_ecc_uat_manifest.local.json
```

5. Confirm the schema 2.0 source root. A path is resolved relative to the manifest file location.

```json
{
  "schema_version": "2.0",
  "source_roots": [
    "../Info/reference/du_exports"
  ],
  "selection_policy": "LATEST_FILENAME_TIMESTAMP"
}
```

Because the manifest is stored under `config`, the repository-local export directory uses `../Info/reference/du_exports` rather than `Info/reference/du_exports`.

Absolute Windows paths are also supported:

```json
{
  "schema_version": "2.0",
  "source_roots": [
    "C:\\dev\\create-pr-cd\\Info\\reference\\du_exports"
  ],
  "selection_policy": "LATEST_FILENAME_TIMESTAMP"
}
```

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

## Automatic preflight

Before the existing batch engine runs, the public runner:

1. scans every configured source root;
2. parses Project Code, DU Model, View Name, and export timestamp from each `A-...xlsx` filename;
3. maps Project Code to the canonical Project Key;
4. resolves exactly one DU Profile from Project Key + DU Model;
5. groups all matching exports by profile;
6. selects the unique latest filename timestamp;
7. converts the result into the existing internal schema 1.0 batch manifest;
8. runs the proven All-DU UAT engine without duplicating PR/ECC business logic.

The preflight output is:

```text
UAT_SOURCE_RESOLUTION.csv
```

It records selected files, ignored older files, Project identity, DU Model, Profile ID, View Name, timestamp, source path, and any discovery error.

## Output

```text
output\NON_PRODUCTION_UAT\<Run ID>\
├─ UAT_MASTER_MANIFEST.xlsx
├─ UAT_MASTER_SUMMARY.json
├─ UAT_BLOCKED_PROFILES.csv
├─ UAT_SOURCE_RESOLUTION.csv
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
- Unknown Project Codes produce `PROJECT_CODE_UNREGISTERED`.
- Unknown DU Models produce `DU_MODEL_UNREGISTERED`.
- Duplicate Project + DU Model routes produce `DU_PROFILE_IDENTITY_AMBIGUOUS`.
- Two files sharing the latest filename timestamp produce `SOURCE_EXPORT_TIMESTAMP_AMBIGUOUS`.
- Filename Project + DU Model and workbook DU Model ID mismatch produces `SOURCE_FILENAME_WORKBOOK_IDENTITY_MISMATCH`.
- Missing, unknown, or identity-mismatched source exports produce no ECC.
- Header Hash failures produce no ECC and do not trigger fallback to an older file.
- `SM` TSS and TI records are classified `IGNORED` with reason code `PR_NOT_REQUIRED_OUTSOURCED_TO_OTHER_VENDOR`.
- Missing, blank, placeholder, or `UNKNOWN` contract mappings are moved to `REVIEW_REQUIRED` with reason code `CONTRACT_MAPPING_NOT_FOUND`.
- An existing Run ID is never overwritten.
- `celcomdigi_cd_consolidation_2023_pr_v1` is routed deterministically as one DRAFT profile family, preserves both Decom and Rollout layouts, and remains blocked because it has no approved Header Hash and no implemented Backoffice / Operation PR workflow.

## Legacy schema 1.0 replay mode

The runner still accepts the previous explicit profile-to-source manifest for controlled historical replay:

```json
{
  "schema_version": "1.0",
  "profiles": [
    {
      "profile_id": "tx_rollout_2023_pr_v1",
      "source_export": "D:\\Exports\\A-P202202168750_D002-2023 TX Rollout-TX Rollout PR_PO View-20260728172643.xlsx",
      "expected_source_sha256": "optional-pinned-sha256"
    }
  ]
}
```

Schema 1.0 is not the normal operating mode. It is retained for reproducible pinned-source replay and compatibility.

## Business verification

Open `UAT_MASTER_MANIFEST.xlsx` and review each generated ECC row. Set `Verification Status` to one of:

- `PENDING`
- `PASS`
- `FAIL`
- `WAIVED_WITH_ACCEPTED_RISK`

Record findings in `Reviewer Comment`.

A `PASS` or accepted-risk entry is UAT evidence only. Profile promotion to `PRODUCTION` requires a separate, explicit lifecycle decision and change.
