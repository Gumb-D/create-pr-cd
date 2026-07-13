# Jendela TX Migration PR Input Onboarding Design

Date: 2026-07-13  
Issue: #21  
Target profile: `jendela_tx_migration_pr_v1`

## 1. Objective

Promote the existing Jendela TX Migration DU profile from discovery-only `DRAFT` to non-production `PR_INPUT_READY` using approved four-layer header evidence, approved duplicate-prevention fields, and profile-specific fail-closed tests.

This change prepares canonical PR input only. It does not enable production ECC generation.

## 2. Business Decisions

The following decisions are approved for this onboarding:

1. Preserve the existing profile ID `jendela_tx_migration_pr_v1`; do not perform a rename migration.
2. Keep the existing identity:
   - Project: `Malaysia_CelcomDigi_Project`
   - DU Model: `Jendela TX Migration`
   - DU Model ID: `4972593269368006257`
   - Accepted View ID: `4026888666764910245`
3. Approve the observed Header Hash:
   - `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3`
4. Promote the profile lifecycle to `PR_INPUT_READY`, never `PRODUCTION`.
5. Approve only the seven runtime mappings listed in Section 4. All other existing candidates remain optional and `UNVERIFIED` unless separately approved later.
6. Use `normalize_pr_reference_status` for both existing-PR fields.
7. Refresh only directly related tracked governance outputs plus mandatory authoritative consistency updates. Do not include unrelated regenerated drift.

## 3. Profile Metadata Changes

Update `config/du_profiles/jendela_tx_migration_pr_v1.yaml` as follows:

- `profile_version`: `0.2.0`
- `mapping_version`: `approved-2026-07-13-jendela-tx-migration-v1`
- `status`: `PR_INPUT_READY`
- add the observed Header Hash to `approved_header_hashes`
- retain strict Header Hash validation
- retain all current identity fields and accepted View metadata

Update the DU profile identity registry record for `jendela_tx_migration_pr_v1` from `DRAFT` to `PR_INPUT_READY`. No identity or naming-status change is permitted.

## 4. Approved Mapping Set

### 4.1 Site code

Canonical field: `site_code`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `site|fix00012|4972593269368006257|4026888666764910245`
- WBS stage: `Site Basic Info`
- task name: `Site Basic Info`
- display header: `customer site code`

Mapping status: `APPROVED`  
Transforms: `trim`, `uppercase`

### 4.2 TX SOW

Canonical field: `tx_sow_raw`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `docata|ZDCSZ00815532`
- WBS stage: `Planner`
- task name: `Microwave`
- display header: `Tx SOW`

Mapping status: `APPROVED`  
Transforms: `trim`

### 4.3 Region

Canonical field: `region`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `site|region_name`
- WBS stage: `Site Basic Info`
- task name: `Site Basic Info`
- display header: `region`

Mapping status: `APPROVED`  
Transforms: `trim`

### 4.4 TSS subcontractor

Canonical field: `subcontractor_tss`  
Profile `required`: `false`

Four-layer fingerprint:

- field code: `docata|ZDCSZ640307`
- WBS stage: `RPM`
- task name: `SubCon - TSS`
- display header: `SubCon - TSS`

Mapping status: `APPROVED`  
Transforms: `trim`

The profile-level field remains optional because requirement enforcement is scope-specific. The canonical validator must still require this source evidence for TSS scope and reject blank TSS subcontractor values even when TI subcontractor data exists.

### 4.5 TI subcontractor

Canonical field: `subcontractor_ti`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `docata|ZDCSZ640242`
- WBS stage: `RPM`
- task name: `Wireless RAN`
- display header: `SubCon - TI`

Mapping status: `APPROVED`  
Transforms: `trim`

### 4.6 Existing TSS PR status/reference

Canonical field: `existing_tss_pr_status`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `docata|ZDCSZ641766`
- WBS stage: `PR Team`
- task name: `Wireless RAN`
- display header: `Subcon PR - TSS`

Mapping status: `APPROVED`  
Transforms: `normalize_pr_reference_status`

### 4.7 Existing TI PR status/reference

Canonical field: `existing_ti_pr_status`  
Profile `required`: `true`

Four-layer fingerprint:

- field code: `docata|ZDCSZ641765`
- WBS stage: `PR team`
- task name: `Wireless RAN`
- display header: `Subcon PR - TI`

Mapping status: `APPROVED`  
Transforms: `normalize_pr_reference_status`

The WBS-stage casing is part of the exact observed fingerprint and must not be normalized across the two PR fields.

## 5. Optional Fields

Existing optional candidates such as site name, DU code, latitude, longitude, antenna sizes, BOQ configuration, SOW details, and planning subcontractor remain unchanged and `UNVERIFIED`.

No optional mapping may be treated as approved merely because an analogous mapping is approved in another DU profile.

## 6. Data Flow and Runtime Boundary

1. The adapter accepts only the registered Project, DU Model, DU Model ID, View ID, and approved Header Hash.
2. Each approved canonical field resolves through its exact four-layer fingerprint.
3. Existing TSS/TI PR values pass through `normalize_pr_reference_status` for duplicate-prevention decisions.
4. Missing, ambiguous, changed, or unapproved evidence remains quarantined.
5. A valid canonical record may become PR-input ready under this profile.
6. ECC output remains blocked because the profile status is `PR_INPUT_READY`, not `PRODUCTION`.

No generator, ECC template, PR model, SOW registry, or production-output code path changes are required.

## 7. Error Handling and Fail-Closed Rules

The implementation must reject or quarantine at least these cases:

- unknown Project, DU Model, DU Model ID, or View ID;
- Header Hash missing from `approved_header_hashes`;
- changed Header Hash;
- missing approved required source column;
- duplicate or ambiguous matching fingerprints;
- use of an unapproved alternative candidate;
- blank TSS subcontractor for TSS scope;
- blank TI subcontractor for TI scope;
- missing source evidence for either existing-PR field;
- unknown transform;
- any attempt to generate ECC while the profile is not `PRODUCTION`.

## 8. Test Design

### 8.1 Profile loader tests

Add or update tests confirming:

- Jendela loads as `PR_INPUT_READY`;
- the Header Hash is approved;
- all seven runtime mappings are approved;
- both existing-PR mappings use `normalize_pr_reference_status`;
- optional fields remain unverified;
- the profile is not `PRODUCTION`.

### 8.2 Adapter tests

Add a dedicated Jendela adapter test group covering:

- exact resolution of all seven approved mappings;
- source provenance retention;
- blank and nonblank PR-reference normalization;
- changed Header Hash quarantine;
- missing approved source-column quarantine;
- rejected alternative candidate behavior;
- TSS-scope subcontractor enforcement;
- TI-scope subcontractor enforcement;
- `PROFILE_NOT_PRODUCTION` output decision.

### 8.3 Governance tests

Update and verify:

- profile identity registry lifecycle status;
- profile status consistency;
- discovery packet consistency;
- readiness and transition-review artifacts where required;
- no profile reaches `PRODUCTION`.

### 8.4 Full verification

Before merge, run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
python -m compileall -q scripts
git diff --check
```

The working tree must be clean after committing generated authoritative updates.

## 9. Refresh and Diff Policy

Run the repository's standard MW DU discovery/governance refresh path when required by existing tests and consistency guards.

Include only:

- Jendela profile changes;
- Jendela-specific test changes;
- Jendela-related registry and documentation updates;
- authoritative summary/count changes that are strictly required for consistency.

Exclude unrelated regenerated changes for other DU profiles unless a consistency guard proves they are inseparable. Any such inseparable change must be documented explicitly in the PR body.

## 10. Safety Boundary

This onboarding must not:

- rename the existing profile;
- modify another DU profile's mapping or lifecycle status;
- change generator behavior;
- change TX SOW normalization or business rules;
- modify ECC templates or PR models;
- commit raw iEPMS exports or anything under `Info/reference`;
- promote Jendela or any other profile to `PRODUCTION`;
- enable production ECC output;
- infer approval from another DU profile.

## 11. Acceptance Criteria

The work is complete when:

1. `jendela_tx_migration_pr_v1` is `PR_INPUT_READY` with profile version `0.2.0`.
2. The exact observed Header Hash is approved.
3. The seven mappings in Section 4 are the only newly approved runtime mappings.
4. Both existing-PR fields use the established normalization transform.
5. Scope-specific subcontractor validation remains enforced.
6. Changed, missing, ambiguous, and unapproved evidence fails closed.
7. Identity and status registries agree with the profile.
8. All focused and full repository tests pass.
9. No raw customer data is committed.
10. No profile is `PRODUCTION`, and ECC remains blocked.
