# DU Profile Identity Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce `iEPMS Project + DU Model` as the authoritative DU profile identity through a naming standard, a machine-readable registry, and deterministic regression tests.

**Architecture:** Keep runtime and profile-loading behavior unchanged. Add one JSON-compatible YAML registry that records every existing profile identity and exact duplicate-review exceptions, then add a focused unittest module that compares the registry with all files under `config/du_profiles/`. The human-readable standard explains the same rules and remains aligned with Issue #28.

**Tech Stack:** Python 3 standard library (`json`, `unittest`, `pathlib`, `copy`, `collections`), JSON-compatible YAML configuration, Markdown documentation.

## Global Constraints

- Canonical identity is `(project_key, du_model_id)`.
- View ID, View name, four-layer Header Fingerprint, and Header Hash remain source-layout evidence, not business identity.
- Do not rename any existing profile.
- Do not change any profile lifecycle status, mapping, approved Header Hash, runtime behavior, ECC gate, or production setting.
- `tx_mini_pr_v1` must remain `LEGACY_ACCEPTED`.
- `tx_mini_pr_v1` and `zte_tx_mini_pr_v1` must remain separate identities.
- The two CD Consolidation DRAFT profiles may coexist only as the exact profile set recorded under `CONSOLIDATION_REVIEW_REQUIRED`.
- No raw customer export or local-only evidence may be committed.

---

## File Structure

- Create `config/registries/mw_du_profile_identity_registry.yaml`: authoritative profile-to-identity governance registry and exact duplicate-identity review set.
- Create `tests/test_du_profile_identity_governance.py`: reusable validation helper plus positive and negative regression tests.
- Create `docs/MW_DU_Profile_Naming_Standard.md`: business-readable naming and View-handling standard.
- Keep `docs/superpowers/specs/2026-07-13-du-profile-identity-governance-design.md` unchanged except for implementation-status updates after delivery.

### Task 1: Add failing governance tests

**Files:**
- Create: `tests/test_du_profile_identity_governance.py`
- Test: `tests/test_du_profile_identity_governance.py`

**Interfaces:**
- Consumes: JSON-compatible profile files from `config/du_profiles/*.yaml`.
- Produces: `validate_identity_governance(profiles: dict[str, dict], registry: dict) -> list[str]`, returning deterministic error strings.

- [ ] **Step 1: Create the validation helper and tests before the registry exists**

Implement these constants and helpers:

```python
ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "config" / "du_profiles"
REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"


def load_json_mapping(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def identity_key(profile: dict) -> str:
    identity = profile["identity"]
    model_ids = identity["accepted_du_model_ids"]
    if len(model_ids) != 1:
        raise AssertionError(f"{profile['profile_id']} must register exactly one DU model ID")
    return f"{identity['project_key']}::{model_ids[0]}"
```

Implement `validate_identity_governance()` so it returns these exact errors when applicable:

```text
UNREGISTERED_DU_PROFILE:<profile_id>
STALE_PROFILE_REGISTRY_RECORD:<profile_id>
PROFILE_IDENTITY_MISMATCH:<profile_id>
PROFILE_STATUS_MISMATCH:<profile_id>
DUPLICATE_PROFILE_IDENTITY:<identity_key>
DUPLICATE_IDENTITY_SET_MISMATCH:<identity_key>
NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:<profile_id>
LEGACY_PROFILE_WITHOUT_REASON:<profile_id>
CONSOLIDATION_REVIEW_WITHOUT_REASON:<profile_id>
```

The validator must:

```python
allowed_name_statuses = {
    "STANDARD",
    "LEGACY_ACCEPTED",
    "CONSOLIDATION_REVIEW_REQUIRED",
}
```

1. Require a one-to-one set match between profile IDs and registry profile records.
2. Compare `project_key`, one DU model name, one DU model ID, `identity_key`, `accepted_view_ids`, and lifecycle `profile_status`.
3. Require `profile_id == canonical_profile_id` for `STANDARD`.
4. Require nonblank `reason` for `LEGACY_ACCEPTED` and `CONSOLIDATION_REVIEW_REQUIRED`.
5. Group by `identity_key`; unique groups pass without review.
6. For duplicate groups, require an `identity_reviews` record whose `permitted_profile_ids` exactly equals the current duplicate set and whose status is `CONSOLIDATION_REVIEW_REQUIRED`.

Add positive tests for the committed registry and negative tests using deep copies:

```python
def test_unregistered_profile_fails(self): ...
def test_unapproved_duplicate_identity_fails(self): ...
def test_third_cd_consolidation_profile_fails(self): ...
def test_standard_record_with_noncanonical_id_fails(self): ...
def test_legacy_record_without_reason_fails(self): ...
def test_tx_mini_profiles_are_distinct_identities(self): ...
def test_profile_lifecycle_statuses_are_unchanged(self): ...
```

- [ ] **Step 2: Run the focused test and confirm the expected red state**

Run:

```bash
python -m unittest tests.test_du_profile_identity_governance -v
```

Expected result: failure because `config/registries/mw_du_profile_identity_registry.yaml` does not exist.

- [ ] **Step 3: Commit the red test**

```bash
git add tests/test_du_profile_identity_governance.py
git commit -m "test(du): define profile identity governance"
```

### Task 2: Add the machine-readable identity registry

**Files:**
- Create: `config/registries/mw_du_profile_identity_registry.yaml`
- Test: `tests/test_du_profile_identity_governance.py`

**Interfaces:**
- Consumes: exact identity metadata already present in each DU profile.
- Produces: registry keys `schema_version`, `identity_rule`, `project_slugs`, `profiles`, and `identity_reviews`.

- [ ] **Step 1: Create JSON-compatible registry content**

Use this top-level structure:

```json
{
  "schema_version": "1.0",
  "identity_rule": "iEPMS Project + DU Model",
  "identity_key_fields": ["project_key", "du_model_id"],
  "project_slugs": {
    "Malaysia_CelcomDigi_Project": "celcomdigi",
    "CelcomDigi_MW": "mw"
  },
  "profiles": [],
  "identity_reviews": []
}
```

Register all 10 existing profiles with exact values from their profile files.

Use these naming decisions:

```text
STANDARD
- celcomdigi_bau_2023_pr_v1
- celcomdigi_bau_2024_pr_v1
- celcomdigi_usp_pr_v1
- mw_eos_swap_pr_v1

LEGACY_ACCEPTED
- tx_mini_pr_v1
- tx_rollout_2023_pr_v1
- jendela_tx_migration_pr_v1
- zte_tx_mini_pr_v1

CONSOLIDATION_REVIEW_REQUIRED
- cd_consolidation_2023_decom_pr_v1
- cd_consolidation_2023_rollout_pr_v1
```

Canonical IDs for nonstandard families:

```text
tx_mini_pr_v1                       -> celcomdigi_tx_mini_project_pr_v1
tx_rollout_2023_pr_v1               -> celcomdigi_2023_tx_rollout_pr_v1
jendela_tx_migration_pr_v1          -> celcomdigi_jendela_tx_migration_pr_v1
zte_tx_mini_pr_v1                   -> mw_zte_tx_mini_pr_v1
cd_consolidation_2023_*_pr_v1       -> celcomdigi_cd_consolidation_2023_pr_v1
```

Each record must include:

```json
{
  "profile_id": "...",
  "canonical_profile_id": "...",
  "project_key": "...",
  "project_slug": "...",
  "du_model_name": "...",
  "du_model_id": "...",
  "identity_key": "<project_key>::<du_model_id>",
  "profile_status": "DRAFT or PR_INPUT_READY",
  "name_status": "STANDARD or LEGACY_ACCEPTED or CONSOLIDATION_REVIEW_REQUIRED",
  "accepted_view_ids": ["..."],
  "reason": "... or null"
}
```

The CD Consolidation review must be exact:

```json
{
  "identity_key": "Malaysia_CelcomDigi_Project::8359047522524182050",
  "status": "CONSOLIDATION_REVIEW_REQUIRED",
  "permitted_profile_ids": [
    "cd_consolidation_2023_decom_pr_v1",
    "cd_consolidation_2023_rollout_pr_v1"
  ],
  "reason": "Both DRAFT profiles represent different export views for the same Project + DU Model and require business/technical consolidation review before onboarding."
}
```

- [ ] **Step 2: Run the focused governance tests**

Run:

```bash
python -m unittest tests.test_du_profile_identity_governance -v
```

Expected result: all governance tests pass.

- [ ] **Step 3: Commit the registry**

```bash
git add config/registries/mw_du_profile_identity_registry.yaml tests/test_du_profile_identity_governance.py
git commit -m "feat(du): register profile identities"
```

### Task 3: Add the human-readable naming standard

**Files:**
- Create: `docs/MW_DU_Profile_Naming_Standard.md`

**Interfaces:**
- Consumes: the approved design and registry terminology.
- Produces: the authoritative human-readable standard for Issue #21 onboarding.

- [ ] **Step 1: Write the standard**

The document must contain these sections and decisions:

```markdown
# MW DU Profile Naming and Identity Standard

## Authoritative identity
DU Profile Identity = iEPMS Project + DU Model
Canonical machine key = (project_key, du_model_id)

## Profile ID format
<project_slug>_<du_model_slug>_pr_v<major>

## View handling
Views and Header Hashes are accepted source-layout evidence within a profile family; they are not identity.

## Separate-profile criteria
Different Project, different DU Model, materially different PR semantics, incompatible field semantics, or layouts that cannot be validated safely within one family.

## Existing-profile decisions
Legacy accepted names, separate TX Mini identities, standard-compatible names, and CD Consolidation review status.

## Change control
Registry update + tests + human justification required; no silent duplicate family creation.
```

State explicitly that naming governance does not grant `PRODUCTION` status or enable ECC output.

- [ ] **Step 2: Check terminology against the registry and design**

Run:

```bash
git diff --check
```

Expected result: no whitespace errors.

- [ ] **Step 3: Commit the standard**

```bash
git add docs/MW_DU_Profile_Naming_Standard.md
git commit -m "docs(du): standardize profile identity naming"
```

### Task 4: Complete regression verification and open the Draft PR

**Files:**
- Verify: `config/registries/mw_du_profile_identity_registry.yaml`
- Verify: `tests/test_du_profile_identity_governance.py`
- Verify: `docs/MW_DU_Profile_Naming_Standard.md`
- Verify: `docs/superpowers/specs/2026-07-13-du-profile-identity-governance-design.md`
- Verify: `docs/superpowers/plans/2026-07-13-du-profile-identity-governance.md`

**Interfaces:**
- Consumes: all deliverables from Tasks 1-3.
- Produces: a reviewable Draft PR linked to Issue #28.

- [ ] **Step 1: Run focused and full verification**

```bash
python -m unittest tests.test_du_profile_identity_governance -v
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
python -m compileall -q scripts
git diff --check
```

Expected result: every command exits 0.

- [ ] **Step 2: Confirm the branch scope**

```bash
git diff --name-only origin/main...HEAD
```

Expected files only:

```text
config/registries/mw_du_profile_identity_registry.yaml
docs/MW_DU_Profile_Naming_Standard.md
docs/superpowers/plans/2026-07-13-du-profile-identity-governance.md
docs/superpowers/specs/2026-07-13-du-profile-identity-governance-design.md
tests/test_du_profile_identity_governance.py
```

- [ ] **Step 3: Open a Draft PR**

Title:

```text
docs(du): enforce profile identity by project and DU model
```

Body must summarize:

```text
- fixes #28
- adds naming standard and machine-readable registry
- preserves all existing IDs and lifecycle states
- records exact CD Consolidation duplicate-review set
- adds positive and negative governance tests
- does not change runtime mappings, ECC behavior, or production status
```

- [ ] **Step 4: Review the PR diff before requesting merge**

Inspect every changed file and verify the PR contains no generated discovery packet refresh, profile mutation, raw customer data, or runtime code change.
