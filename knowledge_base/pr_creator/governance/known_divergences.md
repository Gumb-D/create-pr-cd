# Known divergences and decisions required

This register is deliberately small. A divergence is not automatically a defect; it is a point where current documentation, code, source data or intended business policy do not yet form one unambiguous truth.

| ID | Severity | Topic | Evidence | Current risk | Required decision |
|---|---|---|---|---|---|
| KB-DIV-001 | Critical | Contract and Purchasing Area source | The Skill states that `contract infor` in the PR Model is the source. The CLI loads `Info/input/contract_info_reference.md` for Region → Purchasing Area and Subcontractor → Contract. | PR output may be generated from a mapping source that differs from the documented source. | Select the authoritative source, define synchronisation ownership, and record a version/effective date. |
| KB-DIV-002 | High | TI antenna category vocabulary | The Skill lists 0.3m/0.6m as small and separate 1.2m / 1.8m / 2.4m groups. Runtime categories are `0.3/0.6m`, `0.9/1.2m`, `1.8m`, `2.4m`, or an explicit size. | A PR Model might use labels that do not match runtime category values. | Confirm the approved PR Model category labels and add fixtures for every allowed antenna size. |
| KB-DIV-003 | Critical | Fuzzy subcontractor matching | README says fuzzy matching is enabled. Runtime returns the closest match when similarity is above 0.6. The Skill instructs REVIEW_REQUIRED for missing reference values but does not approve silent fuzzy contract selection. | An incorrect subcontractor could receive another subcontractor's contract number. | Decide whether fuzzy matching is allowed only as a suggestion, or can directly generate ECC output. Require score, matched value and reviewer trace if retained. |
| KB-DIV-004 | High | Implemented scope versus documented scope | Skill documents TSS, TI, Planning and Operation Backoffice. CLI argument validation supports only TSS and TI. | Users may plan an operational workflow around a scope that cannot run. | Keep external user guidance at TSS/TI only until a tested implementation exists. |
| KB-DIV-005 | High | Incomplete TI antenna input handling | Skill requires REVIEW_REQUIRED when one size is blank. Runtime computes a category from the available side and carries a review remark. | A downstream branch could still use an incomplete category unless end-to-end output behaviour is tested. | Add an acceptance fixture that proves no normal TI line is emitted when either antenna side is missing. |

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
