# CD Consolidation 2023 Profile Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace two View-based CD consolidation DRAFT profiles with one deterministic Project + DU Model profile family while preserving both layouts as unapproved discovery evidence.

**Architecture:** One canonical profile owns the Project + DU Model identity. Its `layout_variants` section preserves Decom and Rollout View IDs, observed Header Hashes, and exact four-layer candidates; the ordinary field mapping remains fail-closed and unapproved. Registry and governance outputs contain one profile route, while discovery inventory remains one row per export View.

**Tech Stack:** Python 3.11, JSON-compatible YAML profile files, `unittest`, GitHub Actions.

## Global Constraints

- Profile routing remains Project + DU Model only.
- View Name and View ID are not profile identity.
- Profile status remains `DRAFT`.
- `approved_header_hashes` remains empty.
- All mapping candidates remain `UNVERIFIED`.
- Do not enable TSS, TI, Backoffice, or Operation ECC generation.
- Do not change existing SOW, subcontractor, contract, duplicate, Cancel/Drop, SM, Huawei-owned, or renderer rules.
- Preserve both View IDs, both observed Header Hashes, and both sets of four-layer evidence.
- Backoffice / Operation business logic remains under Issue #34.

---

### Task 1: Lock canonical identity with failing governance tests

**Files:**
- Modify: `tests/test_du_profile_identity_governance.py`
- Modify: `tests/du_profile_loader_legacy_tests.py`
- Create: `tests/test_cd_consolidation_profile_family.py`

**Interfaces:**
- Consumes: profile files under `config/du_profiles` and registry `config/registries/mw_du_profile_identity_registry.yaml`.
- Produces: tests requiring exactly one canonical profile, two layout variants, empty approved hashes, and DRAFT lifecycle.

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
CANONICAL_PROFILE_ID = "celcomdigi_cd_consolidation_2023_pr_v1"
OLD_PROFILE_IDS = {
    "cd_consolidation_2023_decom_pr_v1",
    "cd_consolidation_2023_rollout_pr_v1",
}


def test_registry_has_one_cd_consolidation_identity_route():
    records = [
        row for row in registry["profiles"]
        if row["identity_key"] == "Malaysia_CelcomDigi_Project::8359047522524182050"
    ]
    assert [row["profile_id"] for row in records] == [CANONICAL_PROFILE_ID]
    assert records[0]["name_status"] == "STANDARD"
    assert not registry.get("identity_reviews")


def test_profile_preserves_both_layouts_and_remains_fail_closed():
    assert profile["status"] == "DRAFT"
    assert profile["export_structure"]["approved_header_hashes"] == []
    variants = {row["variant_id"]: row for row in profile["layout_variants"]}
    assert set(variants) == {"decom", "rollout"}
    assert variants["decom"]["view_id"] == "702960351133798763"
    assert variants["rollout"]["view_id"] == "8359047522524230651"
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m unittest \
  tests/test_cd_consolidation_profile_family.py \
  tests/test_du_profile_identity_governance.py \
  tests/du_profile_loader_legacy_tests.py -v
```

Expected: FAIL because the canonical profile does not exist and two registry records remain.

- [ ] **Step 3: Commit RED tests**

```bash
git add tests/test_cd_consolidation_profile_family.py tests/test_du_profile_identity_governance.py tests/du_profile_loader_legacy_tests.py
git commit -m "test(identity): require one CD consolidation profile family"
```

---

### Task 2: Create the canonical fail-closed profile and registry route

**Files:**
- Create: `config/du_profiles/celcomdigi_cd_consolidation_2023_pr_v1.yaml`
- Delete: `config/du_profiles/cd_consolidation_2023_decom_pr_v1.yaml`
- Delete: `config/du_profiles/cd_consolidation_2023_rollout_pr_v1.yaml`
- Modify: `config/registries/mw_du_profile_identity_registry.yaml`

**Interfaces:**
- Consumes: exact discovery evidence from the two old profile files.
- Produces: one canonical profile with `layout_variants: list[dict]` and one registry route.

- [ ] **Step 1: Create the canonical profile**

Use this identity and safety envelope:

```json
{
  "profile_id": "celcomdigi_cd_consolidation_2023_pr_v1",
  "profile_version": "0.1.0",
  "mapping_version": "discovery-2026-08-05-cd-consolidation-2023-family-v1",
  "status": "DRAFT",
  "identity": {
    "project_key": "Malaysia_CelcomDigi_Project",
    "accepted_du_models": ["CD consolidation 2023"],
    "accepted_du_model_ids": ["8359047522524182050"],
    "accepted_view_ids": ["702960351133798763", "8359047522524230651"]
  },
  "export_structure": {
    "sheet_selector": null,
    "header_rows": [0, 1, 2, 3],
    "header_hash_policy": "strict",
    "observed_header_hashes": [
      "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16",
      "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1"
    ],
    "approved_header_hashes": []
  }
}
```

Add `layout_variants` entries for `decom` and `rollout`, each preserving its View ID, observed Header Hash, and field candidates copied exactly from the corresponding old profile.

Keep the top-level `field_mapping` fail-closed: required Backoffice / Operation fields unresolved, candidates unverified, and no approved layout selected.

- [ ] **Step 2: Replace registry records**

Replace both duplicate records and the `identity_reviews` exception with:

```json
{
  "profile_id": "celcomdigi_cd_consolidation_2023_pr_v1",
  "canonical_profile_id": "celcomdigi_cd_consolidation_2023_pr_v1",
  "project_key": "Malaysia_CelcomDigi_Project",
  "project_slug": "celcomdigi",
  "du_model_name": "CD consolidation 2023",
  "du_model_id": "8359047522524182050",
  "identity_key": "Malaysia_CelcomDigi_Project::8359047522524182050",
  "profile_status": "DRAFT",
  "name_status": "STANDARD",
  "accepted_view_ids": ["702960351133798763", "8359047522524230651"],
  "reason": null
}
```

Set `identity_reviews` to an empty list or remove it if all consumers accept omission.

- [ ] **Step 3: Delete old profile files**

Delete both View-based profile files only after their evidence exists in the canonical profile.

- [ ] **Step 4: Run targeted tests to verify GREEN**

Run the Task 1 command. Expected: PASS.

- [ ] **Step 5: Commit profile consolidation**

```bash
git add config/du_profiles config/registries/mw_du_profile_identity_registry.yaml
git commit -m "fix(identity): consolidate CD consolidation profile family"
```

---

### Task 3: Update discovery and governance outputs

**Files:**
- Modify: `docs/MW_DU_Discovery_Inventory.md`
- Modify: `docs/MW_DU_Profile_Naming_Standard.md`
- Modify generated governance documents containing either old Profile ID.
- Modify tests that assert two CD consolidation profiles.

**Interfaces:**
- Consumes: canonical profile and registry from Task 2.
- Produces: governance artifacts consistently reporting one profile family and two source Views.

- [ ] **Step 1: Update tests first**

Update review/readiness/discovery tests so they require:

```python
assert set(cd_rows["Profile ID"]) == {"celcomdigi_cd_consolidation_2023_pr_v1"}
assert set(cd_rows["View ID"]) == {
    "702960351133798763",
    "8359047522524230651",
}
```

Replace tests named for separate Decom/Rollout profiles with one family test that checks both layout evidence sets.

- [ ] **Step 2: Run the affected governance tests to verify RED**

Run:

```bash
python -m unittest \
  tests/test_missing_field_bridge_review.py \
  tests/test_profile_review_matrix.py \
  tests/test_profile_readiness_review.py \
  tests/test_du_discovery_registry.py \
  tests/test_discovery_packet_consistency.py \
  tests/test_discovery_packet_header_compatibility.py \
  tests/test_unresolved_skill_field_review.py -v
```

Expected: FAIL while generated documents still contain old Profile IDs.

- [ ] **Step 3: Refresh or manually update generated governance outputs**

Run the existing refresh builders when local profiler prerequisites are available. Otherwise update only the affected CD consolidation rows while preserving all unrelated generated content byte-for-byte.

The discovery inventory must keep two rows, one per View, but both rows must use `celcomdigi_cd_consolidation_2023_pr_v1`.

The naming standard must replace `CONSOLIDATION_REVIEW_REQUIRED` with the approved consolidation decision and state that both layouts are owned by one canonical DRAFT profile.

- [ ] **Step 4: Run affected tests to verify GREEN**

Run the Step 2 command. Expected: PASS, except local-only discovery tests may skip or reproduce their documented fixture prerequisite.

- [ ] **Step 5: Commit governance refresh**

```bash
git add docs tests scripts
git commit -m "docs(identity): align governance with CD profile family"
```

---

### Task 4: Verify fail-closed behaviour and broad regression

**Files:**
- Modify only if a failing regression identifies a real consolidation defect.
- Temporary verification workflow may be added and removed on the feature branch.

**Interfaces:**
- Consumes: all preceding tasks.
- Produces: verification evidence for PR #59 and Issue #61.

- [ ] **Step 1: Run profile loader and resolver regression**

```bash
python -m unittest \
  tests/test_du_profile_loader.py \
  tests/test_du_profile_identity_governance.py \
  tests/test_project_du_model_source_routing.py \
  tests/test_all_du_v2_manifest_completeness.py -v
```

Expected: PASS. The canonical profile remains blocked because it is DRAFT and has no approved Header Hash.

- [ ] **Step 2: Run broad repository regression**

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all repository-supported tests pass. Document only failures reproduced unchanged on `main` or tests requiring ignored local customer artifacts.

- [ ] **Step 3: Inspect final diff**

Confirm:

- one canonical CD profile file exists;
- both old files are deleted;
- exactly one registry route exists;
- no lifecycle promotion;
- no approved Header Hash;
- no business-rule or renderer changes;
- temporary CI files are removed.

- [ ] **Step 4: Update Issue #61 and PR #59**

Record business decision A, changed files, test results, remaining Issue #34 scope, and final head SHA. Keep PR unmerged pending review.

- [ ] **Step 5: Commit any final documentation-only cleanup**

```bash
git add docs
 git commit -m "docs: record CD profile family verification"
```
