# CD Consolidation 2023 Profile Family Design

## Decision

Business owner decision: Decom Site and Rollout are the same Backoffice / Operation PR type and may share one DU Profile family.

The canonical identity remains:

```text
Project: Malaysia_CelcomDigi_Project
DU Model: CD consolidation 2023
DU Model ID: 8359047522524182050
```

View Name, View ID, Header Hash, and four-layer field locations are layout evidence only. They do not create separate profile identities.

## Current problem

Two DRAFT profiles currently share the same Project + DU Model identity:

- `cd_consolidation_2023_decom_pr_v1`
- `cd_consolidation_2023_rollout_pr_v1`

The Project + DU Model resolver cannot safely choose between two profile families. The temporary governance exception keeps the duplicate identity fail-closed, but it prevents deterministic automatic routing.

## Canonical profile family

Replace the two View-based DRAFT profiles with one canonical profile:

```text
celcomdigi_cd_consolidation_2023_pr_v1
```

The profile remains `DRAFT` and is not eligible for TSS/TI or Backoffice / Operation ECC generation.

## Layout evidence model

The canonical profile records two layout variants:

### Decom layout

- View ID: `702960351133798763`
- Observed Header Hash: `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16`
- Four-layer field locations retain the existing Decom evidence.

### Rollout layout

- View ID: `8359047522524230651`
- Observed Header Hash: `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1`
- Four-layer field locations retain the existing Rollout evidence.

The profile stores both layouts as discovery-only variants. Neither Header Hash is approved. All field candidates remain `UNVERIFIED`.

## Resolver behaviour

Profile routing uses only Project + DU Model and returns the canonical profile.

After routing, the loader may identify the observed layout using exact View ID, Header Hash, or four-layer fingerprints for audit and future mapping work. An unknown layout remains fail-closed.

The normal resolver must not use View Name or View ID to select a different profile family.

## Safety boundaries

This change does not:

- implement Backoffice / Operation PR eligibility;
- map this DU Model into the existing TSS/TI workflow;
- approve either observed Header Hash;
- approve any field mapping;
- promote lifecycle status;
- enable ECC generation;
- define Backoffice / Operation duplicate-prevention or output-template rules.

Those items remain under Issue #34.

## Migration

1. Create `config/du_profiles/celcomdigi_cd_consolidation_2023_pr_v1.yaml`.
2. Preserve all Decom and Rollout discovery evidence as layout variants.
3. Delete the two View-based profile files.
4. Replace the two registry records with one `STANDARD` record.
5. Remove the duplicate-identity review exception.
6. Update governance tests and generated governance documentation to one profile family.
7. Keep discovery inventory rows per View, but point both rows to the same canonical Profile ID.

## Acceptance criteria

- Exactly one profile route exists for the identity.
- Both View IDs and observed Header Hashes remain traceable.
- Both sets of four-layer mapping evidence remain traceable.
- The canonical profile remains `DRAFT`.
- `approved_header_hashes` remains empty.
- Existing TSS/TI entrypoints generate no ECC for this profile.
- Duplicate-identity governance exception is removed.
- Targeted and broad regression tests pass.
