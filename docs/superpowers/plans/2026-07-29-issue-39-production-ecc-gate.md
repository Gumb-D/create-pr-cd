# Issue #39 Production ECC Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block formal ECC generation for every non-`PRODUCTION` DU profile while preserving a deliberate, visibly isolated `NON_PRODUCTION_UAT` path for `PR_INPUT_READY` validation.

**Architecture:** Keep lifecycle enforcement in the official `scripts/create_pr.py` orchestration boundary, immediately after structured DU Profile resolution and before canonicalization or renderer invocation. Production mode keeps the current output contract. Explicit UAT mode reuses the same canonical and renderer path but writes to a marker-bearing run directory, renames renderer artefacts with the marker, and records run mode/profile status in the summary.

**Tech Stack:** Python 3, `unittest`, `unittest.mock`, `openpyxl`, existing DU Profile resolver and ECC renderer.

## Global Constraints

- Formal ECC generation is permitted only when `profile.status == "PRODUCTION"`.
- `PR_INPUT_READY` requires explicit `--non-production-uat` opt-in.
- Explicit UAT accepts only `PR_INPUT_READY` or `PRODUCTION`; all earlier/deprecated lifecycle states remain blocked.
- Gate decisions use structured profile status, never profile notes.
- UAT output directory, ECC/review filenames, and summary filename/content must contain `NON_PRODUCTION_UAT`.
- Production output naming and directory behaviour remain unchanged.
- Do not change canonical mapping, partition, duplicate, SOW, contract, or renderer selection rules.
- Do not commit generated Excel, review CSV, canonical workbook, or UAT output.

---

### Task 1: Add lifecycle-gate tests

**Files:**
- Modify: `tests/test_create_pr_entrypoint.py`

**Interfaces:**
- Consumes: `create_pr._resolve_run_mode(profile_status, non_production_uat)`
- Produces: executable expectations for blocked default mode, production mode, explicit UAT mode, and ineligible UAT status.

- [ ] **Step 1: Write failing unit tests**

Add tests asserting:

```python
self.assertRaisesRegex(CreatePrError, "not PRODUCTION")
self.assertEqual(_resolve_run_mode("PRODUCTION", False), "PRODUCTION")
self.assertEqual(_resolve_run_mode("PR_INPUT_READY", True), "NON_PRODUCTION_UAT")
```

Also assert that `DRAFT` with explicit UAT raises `PROFILE_NOT_UAT_ELIGIBLE`.

- [ ] **Step 2: Update the existing CLI regression test before implementation**

Change the current `PR_INPUT_READY` default CLI test to expect:

```text
return code = 1
error code = PROFILE_NOT_PRODUCTION
no ECC workbook
```

Add an explicit `--non-production-uat` CLI test expecting a successful marker-bearing summary and output directory.

- [ ] **Step 3: Run targeted tests and verify RED**

Run:

```bash
python -m unittest tests.test_create_pr_entrypoint -v
```

Expected: FAIL because `_resolve_run_mode` and `--non-production-uat` do not exist and the current CLI still generates ECC for `PR_INPUT_READY`.

- [ ] **Step 4: Commit tests**

```bash
git add tests/test_create_pr_entrypoint.py
git commit -m "test: define non-production ECC gate behavior"
```

---

### Task 2: Implement the structured production gate

**Files:**
- Modify: `scripts/create_pr.py`
- Test: `tests/test_create_pr_entrypoint.py`

**Interfaces:**
- Produces: `_resolve_run_mode(profile_status: str, non_production_uat: bool) -> str`
- Produces: `RUN_MODE_PRODUCTION = "PRODUCTION"`
- Produces: `RUN_MODE_NON_PRODUCTION_UAT = "NON_PRODUCTION_UAT"`

- [ ] **Step 1: Add the CLI flag**

Add:

```python
parser.add_argument(
    "--non-production-uat",
    action="store_true",
    help="Explicitly generate visibly isolated non-production UAT ECC output for PR_INPUT_READY/PRODUCTION profiles.",
)
```

- [ ] **Step 2: Implement minimal lifecycle resolution**

Rules:

```text
flag=false + PRODUCTION      -> PRODUCTION
flag=false + any other state -> PROFILE_NOT_PRODUCTION
flag=true  + PR_INPUT_READY  -> NON_PRODUCTION_UAT
flag=true  + PRODUCTION      -> NON_PRODUCTION_UAT
flag=true  + other state     -> PROFILE_NOT_UAT_ELIGIBLE
```

Errors must include `profile_status` and an actionable required step.

- [ ] **Step 3: Enforce the gate immediately after profile resolution**

Resolve the structured status from:

```python
resolution["profile"]["status"]
```

Call `_resolve_run_mode` before creating the output directory, building canonical records, or invoking the renderer.

- [ ] **Step 4: Run gate unit tests and verify GREEN**

Run:

```bash
python -m unittest tests.test_create_pr_entrypoint.TestCreatePrEntrypoint.test_pr_input_ready_default_mode_is_blocked -v
python -m unittest tests.test_create_pr_entrypoint.TestCreatePrEntrypoint.test_production_status_allows_formal_run_mode -v
python -m unittest tests.test_create_pr_entrypoint.TestCreatePrEntrypoint.test_explicit_uat_accepts_pr_input_ready -v
python -m unittest tests.test_create_pr_entrypoint.TestCreatePrEntrypoint.test_explicit_uat_rejects_draft_profile -v
```

Expected: PASS.

- [ ] **Step 5: Commit gate implementation**

```bash
git add scripts/create_pr.py tests/test_create_pr_entrypoint.py
git commit -m "fix: enforce DU profile production gate"
```

---

### Task 3: Isolate and label explicit UAT artefacts

**Files:**
- Modify: `scripts/create_pr.py`
- Test: `tests/test_create_pr_entrypoint.py`

**Interfaces:**
- Produces: `_resolve_output_directory(requested_output: Path, run_mode: str, run_id: str | None = None) -> tuple[Path, str | None]`
- Produces: `_mark_uat_artifacts(paths: list[Path]) -> list[Path]`

- [ ] **Step 1: Add failing tests for UAT output isolation**

Assert that explicit UAT:

```text
requested output / NON_PRODUCTION_UAT / <run_id>
```

is used, and every renderer-created filename receives `_NON_PRODUCTION_UAT` before its suffix.

Assert production mode returns the caller-supplied output directory unchanged.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m unittest tests.test_create_pr_entrypoint -v
```

Expected: FAIL because output isolation helpers do not yet exist.

- [ ] **Step 3: Implement deterministic output helpers**

Use a UTC run ID formatted as:

```text
YYYYMMDDTHHMMSSffffffZ
```

Do not mutate caller-supplied production output paths.

- [ ] **Step 4: Apply marker-bearing review and summary filenames**

UAT names:

```text
CANONICAL_REVIEW_REQUIRED_<SCOPE>_NON_PRODUCTION_UAT.csv
CREATE_PR_SUMMARY_<SCOPE>_NON_PRODUCTION_UAT.json
```

Production names remain unchanged.

- [ ] **Step 5: Rename all renderer-created UAT files before summary collection**

Rename every newly created renderer artefact by inserting:

```text
_NON_PRODUCTION_UAT
```

before the extension. Preserve the suffix and fail if a target collision exists.

- [ ] **Step 6: Add summary traceability fields**

Include:

```text
run_mode
profile_status
non_production_uat
production_ecc_allowed
requested_output
output_root
run_id
```

For UAT, `production_ecc_allowed` must be `false`; for formal production it must be `true`.

- [ ] **Step 7: Run targeted tests and verify GREEN**

Run:

```bash
python -m unittest tests.test_create_pr_entrypoint -v
```

Expected: PASS.

- [ ] **Step 8: Commit UAT isolation**

```bash
git add scripts/create_pr.py tests/test_create_pr_entrypoint.py
git commit -m "feat: isolate explicit non-production UAT output"
```

---

### Task 4: Verify regression safety and publish Draft PR

**Files:**
- Modify only if required by test evidence: `scripts/create_pr.py`, `tests/test_create_pr_entrypoint.py`

- [ ] **Step 1: Run targeted tests**

```bash
python -m unittest tests.test_create_pr_entrypoint -v
```

- [ ] **Step 2: Run the full suite**

```bash
python -m unittest discover -s tests -v
```

- [ ] **Step 3: Run syntax and whitespace checks**

```bash
python -m py_compile scripts/create_pr.py tests/test_create_pr_entrypoint.py
git diff --check
```

- [ ] **Step 4: Review scope**

Confirm:

```text
No DU Profile lifecycle status changed
No production mappings changed
No renderer business rules changed
No generated output tracked
```

- [ ] **Step 5: Push branch and open Draft PR**

PR title:

```text
fix(gate): block production ECC for non-PRODUCTION DU profiles
```

PR body must link `Fixes #39`, list RED/GREEN evidence, and state that `PR_INPUT_READY` now requires explicit `--non-production-uat`.
