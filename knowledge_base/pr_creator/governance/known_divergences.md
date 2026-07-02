# Known divergences and decisions required

This register is deliberately small. A divergence is not automatically a defect; it is a point where current documentation, code, source data or intended business policy do not yet form one unambiguous truth.

| ID | Severity | Topic | Evidence | Current risk | Required decision |
|---|---|---|---|---|---|
| KB-DIV-001 | Critical | Contract and Purchasing Area source | The Skill states that `contract infor` in the PR Model is the source. The CLI loads `Info/input/contract_info_reference.md` for Region → Purchasing Area and Subcontractor → Contract. | PR output may be generated from a mapping source that differs from the documented source. | Select the authoritative source, define synchronisation ownership, and record a version/effective date. |
| KB-DIV-002 | High | TI antenna category vocabulary | The Skill lists 0.3m/0.6m as small and separate 1.2m / 1.8m / 2.4m groups. Runtime categories are `0.3/0.6m`, `0.9/1.2m`, `1.8m`, `2.4m`, or an explicit size. | A PR Model might use labels that do not match runtime category values. | Confirm the approved PR Model category labels and add fixtures for every allowed antenna size. |
| KB-DIV-003 | Critical | Fuzzy subcontractor matching | README says fuzzy matching is enabled. Runtime returns the closest match when similarity is above 0.6. The Skill instructs REVIEW_REQUIRED for missing reference values but does not approve silent fuzzy contract selection. | An incorrect subcontractor could receive another subcontractor's contract number. | Decide whether fuzzy matching is allowed only as a suggestion, or can directly generate ECC output. Require score, matched value and reviewer trace if retained. |
| KB-DIV-004 | High | Implemented scope versus documented scope | Skill documents TSS, TI, Planning and Operation Backoffice. CLI argument validation supports only TSS and TI. | Users may plan an operational workflow around a scope that cannot run. | Keep external user guidance at TSS/TI only until a tested implementation exists. |
| KB-DIV-006 | Medium | Rule lifecycle values not represented in the YAML `knowledge_status` enum | The README lifecycle (`README.md`, "Rule lifecycle" section) lists `IMPLEMENTED` and `REGRESSION_TESTED` as later lifecycle states. The `knowledge_status` enum in `rules/pr_creator_rule_register.yaml` currently permits only `EXTRACTED`, `VERIFIED`, `APPROVED`, `DEPRECATED`. | Rules with merged, regression-tested behaviour (for example `PRC-MODEL-002`, `PRC-DATA-001`, `PRC-TSS-001`, `PRC-OUT-004`) have no enum value that records "implemented and regression-tested" without changing the schema. This KB intentionally does not silently add enum values to close the gap. | Business/technical owners must confirm whether lifecycle evidence beyond `VERIFIED` should be added as new `knowledge_status` enum values, or represented as separate fields (for example `runtime_status: ACTIVE` plus an explicit `regression_evidence` field) so the schema change is deliberate and reviewed, not incidental to a documentation-only update. |

## Resolved divergences

| ID | Severity | Topic | Evidence | Resolution | Related PR / commit |
|---|---|---|---|---|---|
| KB-DIV-005 | High | Incomplete TI antenna input handling | Skill required REVIEW_REQUIRED when one size is blank. Runtime previously computed a category from the available side and carried a review remark. | PR #13 (`c3ccb22`, `8b538cc`) verified end-to-end that: (1) antenna-independent TI SOWs, `BBU Patching` and `MW IDU Patching`, do not require antenna data and generate normally with blank or one-sided antenna input (`scripts/generate_tss_pr_ecc.py:678-716`, `scripts/generate_tss_pr_ecc.py:1279-1321`); (2) antenna-dependent TI models (for example `MW Parallel Link`) still fail closed to REVIEW_REQUIRED on incomplete NE/FE data; (3) regression coverage exists proving both outcomes in `tests/test_ti_sow_matching.py:120-255` (`TestProductionTiSowMatching.test_ti_generator_requires_exact_sow_matches`). See `PRC-ANT-001` and `PRC-MODEL-002`. | PR #13, commits `c3ccb22`, `8b538cc`, `79bb5ba` |

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
