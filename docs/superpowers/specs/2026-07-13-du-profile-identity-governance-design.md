# DU Profile Identity Governance Design

**Issue:** #28  
**Repository:** `Gumb-D/create-pr-cd`  
**Date:** 2026-07-13  
**Status:** Pending user review

## 1. Objective

Standardize MW DU profile identity so that profiles follow the iEPMS business hierarchy rather than export-view naming.

```text
DU Profile Identity = iEPMS Project + DU Model
```

The export View is evidence and layout metadata. It is not the business identity unless it represents a genuinely different business process or incompatible PR logic.

## 2. Selected Approach

Use a governance package consisting of:

1. a human-readable naming standard;
2. a machine-readable identity registry;
3. automated tests that detect duplicate or nonstandard profile identities.

This is preferred over documentation-only governance because future onboarding work under Issue #21 must be protected from repeated naming drift.

## 3. Scope

### Included

- Define the standard profile ID format.
- Register the identity of every existing DU profile.
- Preserve all approved profile IDs without renaming.
- Mark accepted legacy names explicitly.
- Detect multiple profile IDs for the same Project + DU Model identity.
- Allow an explicit exception only when the registry records a business justification and an exact permitted profile set.
- Flag the two `CD consolidation 2023` DRAFT profiles for consolidation review.

### Excluded

- Renaming existing profiles.
- Merging or deleting the CD Consolidation profiles.
- Changing profile lifecycle status.
- Promoting any profile to `PRODUCTION`.
- Enabling ECC output.
- Changing DU mapping fingerprints, Header Hash evidence, or PR business rules.

## 4. Identity Model

The canonical identity key is:

```text
(project_key, du_model_id)
```

`du_model_name` is retained as readable evidence but is not the sole unique key because names may be edited while the iEPMS model ID remains stable.

Each profile registry record contains:

```yaml
profile_id: <current profile ID>
canonical_profile_id: <standard ID for this profile family>
project_key: <registered project key>
project_slug: <controlled project slug>
du_model_name: <iEPMS DU model name>
du_model_id: <iEPMS DU model ID>
identity_key: <project_key>::<du_model_id>
name_status: STANDARD | LEGACY_ACCEPTED | CONSOLIDATION_REVIEW_REQUIRED
accepted_view_ids: []
exception:
  allowed: false
  reason: null
```

The registry also contains exact duplicate-identity review records:

```yaml
identity_reviews:
  - identity_key: <project_key>::<du_model_id>
    status: CONSOLIDATION_REVIEW_REQUIRED
    permitted_profile_ids:
      - <existing profile A>
      - <existing profile B>
    reason: <business and technical review required>
```

A third profile for the same identity fails governance unless the permitted set is deliberately updated with justification.

## 5. Naming Standard

New profile families should use:

```text
<project_slug>_<du_model_slug>_pr_v<major>
```

Rules:

- Use lowercase snake case.
- Use the registry-controlled project slug and normalized DU model slug.
- Do not derive the profile ID from the export View label or View ID.
- Use `_pr_v<major>` for the profile family version suffix.
- Create a separate profile only for a different Project, different DU Model, materially different PR logic, materially different field semantics, or source layouts that cannot be validated safely within one profile family.
- New profiles must equal the registry `canonical_profile_id` unless an explicit exception is approved.

This avoids unreliable keyword guessing: machine enforcement compares the actual ID with a declared canonical ID rather than trying to infer whether a token came from a View name.

## 6. Existing Profile Decisions

### Legacy accepted

`tx_mini_pr_v1` remains unchanged. It maps to:

```text
Project: Malaysia_CelcomDigi_Project
DU Model: TX Mini Project
```

Its current name predates the standard and is accepted to avoid migration risk.

### Separate identity required

`zte_tx_mini_pr_v1` remains separate from `tx_mini_pr_v1` because it maps to a different Project and a different DU Model:

```text
Project: CelcomDigi_MW
DU Model: ZTE TX MINI
```

Similarity in wording does not make the identities equivalent.

### Existing names retained

The following existing names remain unchanged. The registry records whether each current name is canonical or an accepted legacy name:

- `celcomdigi_bau_2024_pr_v1`
- `celcomdigi_usp_pr_v1`
- `mw_eos_swap_pr_v1`
- `tx_rollout_2023_pr_v1`
- `jendela_tx_migration_pr_v1`

No existing profile is renamed solely to improve naming consistency.

### Consolidation review required

The following DRAFT profiles both map to the same Project + DU Model identity:

- `cd_consolidation_2023_decom_pr_v1`
- `cd_consolidation_2023_rollout_pr_v1`

They remain unchanged in this PR. The identity review permits exactly these two existing profiles and marks them `CONSOLIDATION_REVIEW_REQUIRED` until business and technical evidence proves either:

1. they should become one profile family accepting multiple Views and Header Hashes; or
2. they require separate profiles because the workflows have materially different PR semantics.

## 7. Machine Enforcement

Add a registry at:

```text
config/registries/mw_du_profile_identity_registry.yaml
```

Add a test at:

```text
tests/test_du_profile_identity_governance.py
```

The test must:

1. load every file under `config/du_profiles/`;
2. require a matching registry record for every profile;
3. verify registry identity fields match the profile identity block;
4. group profiles by `(project_key, du_model_id)`;
5. fail when more than one profile exists for the same identity unless an identity review exists and its `permitted_profile_ids` exactly match the current duplicate set;
6. require `profile_id == canonical_profile_id` for `STANDARD` records;
7. require a non-empty reason for every `LEGACY_ACCEPTED` or exception record;
8. verify `tx_mini_pr_v1` is marked `LEGACY_ACCEPTED`;
9. verify `tx_mini_pr_v1` and `zte_tx_mini_pr_v1` have different identity keys;
10. verify the profile lifecycle statuses captured in the registry match the actual profiles.

## 8. View Handling

A profile may accept multiple export Views through existing metadata:

```yaml
identity:
  accepted_view_ids:
    - <view A>
    - <view B>

export_structure:
  approved_header_hashes:
    - <header hash A>
    - <header hash B>
```

Adding a View to a profile still requires approved four-layer Header Fingerprint evidence and Header Hash governance. Identity consolidation does not weaken fail-closed source validation.

## 9. Error Handling

Governance violations must fail tests with actionable messages, including:

- `UNREGISTERED_DU_PROFILE:<profile_id>`
- `PROFILE_IDENTITY_MISMATCH:<profile_id>`
- `DUPLICATE_PROFILE_IDENTITY:<identity_key>`
- `DUPLICATE_IDENTITY_SET_MISMATCH:<identity_key>`
- `NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:<profile_id>`
- `LEGACY_PROFILE_WITHOUT_REASON:<profile_id>`

The governance test does not modify files automatically.

## 10. Validation Strategy

Minimum verification:

```text
python -m unittest tests.test_du_profile_identity_governance -v
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
python -m compileall -q scripts
git diff --check
```

Focused negative fixtures or in-test temporary registry/profile data must prove:

- an unregistered profile fails;
- an unapproved duplicate identity fails;
- a third CD Consolidation profile fails because it is outside the exact permitted set;
- a `STANDARD` record with a noncanonical ID fails;
- a legacy record without a reason fails.

## 11. Delivery Boundary

The implementation PR should contain only:

- `docs/MW_DU_Profile_Naming_Standard.md`
- `config/registries/mw_du_profile_identity_registry.yaml`
- `tests/test_du_profile_identity_governance.py`
- this design and the implementation plan

Additional changes are permitted only when required to expose existing profile metadata safely to the test. No generated discovery packet refresh should be included unless the new registry is intentionally integrated into that refresh workflow.

## 12. Acceptance Criteria

- Project + DU Model is documented as the authoritative identity.
- View is documented as source-layout evidence, not identity.
- All existing profile IDs remain unchanged.
- `tx_mini_pr_v1` is explicitly marked as legacy accepted.
- `zte_tx_mini_pr_v1` is proven to be a separate identity.
- CD Consolidation duplicate identity is recorded with an exact permitted profile set.
- New duplicate or nonstandard identities fail automated tests unless explicitly justified.
- No lifecycle promotion, ECC enablement, raw customer data, or production behavior change is introduced.
