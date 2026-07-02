# PR Creator Knowledge Base

## Purpose

This directory is the controlled knowledge layer for the CelcomDigi TX PR Creator.

It is not a replacement for the PR generator. It records the business rules, rule sources, runtime status, known ambiguities and acceptance questions needed to make the generator explainable, auditable and eventually configuration-driven.

## Why this exists

The current PR Creator contains business knowledge across:
- `create-pr-cd_SKILL.md`
- `README.md`
- `scripts/generate_tss_pr_ecc.py`
- PR model workbooks, contract mappings and ECC templates

That is workable for a script, but hard to govern when rules change, when an auditor asks why a line was generated, or when an AI Worker must explain its decision.

## v0.1 boundary

This first version is a **baseline extraction**, not a runtime switch.

- The current Python generator remains the runtime authority for what is actually executed.
- The rule register records what has been extracted from the current baseline and whether it still needs business verification.
- No rule is treated as approved merely because it exists in this folder.
- No mapping value may be changed here as a substitute for changing the approved input mapping or PR model.

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

Until the generator is intentionally refactored to load this KB at runtime, use the following order:

1. **Runtime behaviour:** current code on the released branch
2. **Approved business decision:** signed-off rule / change record
3. **Approved reference data:** PR Model, contract mapping and ECC template
4. **This KB:** controlled inventory, explanation and test specification
5. **Unapproved documentation:** reference only

If items 1–4 disagree, do not silently choose one. Register the difference in `governance/known_divergences.md`, decide an owner, and resolve it through a reviewed change.

## Rule lifecycle

```text
EXTRACTED → VERIFIED → APPROVED → IMPLEMENTED → REGRESSION_TESTED
                         ↓
                    DEPRECATED
```

- `EXTRACTED`: copied from current documentation or code, not business-confirmed.
- `VERIFIED`: evidence and observed runtime behaviour agree.
- `APPROVED`: business owner has confirmed the intended behaviour.
- `IMPLEMENTED`: approved rule has a traceable code/config implementation.
- `REGRESSION_TESTED`: an automated test proves the intended result.
- `DEPRECATED`: retained for traceability only.

## Change workflow

1. Create or update one rule record.
2. Link the source, owner, effective date and acceptance question.
3. Record any conflict or unclear input as a divergence.
4. Obtain business approval for a rule change.
5. Change code/config in a separate implementation change.
6. Add or update a regression fixture.
7. Update `runtime_status` only after the implementation is merged and verified.

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

Once this register and acceptance set are stable, the next controlled step is to move low-risk, approved rules from Python into machine-readable configuration while preserving regression coverage.
