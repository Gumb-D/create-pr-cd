# MW DU Profile Naming and Identity Standard

## 1. Purpose

This standard defines how MW DU PR profiles are identified and named before additional DU models are onboarded under Issue #21.

The authoritative business rule is:

```text
DU Profile Identity = iEPMS Project + DU Model
```

The canonical machine identity key is:

```text
(project_key, du_model_id)
```

`du_model_name` remains readable evidence, but the stable iEPMS DU Model ID is the primary model identifier.

## 2. Profile ID format

New profile families should use:

```text
<project_slug>_<du_model_slug>_pr_v<major>
```

Rules:

- Use lowercase snake case.
- Use the controlled project slug from `config/registries/mw_du_profile_identity_registry.yaml`.
- Derive the DU model slug from the DU Model, not from an export View.
- Use `_pr_v<major>` as the profile-family version suffix.
- A `STANDARD` profile ID must equal its registry `canonical_profile_id`.
- Existing approved IDs are not renamed solely to improve naming consistency.

## 3. View handling

An iEPMS export View is source-layout evidence. It is not a separate DU profile identity.

The same Project + DU Model may accept multiple Views through profile metadata such as:

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

A DRAFT profile may preserve unapproved layouts separately:

```yaml
layout_variants:
  - variant_id: <layout A>
    view_id: <view A>
    observed_header_hash: <observed hash A>
    field_mapping: <exact four-layer discovery evidence>
```

Each accepted or observed layout still requires controlled evidence:

- exact four-layer Header Fingerprints;
- strict Header Hash validation;
- approved canonical-field mappings before lifecycle promotion;
- fail-closed handling for unknown or changed layouts.

Combining Views within one profile family does not weaken source validation.

## 4. When a separate profile is allowed

Create a separate profile family only when at least one of these conditions applies:

- different iEPMS Project;
- different DU Model;
- materially different PR business semantics;
- materially incompatible canonical-field meanings;
- source layouts that cannot be validated safely within one profile family.

A different View name, View ID, Header Hash, or WBS/Task location alone is not sufficient justification.

## 5. Registry statuses

### `STANDARD`

The current `profile_id` equals the registry `canonical_profile_id`.

### `LEGACY_ACCEPTED`

The current profile predates this standard or is retained to avoid migration risk. A non-empty reason is mandatory.

### `CONSOLIDATION_REVIEW_REQUIRED`

This is a temporary migration status only. It may be used while multiple existing profiles share one Project + DU Model identity and the business semantics have not yet been confirmed. The registry must list the exact temporarily permitted set. Once the business decision is made, the duplicate profiles must be consolidated or separated using a genuine business identity—not retained by View.

The current registry contains no active duplicate-identity review.

## 6. Existing profile decisions

### Legacy accepted TX Mini profile

`tx_mini_pr_v1` remains unchanged.

```text
Project: Malaysia_CelcomDigi_Project
DU Model: TX Mini Project
DU Model ID: 4188808420049567786
```

Its existing ID predates this standard and is retained to avoid migration risk.

### Separate ZTE TX MINI identity

`zte_tx_mini_pr_v1` must remain separate from `tx_mini_pr_v1`.

```text
Project: CelcomDigi_MW
DU Model: ZTE TX MINI
DU Model ID: 8638668101234290847
```

The similar wording does not make the identities equivalent. Both the Project and DU Model are different.

### Standard names retained

The registry currently treats these names as standard:

- `celcomdigi_bau_2023_pr_v1`
- `celcomdigi_bau_2024_pr_v1`
- `celcomdigi_usp_pr_v1`
- `mw_eos_swap_pr_v1`
- `celcomdigi_cd_consolidation_2023_pr_v1`

### Other legacy names retained

These existing names remain stable and are explicitly registered as legacy accepted:

- `tx_rollout_2023_pr_v1`
- `jendela_tx_migration_pr_v1`
- `zte_tx_mini_pr_v1`

### CD Consolidation decision

Business owner decision A confirms that Decom Site and Rollout use the same Backoffice / Operation PR type and belong to one profile family:

```text
Project: Malaysia_CelcomDigi_Project
DU Model: CD consolidation 2023
DU Model ID: 8359047522524182050
Profile: celcomdigi_cd_consolidation_2023_pr_v1
```

The canonical DRAFT profile preserves both source layouts:

- Decom View ID `702960351133798763`, observed Header Hash `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`;
- Rollout View ID `8359047522524230651`, observed Header Hash `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`.

Both layouts remain unapproved discovery evidence. The profile remains `DRAFT`, contains no approved Header Hash, and cannot generate ECC. Backoffice / Operation PR eligibility, duplicate prevention, output contract, and template development remain under Issue #34.

## 7. Change control

Every new or changed DU profile identity requires:

1. an update to `config/registries/mw_du_profile_identity_registry.yaml`;
2. a matching Project + DU Model identity;
3. a canonical profile ID or documented exception reason;
4. a deliberate temporary review record only when a duplicate identity cannot yet be resolved;
5. passing `tests/test_du_profile_identity_governance.py` and the full regression suite.

Governance failures use actionable codes such as:

```text
UNREGISTERED_DU_PROFILE:<profile_id>
PROFILE_IDENTITY_MISMATCH:<profile_id>
PROFILE_STATUS_MISMATCH:<profile_id>
DUPLICATE_PROFILE_IDENTITY:<identity_key>
DUPLICATE_IDENTITY_SET_MISMATCH:<identity_key>
NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:<profile_id>
LEGACY_PROFILE_WITHOUT_REASON:<profile_id>
```

## 8. Safety boundary

This standard does not:

- promote a profile to `PRODUCTION`;
- enable ECC output;
- approve mappings or Header Hashes;
- change PR business rules;
- replace golden parity, business validation, or release approval.

Profile identity governance and production readiness are separate controls.
