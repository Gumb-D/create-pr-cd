# PR Creator Knowledge Base

## Purpose

This directory is the controlled knowledge layer for the CelcomDigi TX PR Creator.

It is not a replacement for the PR generator. It records the business rules, rule sources, runtime status, known ambiguities and acceptance questions needed to make the generator explainable, auditable and eventually configuration-driven.

## Why this exists

The current PR Creator contains business knowledge across:
- `SKILL.md`
- `README.md`
- runtime Python modules
- PR model workbooks, contract mappings and ECC templates
- DU Profile / four-layer Header evidence

That is workable for a script, but hard to govern when rules change, when an auditor asks why a line was generated, or when an AI Worker must explain its decision.

## Current boundary

This knowledge base separates **business approval** from **runtime implementation**.

- The current Python generator remains the runtime authority for what is actually executable.
- The rule register records extracted, verified or business-approved intended behavior.
- A rule may be `APPROVED` while `runtime_status` remains `DOCUMENTED_ONLY`; that does not enable ECC generation.
- No mapping value may be changed here as a substitute for changing the approved input mapping, DU Profile, PR model, or controlled contract reference.
- Raw iEPMS exports used as discovery/UAT evidence must not be committed.

As of 2026-08-11:

- TSS/TI are runtime scopes.
- Planning business logic is approved under Issue #34 for all eight supported DU Models, but runtime implementation is still pending.
- Operation Backoffice remains a separate future scope and is not part of Issue #34.

## Directory

```text
knowledge_base/pr_creator/
├─ README.md
├─ rules/
│  └─ pr_creator_rule_register.yaml
├─ validation/
│  └─ acceptance_questions.yaml
└─ governance/
   └─ known_divergences.md
```

## Knowledge record model

Every rule has:
- `id`: stable identifier, for example `PRC-ELIG-001`
- `title`: human-readable rule name
- `domain`: eligibility, matching, mapping, output, review or roadmap
- `knowledge_status`: `EXTRACTED`, `VERIFIED`, `APPROVED`, `DEPRECATED`
- `runtime_status`: `ACTIVE`, `PARTIAL`, `DOCUMENTED_ONLY`, `UNKNOWN`
- `source_references`: the current file(s) that evidence the rule
- `risk`: operational consequence if the rule is wrong
- `acceptance_question_ids`: questions that must eventually be tested

## Source-of-truth rule

Use the following order:

1. **Runtime behaviour:** current code on the released branch for what is executable now.
2. **Approved business decision:** signed-off rule/change record for intended behavior.
3. **Approved reference data:** DU Profile/fingerprint evidence, PR Model, `Info/input/contract_info_reference.md`, and ECC template.
4. **This KB:** controlled inventory, explanation and test specification.
5. **Unapproved/historical documentation:** reference only.

If runtime and approved intended behavior disagree because implementation is still pending, record that state explicitly rather than silently claiming the feature is executable.

## Rule lifecycle

```text
EXTRACTED → VERIFIED → APPROVED → IMPLEMENTED → REGRESSION_TESTED
                         ↓
                    DEPRECATED
```

- `EXTRACTED`: copied from current documentation or code, not business-confirmed.
- `VERIFIED`: evidence and observed runtime behaviour agree.
- `APPROVED`: business owner has confirmed intended behaviour.
- `IMPLEMENTED`: approved rule has a traceable code/config implementation.
- `REGRESSION_TESTED`: an automated test proves the intended result.
- `DEPRECATED`: retained for traceability only.

The current YAML enum does not yet represent `IMPLEMENTED` and `REGRESSION_TESTED` directly; see `KB-DIV-006`.

## Change workflow

1. Create or update one rule record.
2. Link the source, owner, effective date and acceptance question.
3. Record any conflict or unclear input as a divergence.
4. Obtain business approval for a rule change.
5. Change code/config in a separate implementation step.
6. Add or update regression fixtures.
7. Update `runtime_status` only after implementation is merged and verified.

## Issue #34 Planning baseline

The approved Planning decision is recorded in:

- `docs/superpowers/specs/2026-08-11-planning-pr-all-du-design.md`
- `docs/superpowers/plans/2026-08-11-planning-pr-all-du.md`
- `rules/pr_creator_rule_register.yaml` (`PRC-ELIG-003`, `PRC-PLAN-001`, `PRC-PLAN-002`)
- `validation/acceptance_questions.yaml` (`AQ-025` through `AQ-032`)

The runtime must remain fail-closed until those acceptance requirements are implemented and tested.

## First operating objective

The first improvement is not “make an AI chatbot.”

The first improvement is to make each PR decision answerable:

```text
Why was this site included?
Which rule selected this PR line?
Which source data was used?
Why was a row marked REVIEW_REQUIRED?
Which contract / purchasing mapping was applied?
```

Once a rule is stable and regression-covered, the next controlled step is to move low-risk approved decisions into machine-readable configuration without weakening safety controls.
