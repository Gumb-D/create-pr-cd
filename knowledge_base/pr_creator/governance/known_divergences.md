# Known divergences and decisions required

This register is deliberately small. A divergence is not automatically a defect; it is a point where current documentation, code, source data or intended business policy do not yet form one unambiguous truth.

| ID | Severity | Topic | Evidence | Current risk | Required decision |
|---|---|---|---|---|---|
| KB-DIV-002 | High | TI antenna category vocabulary | The Skill lists 0.3m/0.6m as small and separate 1.2m / 1.8m / 2.4m groups. Runtime categories are `0.3/0.6m`, `0.9/1.2m`, `1.8m`, `2.4m`, or an explicit size. | A PR Model might use labels that do not match runtime category values. | Confirm the approved PR Model category labels and add fixtures for every allowed antenna size. |
| KB-DIV-003 | Critical | Fuzzy subcontractor matching | Generic non-Planning runtime behavior may use fuzzy subcontractor matching, while Planning explicitly permits only GCI/GTSB/GCI_AA/GTSB_AA and fails closed otherwise. | Outside Planning, an incorrect subcontractor could receive another subcontractor's contract number if fuzzy matching is not sufficiently governed. | Decide whether generic fuzzy matching is allowed only as a suggestion, or can directly generate ECC output. Require score, matched value and reviewer trace if retained. |
| KB-DIV-006 | Medium | Rule lifecycle values not represented in the YAML `knowledge_status` enum | The README lifecycle lists `IMPLEMENTED` and `REGRESSION_TESTED` as later lifecycle states. The `knowledge_status` enum in `rules/pr_creator_rule_register.yaml` permits only `EXTRACTED`, `VERIFIED`, `APPROVED`, `DEPRECATED`. | Implemented and regression-tested rules have no single knowledge-status value representing that final lifecycle without changing the schema. | Decide whether to extend `knowledge_status`, or continue representing implementation through `runtime_status: ACTIVE` plus explicit regression evidence. |

## Resolved divergences

| ID | Severity | Topic | Evidence | Resolution | Related PR / commit |
|---|---|---|---|---|---|
| KB-DIV-001 | Critical | Contract and Purchasing Area source | Runtime loads `Info/input/contract_info_reference.md`; Issue #34 confirmed Planning uses the same contract reference and `_AA` normalizes to base GCI/GTSB contract identity. | `Info/input/contract_info_reference.md` is the authoritative controlled source for Region → Purchasing Area and Subcontractor → Contract Number. | Issue #34 business-rule baseline, 2026-08-11 |
| KB-DIV-004 | High | Implemented scope versus documented scope | Issue #34 implemented `--scope Planning` through `scripts/create_pr.py`, eight approved DU Profiles, deterministic selector, Planning-specific renderer, shared contract mapping and terminal reconciliation. Targeted all-DU raw four-header E2E, full repository regression and existing-scope regressions pass on the Issue #34 branch. | Planning is an active implemented runtime scope. Operation Backoffice remains a separate undefined/unsupported future scope and must not be inferred from Planning. | Issue #34 / PR #86 |
| KB-DIV-005 | High | Incomplete TI antenna input handling | Regression coverage verifies antenna-independent TI SOWs are not blocked by missing antenna input while antenna-dependent models remain fail closed. | Existing approved TI behavior remains active and regression protected. | PR #13 and subsequent regressions |

## Planning Issue #34 approved and implemented decision record

```text
Decision ID: ISSUE-34-PLANNING-ALL-DU
Decision date: 2026-08-11
Business owner: TX Program / Business Rule Owner
Technical owner: PR Creator Maintainer
Chosen policy:
  - Planning applies to all eight supported DU Models.
  - GCI/GTSB use 350001143904 for five full-planning DUs.
  - GCI/GTSB use 350001143905 for TX Mini Project, MW EOS Swap and ZTE TX MINI.
  - GCI_AA/GTSB_AA use only optional line item 350001042321 for every supported DU.
  - _AA normalizes to GCI/GTSB only for contract identity.
  - TX Planning Remarks is not a Planning PR decision input.
  - contract_info_reference.md is authoritative for contract/purchasing mapping.
Effective date: 2026-08-11
Implementation:
  - scripts/planning_pr_selector.py
  - scripts/planning_pr_runtime.py
  - scripts/planning_ecc_renderer.py
  - scripts/create_pr.py official Planning entrypoint
  - Planning canonical scope in canonical_site_validator.py / canonical_input_pipeline.py
Regression evidence:
  - tests/test_issue_34_planning_selector.py
  - tests/test_issue_34_planning_profile_fields.py
  - tests/test_issue_34_planning_canonical.py
  - tests/test_issue_34_planning_eligibility.py
  - tests/test_issue_34_planning_renderer.py
  - tests/test_issue_34_planning_entrypoint.py
  - tests/test_issue_34_planning_end_to_end.py
  - full repository unittest regression
Related PR / commit: PR #86 / Issue #34
```

## Decision logging format

When resolving a divergence, add an entry below:

```text
Decision ID:
Decision date:
Business owner:
Technical owner:
Chosen source / policy:
Effective date:
Required implementation:
Regression fixture:
Related PR / commit:
```
