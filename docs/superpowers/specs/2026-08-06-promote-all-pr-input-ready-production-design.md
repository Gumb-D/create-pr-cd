# Promote All Current PR_INPUT_READY Profiles to Production — Design

## Decision

Promote the seven DU Profiles that are currently `PR_INPUT_READY` to explicit `PRODUCTION` status:

- `tx_rollout_2023_pr_v1`
- `mw_eos_swap_pr_v1`
- `celcomdigi_bau_2023_pr_v1`
- `celcomdigi_bau_2024_pr_v1`
- `celcomdigi_usp_pr_v1`
- `jendela_tx_migration_pr_v1`
- `zte_tx_mini_pr_v1`

`tx_mini_pr_v1` remains `PRODUCTION`. `celcomdigi_cd_consolidation_2023_pr_v1` remains `DRAFT`.

## Operating Model

Formal production jobs are the validation surface. No non-production UAT approval is required for this promotion. Runtime issues are expected to surface through real production jobs and must remain observable through structured job errors and review outputs.

## Safety Boundaries

The promotion changes lifecycle permission only. It does not weaken or bypass:

- Project + DU Model Profile routing;
- required-field and approved-mapping checks;
- Header Hash and scope-aware stable-field validation;
- duplicate PR prevention;
- missing-contract blocking;
- Cancel/Drop, SM, Huawei-owned, and no-output rules;
- partial-output prevention;
- renderer and ECC integrity checks.

Future Profiles that reach `PR_INPUT_READY` are not automatically production-enabled. Production remains an explicit status recorded in each Profile and governance registry.

## Governance Synchronization

The implementation must synchronize Profile YAML files, identity, transition, readiness, rollback, deprecation, discovery, unresolved-review, and generated Markdown evidence. Transition entries for the seven Profiles must explicitly mark `PRODUCTION` as eligible with no lifecycle denial.

## Verification

Verification focuses on configuration integrity and production gating rather than business UAT:

- all eight intended Profiles load as `PRODUCTION`;
- CD Consolidation remains `DRAFT`;
- formal CLI accepts each promoted Profile without `--non-production-uat`;
- `DRAFT` remains blocked;
- governance consistency and discovery packet checks pass;
- affected and broad automated regression suites pass, excluding only documented pre-existing environment-dependent failures.
