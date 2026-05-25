# Agent Execution Guideline

**Project Context:** `create-pr-cd` / OpenClaw / Codex execution support  
**Document Type:** Consolidated agent workflow guideline  
**Status:** Active operating guideline  
**Last Updated:** 2026-05-25

---

## 1. Purpose

This document consolidates the useful execution-control content from the previous OpenClaw skill guideline into a shorter operating guide.

It should be used when ChatGPT, Codex, OpenClaw, or another agent is asked to work on the repository or skill files.

The purpose is simple:

```text
Plan first.
Task clearly.
Execute within scope.
Record results.
Test before accepting.
```

---

## 2. Core Operating Principles

## 2.1 Plan Before Build

No skill, script, or repo change should start before the task is clear.

The plan must define:

- Objective.
- Input files.
- Target files.
- Expected output.
- Acceptance criteria.
- Testing requirement.
- Scope boundaries.

Do not start by writing or editing files first.

---

## 2.2 Task-Driven Execution

Treat work as scoped tasks, not open-ended editing.

Each task should have:

- Narrow scope.
- Clear owner or agent type.
- Expected output path.
- Testing requirement.
- QA/review requirement.

---

## 2.3 Record Everything Important

Record decisions, changes, test results, and unresolved items.

Use records for:

- Planning brief.
- Task breakdown.
- Execution notes.
- Test results.
- QA summary.
- User actions required.
- Known blockers.

---

## 2.4 No Scope Expansion

Agents must not expand the task beyond the user-approved scope.

Examples of forbidden drift:

- Refactoring unrelated files.
- Changing business rules not included in the task.
- Adding UI/backend architecture when the task is documentation only.
- Committing or pushing without explicit instruction.

---

## 3. Agent Roles

| Role | Responsibility |
|---|---|
| Chat Agent | User communication, final control, progress owner, acceptance decision. |
| Task Planner | Break down work, define dependencies, prepare executable tasks. |
| DEV Agent | Implement assigned changes only. |
| TEST Agent | Run relevant checks and record results. |
| QA Agent | Verify scope, quality, safety, and acceptance criteria. |

Subagents must not commit, push, deploy, or modify control files unless explicitly authorized.

---

## 4. Recommended Command Center Structure

Use this only when the project needs formal multi-agent tracking.

```text
/command-center/00-task-center.md
/command-center/01-user-tasklist.md
/command-center/02-project-progress.md
/command-center/03-instruction.md
/command-center/context/
/command-center/planning/planning-brief.md
/command-center/planning/task-breakdown.md
/command-center/planning/execution-plan.md
/command-center/planning/dependency-map.md
/command-center/tasks/TASK-XXX.md
/command-center/agent-results/TASK-XXX/programming.md
/command-center/agent-results/TASK-XXX/testing.md
/command-center/agent-results/TASK-XXX/qa.md
/command-center/logs/execution-log.md
```

### Chat Agent Only Files

Only the Chat Agent should edit:

```text
/command-center/00-task-center.md
/command-center/01-user-tasklist.md
/command-center/02-project-progress.md
/command-center/context/*
```

---

## 5. Task File Minimum Template

Each task should contain:

```text
Task ID:
Title:
Assigned Agent Type:
Priority:
Status:
Risk Level:
Objective:
Background:
Input Files:
Target Files / Areas:
Expected Output:
Acceptance Criteria:
Dependencies:
Testing Requirement:
QA Requirement:
Output File Path:
Testing File Path:
QA File Path:
User Action Required:
Notes:
```

---

## 6. Execution Lifecycle

Recommended task lifecycle:

```text
BACKLOG
→ ASSIGNED
→ IN_PROGRESS
→ SUBMITTED
→ TESTING
→ QA
→ READY_FOR_MAIN_REVIEW
→ DONE
```

Do not skip testing or QA when code or business rules are changed.

---

## 7. DEV Agent Rules

DEV Agent must:

- Read the task file.
- Work only within assigned files/areas.
- Avoid unrelated cleanup.
- Preserve existing behavior unless instructed.
- Write programming result summary.
- Return only the result path or concise summary.

DEV Agent must not:

- Commit.
- Push.
- Deploy.
- Rewrite architecture without approval.
- Change business logic outside task scope.

---

## 8. TEST Agent Rules

TEST Agent must:

- Read the task and DEV result.
- Run relevant checks.
- Record exact commands and results.
- Identify pass/fail clearly.
- Save testing summary.

Minimum test record:

```text
Command:
Result:
Pass/Fail:
Notes:
Unresolved Issues:
```

---

## 9. QA Agent Rules

QA Agent must verify:

- Requirement completeness.
- Scope adherence.
- Blueprint/design alignment.
- No unrelated file changes.
- Test evidence exists.
- Known risks are documented.

QA result should clearly state:

```text
APPROVED / NOT APPROVED
Reason:
Required Fixes:
```

---

## 10. Skill Development Rules

OpenClaw skills should be treated as behavior modules.

Each skill should have:

- Clear name.
- Description.
- Inputs and outputs.
- Explicit steps.
- Safe defaults.
- Conditional logic.
- Acceptance criteria.
- Test approach.

Recommended structure:

```text
openclaw/skills/<skill-name>/skill.md
openclaw/skills/<skill-name>/references/stepNN_<name>.md
```

Avoid monolithic long instructions.

---

## 11. Repository Work Guardrails

For `create-pr-cd` or similar repo tasks:

- Check current branch and working tree first.
- Do not edit README for detailed discovery rules unless explicitly requested.
- Put design details under `docs/`.
- Keep implementation separate from discovery documents.
- Do not mix documentation changes and code changes unless explicitly requested.
- Do not commit or push unless explicitly requested.
- Preserve REVIEW_REQUIRED safety behavior.

---

## 12. Final Acceptance Checklist

Before calling work complete:

- Scope matches user request.
- Target files created or updated.
- No unrelated files changed.
- Tests/checks performed or explicitly marked not applicable.
- Risks/open questions documented.
- User-facing summary is concise and actionable.

Final principle:

```text
No plan, no build.
No record, no trust.
No test, no acceptance.
No scope control, no merge.
```
