# OpenClaw Skill Development Guideline
# Multi-Agent Planning, Tasking, Recording, and Execution

---

# 0. Purpose

This guideline defines a structured workflow for developing OpenClaw skills using a disciplined multi-agent system.

The system is designed for:

- OpenClaw agent skill development
- Modular skill definition and lifecycle management
- Clear task planning and execution
- Persistent record keeping
- Parallel, safe, and auditable work

Core principle:

> Plan, task, record, execute with multi-agent discipline.


---

# 1. Development Principles

## 1.1 Plan Before Build

No skill should be authored before the plan is clear.

The plan must define:

- Skill intent and user scenario
- Skill inputs and outputs
- Required steps and transitions
- Agent role and behavior
- Acceptance criteria
- File and version scope
- Testing and QA strategy

Do not start by writing step content first.

Start with:

- Skill purpose
- Skill architecture
- Task breakdown
- Output contract
- Validation plan

---

## 1.2 Task-Driven Execution

Treat skill development as a task system, not one-shot content creation.

Every work item must become a task with:

- a narrow scope
- a clear owner
- an expected output path
- testing requirements
- QA requirements

---

## 1.3 Record Everything

Every decision, plan, and result must be recorded in workspace files.

Use command-center records for:

- planning briefs
- task files
- task outputs
- testing results
- QA summaries
- blockers and user actions

This creates an audit trail and supports predictable delivery.

---

## 1.4 Multi-Agent Discipline

Use the agent hierarchy:

User → Chat Agent → Task Planner → Specialized Subagents.

Roles are:

- Chat Agent = user communication, final control, progress owner
- Task Planner = task breakdown, dependency mapping, execution coordination
- DEV Subagent = implementation
- TEST Subagent = verification
- QA Subagent = quality review

Subagents must not commit, push, or deploy.


# 2. OpenClaw Skill Strategy

## 2.1 Skill as Behavior Module

OpenClaw skills should be treated as behavior modules with:

- a clear name
- explicit steps or actions
- conditional logic
- safe defaults
- user guidance

The skill should be easy to inspect and validate.

---

## 2.2 Modular Step Design

Skills should use modular steps or step files when applicable.

Each step should be:

- single-purpose
- confirmable
- reversible or skip-safe
- explicit about next action

Avoid monolithic long instructions.

---

## 2.3 File-Driven Skill Metadata

Skill definition should include metadata for:

- name
- description
- tags
- actor role
- constraints
- tools and triggers

Store metadata alongside skill step files.


# 3. Command Center for Skill Development

## 3.1 Required Files

For skill development, maintain at least:

- `/command-center/03-instruction.md`
- `/command-center/planning/planning-brief.md`
- `/command-center/planning/task-breakdown.md`
- `/command-center/tasks/TASK-XXX.md`
- `/command-center/agent-results/TASK-XXX/programming.md`
- `/command-center/agent-results/TASK-XXX/testing.md`
- `/command-center/agent-results/TASK-XXX/qa.md`
- `/command-center/logs/execution-log.md`

---

## 3.2 Chat Agent Only Files

Only the Chat Agent may edit:

- `/command-center/00-task-center.md`
- `/command-center/01-user-tasklist.md`
- `/command-center/02-project-progress.md`
- `/command-center/context/*`

Subagents may not edit these files.

---

## 3.3 Task File Template

Each task file should include:

- Task ID
- Title
- Assigned Agent Type
- Priority
- Status
- Risk Level
- Objective
- Background
- Input Files
- Target Files / Areas
- Expected Output
- Acceptance Criteria
- Dependencies
- Parallel Group
- Testing Requirement
- QA Requirement
- Output File Path
- Testing File Path
- QA File Path
- User Action Required
- Progress Update Required
- Notes


# 4. Execution Rules

## 4.1 DEV Subagent

DEV Subagents must:

- read task files
- work only within assigned scope
- avoid unrelated changes
- write programming results to task result files
- return only the result file path


## 4.2 TEST Subagent

TEST Subagents must:

- read the task and programming results
- run the relevant checks
- record commands and results
- write testing results to task result files
- return only the test file path


## 4.3 QA Subagent

QA Subagents must:

- verify requirement completeness
- verify blueprint alignment
- verify no scope expansion
- verify content quality and safety
- write QA results to task result files
- return only the QA file path


# 5. Skill Development Quality Standards

## 5.1 Requirement Completeness

QA must verify:

- the skill meets the stated user intent
- the task scope is adhered to
- all expected outputs are present
- any external action requirements are documented

---

## 5.2 Safety and Reliability

Skill behavior should be:

- deterministic where possible
- clear about failure modes
- safe for user interaction
- explicit when it needs confirmation

---

## 5.3 Traceability

Every work item must leave a trace in the command-center files.

If a task changes skill files, the corresponding planning and result records must exist.

---

# 6. OpenClaw Skill Planning Workflow

## 6.1 User Request

A user request is received by the Chat Agent.

The Chat Agent produces a planning brief and writes it to `/command-center/planning/planning-brief.md`.

---

## 6.2 Task Planning

The Task Planner converts the brief into executable tasks.

It reads from `/command-center/03-instruction.md` and updates:

- `/command-center/planning/task-breakdown.md`
- `/command-center/planning/execution-plan.md`
- `/command-center/planning/dependency-map.md`

---

## 6.3 Execution Sequence

Tasks should follow this lifecycle:

BACKLOG → ASSIGNED → IN_PROGRESS → SUBMITTED → TESTING → QA → READY_FOR_MAIN_REVIEW → DONE

Do not skip steps.

---

## 6.4 Final Verification

The Chat Agent must review:

- task results
- testing outcomes
- QA reports
- diffs and scope

Only the Chat Agent approves final completion.


# 7. Metadata and Naming

## 7.1 Skill Identity

Use consistent naming for OpenClaw skills:

- directory: `openclaw/skills/<skill-name>/`
- metadata file: `skill.md`
- step files: `references/stepNN_<name>.md`

---

## 7.2 Versioning

Capture version or review date in skill metadata where applicable.

Document major changes in command-center logs.


# 8. Final Principle

Do not build a skill without a plan.
Do not execute a task without a record.
Do not accept completion without testing and QA.
Do not let work drift outside the multi-agent file-based system.