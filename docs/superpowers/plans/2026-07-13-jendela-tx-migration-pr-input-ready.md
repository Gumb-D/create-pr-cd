# Jendela TX Migration PR Input Ready Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `jendela_tx_migration_pr_v1` from discovery-only `DRAFT` to non-production `PR_INPUT_READY` using one approved Header Hash, seven exact four-layer mappings, profile-specific fail-closed tests, and synchronized governance artifacts.

**Architecture:** Reuse the existing profile-driven canonical adapter and lifecycle guards. No runtime generator code changes are expected: the implementation updates the Jendela profile contract, adds adapter and lifecycle tests around existing interfaces, refreshes the tracked governance packet, and keeps ECC blocked because the profile remains below `PRODUCTION`.

**Tech Stack:** Python 3.11, `unittest`, JSON-compatible YAML files, existing MW DU refresh scripts, PowerShell, Git/GitHub.

## Global Constraints

- Preserve profile ID `jendela_tx_migration_pr_v1`; no rename migration.
- Preserve identity `Malaysia_CelcomDigi_Project::4972593269368006257` and accepted View ID `4026888666764910245`.
- Set `profile_version` to `0.2.0`.
- Set `mapping_version` to `approved-2026-07-13-jendela-tx-migration-v1`.
- Set lifecycle status to `PR_INPUT_READY`, never `PRODUCTION`.
- Approve Header Hash `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3` under strict validation.
- Approve only `site_code`, `tx_sow_raw`, `region`, `subcontractor_tss`, `subcontractor_ti`, `existing_tss_pr_status`, and `existing_ti_pr_status`.
- Keep all other existing mappings `UNVERIFIED`.
- Keep `subcontractor_tss.required` as `false`; TSS-scope validation remains mandatory through `SCOPE_REQUIRED_FIELDS`.
- Use `normalize_pr_reference_status` for both existing-PR fields.
- Do not change generator logic, ECC templates, PR models, SOW rules, or another DU profile.
- Do not commit raw iEPMS exports, anything under `Info/reference`, or generated local review workbooks under `output/`.
- Retain only Jendela-related tracked refresh output plus mandatory authoritative summary/count changes.

---

## File Structure

### Hand-edited source-of-truth files

- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml` — approved lifecycle, Header Hash, mappings, and safety notes.
- Modify: `config/registries/mw_du_profile_identity_registry.yaml` — lifecycle status only for the existing Jendela identity record.
- Modify: `tests/test_du_profile_loader.py` — profile contract and approved TSS mapping coverage.
- Modify: `tests/test_du_profile_identity_governance.py` — locked lifecycle expectation.
- Modify: `tests/test_du_export_adapter.py` — exact mapping, normalization, scope, Header Hash, and non-production tests.
- Modify: `tests/test_unresolved_skill_field_review.py` — approved Jendela mapping review expectations.
- Modify: `tests/test_missing_field_bridge_review.py` — no cross-model bridge after local approved PR fields.
- Modify: `tests/test_profile_readiness_review.py` — only lifecycle and optional-review blockers remain.
- Modify: `tests/test_profile_action_queue.py` — no missing-required or Header Hash action remains.
- Modify: `tests/test_profile_transition_review.py` — `PR_INPUT_READY` eligible while `PRODUCTION` remains denied.
- Modify: `tests/test_profile_rollback_readiness.py` — approved Jendela rollback baseline and a different still-draft negative control.

### Generated authoritative registries

- Modify: `config/registries/mw_du_export_coverage_review.yaml`
- Modify: `config/registries/mw_du_missing_field_bridge_review.yaml`
- Modify: `config/registries/mw_du_model_discovery_registry.yaml`
- Modify: `config/registries/mw_du_profile_action_queue.yaml`
- Modify: `config/registries/mw_du_profile_deprecation_review.yaml`
- Modify: `config/registries/mw_du_profile_readiness_review.yaml`
- Modify: `config/registries/mw_du_profile_review_matrix.yaml`
- Modify: `config/registries/mw_du_profile_rollback_readiness.yaml`
- Modify: `config/registries/mw_du_profile_traceability_audit.yaml`
- Modify: `config/registries/mw_du_profile_transition_review.yaml`
- Modify: `config/registries/mw_du_unresolved_skill_field_review.yaml`

### Generated authoritative documentation

- Modify: `docs/MW_DU_All_DU_Discovery_Mapping_Review.md`
- Modify: `docs/MW_DU_Export_Coverage_Review.md`
- Modify: `docs/MW_DU_Missing_Field_Bridge_Review.md`
- Modify: `docs/MW_DU_Profile_Action_Queue.md`
- Modify: `docs/MW_DU_Profile_Deprecation_Review.md`
- Modify: `docs/MW_DU_Profile_Readiness_Review.md`
- Modify: `docs/MW_DU_Profile_Review_Matrix.md`
- Modify: `docs/MW_DU_Profile_Rollback_Readiness.md`
- Modify: `docs/MW_DU_Profile_Traceability_Audit.md`
- Modify: `docs/MW_DU_Profile_Transition_Review.md`
- Modify: `docs/MW_DU_Unresolved_Skill_Field_Review.md`

---

### Task 1: Lock and implement the Jendela profile contract

**Files:**
- Modify: `tests/test_du_profile_loader.py`
- Modify: `tests/test_du_profile_identity_governance.py`
- Modify: `tests/test_profile_rollback_readiness.py`
- Modify: `config/du_profiles/jendela_tx_migration_pr_v1.yaml`
- Modify: `config/registries/mw_du_profile_identity_registry.yaml`

**Interfaces:**
- Consumes: `load_du_profile(path: Path) -> dict`, `evaluate_rollback_readiness(profile: dict, prior_profile: dict | None) -> dict`.
- Produces: a loadable Jendela `PR_INPUT_READY` profile with exact approved mappings and a matching identity-registry lifecycle record.

- [ ] **Step 1: Update the loader tests first**

In `test_all_pr_input_ready_profiles_have_approved_subcontractor_tss_and_remain_non_production`, add:

```python
"jendela_tx_migration_pr_v1.yaml": ("docata|ZDCSZ640307", "SubCon - TSS"),
```

Replace `test_draft_jendela_profile_loads_with_antenna_and_sow_candidates` with:

```python
def test_pr_input_ready_jendela_profile_loads_with_human_approved_pr_critical_mappings(self):
    profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
    self.assertEqual(profile["status"], "PR_INPUT_READY")
    self.assertEqual(profile["profile_version"], "0.2.0")
    self.assertEqual(profile["mapping_version"], "approved-2026-07-13-jendela-tx-migration-v1")
    self.assertEqual(profile["identity"]["accepted_du_models"], ["Jendela TX Migration"])
    self.assertEqual(profile["identity"]["accepted_du_model_ids"], ["4972593269368006257"])
    self.assertEqual(profile["identity"]["accepted_view_ids"], ["4026888666764910245"])
    self.assertEqual(
        profile["export_structure"]["approved_header_hashes"],
        ["904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3"],
    )
    approved = {
        field_name
        for field_name, config in profile["field_mapping"].items()
        if any(candidate.get("mapping_status") == "APPROVED" for candidate in config.get("source_candidates", []))
    }
    self.assertEqual(
        approved,
        {
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_tss",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        },
    )
    self.assertFalse(profile["field_mapping"]["subcontractor_tss"]["required"])
    self.assertEqual(
        profile["field_mapping"]["existing_tss_pr_status"]["transforms"],
        ["normalize_pr_reference_status"],
    )
    self.assertEqual(
        profile["field_mapping"]["existing_ti_pr_status"]["transforms"],
        ["normalize_pr_reference_status"],
    )
    self.assertNotEqual(profile["status"], "PRODUCTION")
```

- [ ] **Step 2: Lock the identity-governance lifecycle expectation**

In `test_profile_lifecycle_statuses_are_unchanged`, change only:

```python
"jendela_tx_migration_pr_v1": "PR_INPUT_READY",
```

Keep the final assertion:

```python
self.assertNotIn("PRODUCTION", actual.values())
```

- [ ] **Step 3: Update rollback tests for the new lifecycle**

Change the still-draft negative control to `celcomdigi_bau_2023_pr_v1.yaml`:

```python
def test_current_draft_profile_stays_blocked_without_approved_baseline(self):
    profile = load_du_profile(ROOT / "config" / "du_profiles" / "celcomdigi_bau_2023_pr_v1.yaml")
    entry = evaluate_rollback_readiness(profile, None)
    self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
    self.assertIn("NO_APPROVED_HEADER_HASH_BASELINE", entry["blockers"])
    self.assertIn("PROFILE_NOT_RELEASED", entry["blockers"])
```

Add:

```python
def test_jendela_records_rollback_baseline_after_pr_input_ready(self):
    profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
    entry = evaluate_rollback_readiness(profile, None)
    self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BASELINE_RECORDED")
    self.assertEqual(entry["rollback_target_profile_id"], "jendela_tx_migration_pr_v1")
    self.assertEqual(entry["rollback_target_profile_version"], "0.2.0")
    self.assertEqual(
        entry["rollback_target_header_hashes"],
        ["904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3"],
    )
```

- [ ] **Step 4: Run the focused tests and confirm the pre-change failure**

Run:

```powershell
python -m unittest discover -s tests -p "test_du_profile_loader.py" -v
python -m unittest discover -s tests -p "test_du_profile_identity_governance.py" -v
python -m unittest discover -s tests -p "test_profile_rollback_readiness.py" -v
```

Expected: failures showing Jendela is still `DRAFT`, has no approved Header Hash, has no approved TSS mapping, and the identity registry still records `DRAFT`.

- [ ] **Step 5: Update the Jendela profile metadata and mappings**

Set the profile header to:

```json
{
  "profile_id": "jendela_tx_migration_pr_v1",
  "profile_version": "0.2.0",
  "mapping_version": "approved-2026-07-13-jendela-tx-migration-v1",
  "status": "PR_INPUT_READY"
}
```

Set:

```json
"approved_header_hashes": [
  "904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3"
]
```

Use these exact approved field definitions:

```json
"site_code": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "site|fix00012|4972593269368006257|4026888666764910245",
      "wbs_stage": "Site Basic Info",
      "task_name": "Site Basic Info",
      "display_header": "customer site code"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["trim", "uppercase"]
},
"tx_sow_raw": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "docata|ZDCSZ00815532",
      "wbs_stage": "Planner",
      "task_name": "Microwave",
      "display_header": "Tx SOW"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["trim"]
},
"region": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "site|region_name",
      "wbs_stage": "Site Basic Info",
      "task_name": "Site Basic Info",
      "display_header": "region"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["trim"]
},
"subcontractor_tss": {
  "required": false,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "docata|ZDCSZ640307",
      "wbs_stage": "RPM",
      "task_name": "SubCon - TSS",
      "display_header": "SubCon - TSS"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["trim"]
},
"subcontractor_ti": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "docata|ZDCSZ640242",
      "wbs_stage": "RPM",
      "task_name": "Wireless RAN",
      "display_header": "SubCon - TI"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["trim"]
},
"existing_tss_pr_status": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "docata|ZDCSZ641766",
      "wbs_stage": "PR Team",
      "task_name": "Wireless RAN",
      "display_header": "Subcon PR - TSS"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["normalize_pr_reference_status"]
},
"existing_ti_pr_status": {
  "required": true,
  "source_candidates": [{
    "fingerprint": {
      "field_code": "docata|ZDCSZ641765",
      "wbs_stage": "PR team",
      "task_name": "Wireless RAN",
      "display_header": "Subcon PR - TI"
    },
    "mapping_status": "APPROVED"
  }],
  "transforms": ["normalize_pr_reference_status"]
}
```

Do not change any optional candidate's `mapping_status`.

Replace the profile notes with statements covering the seven approved mappings, strict Header Hash behavior, duplicate-prevention normalization, scope-specific TSS enforcement, non-production validation, and permanent ECC blocking until a separate `PRODUCTION` approval.

- [ ] **Step 6: Update the identity registry lifecycle record**

For the existing `jendela_tx_migration_pr_v1` record in `config/registries/mw_du_profile_identity_registry.yaml`, change only:

```json
"profile_status": "PR_INPUT_READY"
```

Do not change `canonical_profile_id`, Project, DU Model, identity key, View IDs, name status, or legacy reason.

- [ ] **Step 7: Re-run the focused tests**

Run the same three commands from Step 4.

Expected: all loader, identity-governance, and rollback tests pass; no profile is `PRODUCTION`.

- [ ] **Step 8: Commit the profile contract**

```powershell
git add config/du_profiles/jendela_tx_migration_pr_v1.yaml `
        config/registries/mw_du_profile_identity_registry.yaml `
        tests/test_du_profile_loader.py `
        tests/test_du_profile_identity_governance.py `
        tests/test_profile_rollback_readiness.py
git commit -m "feat(du): promote Jendela profile to PR input ready"
```

---

### Task 2: Add Jendela adapter and fail-closed tests

**Files:**
- Modify: `tests/test_du_export_adapter.py`

**Interfaces:**
- Consumes: `load_du_profile`, `resolve_profile_field_mappings`, `build_canonical_site_record`, `evaluate_record`, `fingerprint_key`, `PR_STATUS_EXISTS`, `PR_STATUS_NONE`, `PR_STATUS_NOT_REQUIRED`.
- Produces: a dedicated `TestJendelaApprovedProfileAdapter` regression suite without changing adapter runtime code.

- [ ] **Step 1: Add the dedicated test class**

Append this class after the other approved-profile adapter suites:

```python
class TestJendelaApprovedProfileAdapter(unittest.TestCase):
    PROFILE_PATH = ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"

    @classmethod
    def setUpClass(cls):
        cls.profile = load_du_profile(cls.PROFILE_PATH)

    def _inventory_from_profile(self, *, include_alternates=False, missing_fields=None):
        missing_fields = set(missing_fields or [])
        columns = []
        for field_name, config in self.profile["field_mapping"].items():
            if field_name in missing_fields:
                continue
            for candidate in config.get("source_candidates", []):
                columns.append(
                    {
                        "fingerprint": candidate["fingerprint"],
                        "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                    }
                )
        if include_alternates:
            for fingerprint in (
                {
                    "field_code": "docata|ZDCSZ642123",
                    "wbs_stage": "Planner",
                    "task_name": "TX SOW Details",
                    "display_header": "TX SOW Details",
                },
                {
                    "field_code": "docata|ZDCSZ01036639",
                    "wbs_stage": "Installation",
                    "task_name": "Wireless RAN",
                    "display_header": "Subcon PR - Planning",
                },
            ):
                columns.append({"fingerprint": fingerprint, "fingerprint_key": fingerprint_key(fingerprint)})
        return {"sheets": [{"sheet_name": "Jendela TX Migration", "columns": columns}]}

    def _resolved(self, *, include_alternates=False, missing_fields=None):
        return resolve_profile_field_mappings(
            self._inventory_from_profile(include_alternates=include_alternates, missing_fields=missing_fields),
            self.profile,
        )

    def _raw_values(self, overrides=None):
        values = {
            "site_code": "A0001",
            "site_name": "Synthetic Site",
            "du_key": "DU0001",
            "tx_sow_raw": "MW Swap",
            "region": "Northern",
            "subcontractor_tss": "GTSB",
            "subcontractor_ti": "GTSB",
            "subcontractor_planning": "Planner",
            "existing_tss_pr_status": "",
            "existing_ti_pr_status": "",
            "latitude": "5.1234",
            "longitude": "100.1234",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "boq_configuration": "1+0",
            "tx_sow_details": "detail",
            "ne_sow_details": "ne detail",
            "fe_sow_details": "fe detail",
        }
        values.update(overrides or {})
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in values:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = values[field_name]
        return raw

    def _context(self, *, header_hash=None):
        identity = self.profile["identity"]
        return {
            "project_key": identity["project_key"],
            "du_model_name": identity["accepted_du_models"][0],
            "du_model_id": identity["accepted_du_model_ids"][0],
            "view_id": identity["accepted_view_ids"][0],
            "source_file_name": "synthetic-jendela.xlsx",
            "source_file_hash": "synthetic-source-hash",
            "header_hash": header_hash or self.profile["export_structure"]["approved_header_hashes"][0],
            "source_row_number": 5,
        }

    def _build_record(self, overrides=None, *, profile=None, resolved=None, header_hash=None, scope="TSS"):
        profile = profile or self.profile
        return build_canonical_site_record(
            self._raw_values(overrides),
            profile,
            self._context(header_hash=header_hash),
            scope=scope,
            resolved_mappings=resolved or self._resolved(),
        )

    def _production_copy(self):
        clone = json.loads(json.dumps(self.profile))
        clone["status"] = "PRODUCTION"
        for config in clone["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        return clone

    def test_resolver_uses_only_seven_approved_runtime_fingerprints(self):
        resolved = self._resolved(include_alternates=True)
        approved_fields = (
            "site_code",
            "tx_sow_raw",
            "region",
            "subcontractor_tss",
            "subcontractor_ti",
            "existing_tss_pr_status",
            "existing_ti_pr_status",
        )
        for field_name in approved_fields:
            self.assertEqual(resolved[field_name]["status"], "RESOLVED")
        self.assertEqual(
            [match["fingerprint"]["display_header"] for match in resolved["tx_sow_raw"]["matches"]],
            ["Tx SOW"],
        )
        self.assertEqual(
            resolved["existing_tss_pr_status"]["matches"][0]["fingerprint"]["wbs_stage"],
            "PR Team",
        )
        self.assertEqual(
            resolved["existing_ti_pr_status"]["matches"][0]["fingerprint"]["wbs_stage"],
            "PR team",
        )

    def test_missing_approved_pr_column_fails_closed(self):
        resolved = self._resolved(missing_fields={"existing_ti_pr_status"})
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")
        record = self._build_record(resolved=resolved, scope="TI")
        self.assertIn(
            "MISSING_SOURCE_EVIDENCE:existing_ti_pr_status",
            record["validation"]["blocking_reasons"],
        )

    def test_unapproved_alternates_do_not_unlock_required_fields(self):
        inventory = {
            "sheets": [{
                "sheet_name": "Alternates only",
                "columns": [
                    {
                        "fingerprint": {
                            "field_code": "docata|ZDCSZ642123",
                            "wbs_stage": "Planner",
                            "task_name": "TX SOW Details",
                            "display_header": "TX SOW Details",
                        },
                        "fingerprint_key": "docata|ZDCSZ642123|Planner|TX SOW Details|TX SOW Details",
                    },
                    {
                        "fingerprint": {
                            "field_code": "docata|ZDCSZ01036639",
                            "wbs_stage": "Installation",
                            "task_name": "Wireless RAN",
                            "display_header": "Subcon PR - Planning",
                        },
                        "fingerprint_key": "docata|ZDCSZ01036639|Installation|Wireless RAN|Subcon PR - Planning",
                    },
                ],
            }]
        }
        resolved = resolve_profile_field_mappings(inventory, self.profile)
        self.assertEqual(resolved["tx_sow_raw"]["status"], "MISSING")
        self.assertEqual(resolved["existing_ti_pr_status"]["status"], "MISSING")

    def test_pr_reference_fields_normalize_consistently(self):
        record = self._build_record(
            {
                "existing_tss_pr_status": "SQ202506180613-GTSB",
                "existing_ti_pr_status": "No PR required-Work at TSS only",
            }
        )
        self.assertEqual(record["pr_context"]["existing_tss_pr_status"], PR_STATUS_EXISTS)
        self.assertEqual(record["pr_context"]["existing_ti_pr_status"], PR_STATUS_NOT_REQUIRED)
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_tss_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )
        self.assertEqual(
            record["source_evidence"]["fields"]["existing_ti_pr_status"]["transformation"],
            "normalize_pr_reference_status",
        )

    def test_scope_specific_subcontractor_validation_remains_enforced(self):
        tss_record = self._build_record({"subcontractor_tss": ""}, scope="TSS")
        self.assertIn(
            "MISSING_PR_CRITICAL_FIELD:subcontractor_tss",
            tss_record["validation"]["blocking_reasons"],
        )
        ti_record = self._build_record({"subcontractor_ti": ""}, scope="TI")
        self.assertIn(
            "MISSING_PR_CRITICAL_FIELD:subcontractor_ti",
            ti_record["validation"]["blocking_reasons"],
        )

    def test_profile_remains_non_production_and_blocks_ecc_output(self):
        record = self._build_record()
        gate = evaluate_record(record, self.profile, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("DU_PROFILE_NOT_PRODUCTION", gate["blocking_reasons"])

    def test_changed_header_hash_still_fails_closed(self):
        production = self._production_copy()
        record = self._build_record(profile=production, header_hash="changed-header-hash")
        gate = evaluate_record(record, production, scope="TSS")
        self.assertFalse(gate["allow_output"])
        self.assertIn("HEADER_HASH_REVALIDATION_REQUIRED", gate["blocking_reasons"])
```

- [ ] **Step 2: Run the adapter suite**

```powershell
python -m unittest discover -s tests -p "test_du_export_adapter.py" -v
```

Expected: all existing adapter tests plus the seven Jendela tests pass. No runtime source file under `scripts/` changes.

- [ ] **Step 3: Commit the adapter regression suite**

```powershell
git add tests/test_du_export_adapter.py
git commit -m "test(du): cover Jendela approved adapter path"
```

---

### Task 3: Synchronize Jendela governance expectations and refresh outputs

**Files:**
- Modify: `tests/test_unresolved_skill_field_review.py`
- Modify: `tests/test_missing_field_bridge_review.py`
- Modify: `tests/test_profile_readiness_review.py`
- Modify: `tests/test_profile_action_queue.py`
- Modify: `tests/test_profile_transition_review.py`
- Modify: generated registries and docs listed in the File Structure section.

**Interfaces:**
- Consumes: `build_review_entry`, `build_bridge_entry`, `build_readiness_entry`, `build_action_queue_entry`, generated transition registry, and `scripts/refresh_mw_du_discovery_packet.py`.
- Produces: tracked governance artifacts whose Jendela lifecycle, mapping version, blockers, transition decisions, rollback baseline, and identity status all agree.

- [ ] **Step 1: Replace the unresolved-field Jendela expectation**

Replace the old missing-field test with:

```python
def test_jendela_entry_records_human_approved_pr_critical_sources(self):
    shortlist_registry = json.loads(
        (ROOT / "config" / "registries" / "mw_du_priority_skill_field_shortlists.yaml").read_text(encoding="utf-8")
    )
    profile = json.loads(
        (ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml").read_text(encoding="utf-8")
    )
    shortlist_entry = next(
        entry for entry in shortlist_registry["entries"] if "Jendela TX Migration" in entry["source_file_name"]
    )
    review_entry = build_review_entry(profile, shortlist_entry)
    self.assertEqual(review_entry["profile_id"], "jendela_tx_migration_pr_v1")
    self.assertEqual(review_entry["summary"]["missing_required_fields"], [])
    self.assertNotIn("tx_sow_raw", review_entry["summary"]["competing_candidate_fields"])
    self.assertNotIn("subcontractor_ti", review_entry["summary"]["competing_candidate_fields"])
    self.assertEqual(
        review_entry["field_reviews"]["existing_tss_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
        "Subcon PR - TSS",
    )
    self.assertEqual(
        review_entry["field_reviews"]["existing_ti_pr_status"]["recommended_source"]["fingerprint"]["display_header"],
        "Subcon PR - TI",
    )
    self.assertEqual(
        review_entry["field_reviews"]["subcontractor_tss"]["recommended_source"]["fingerprint"]["display_header"],
        "SubCon - TSS",
    )
    self.assertIn("subcontractor_planning", review_entry["summary"]["competing_candidate_fields"])
```

- [ ] **Step 2: Add an empty Jendela bridge test**

```python
def test_jendela_bridge_is_empty_after_approved_pr_status_mappings(self):
    unresolved = json.loads(
        (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
    )
    grouping = json.loads(
        (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
    )
    discovery = json.loads(
        (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
    )
    unresolved_entry = next(
        entry for entry in unresolved["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1"
    )
    bridge_entry = build_bridge_entry(unresolved_entry, grouping, discovery)
    self.assertEqual(bridge_entry["profile_id"], "jendela_tx_migration_pr_v1")
    self.assertEqual(bridge_entry["profile_version"], "0.2.0")
    self.assertEqual(bridge_entry["mapping_version"], "approved-2026-07-13-jendela-tx-migration-v1")
    self.assertEqual(bridge_entry["field_bridges"], {})
```

- [ ] **Step 3: Replace the readiness test**

Replace the old DRAFT/missing-field Jendela test with:

```python
def test_jendela_entry_stays_blocked_only_for_non_production_and_optional_review_work(self):
    profile = load_du_profile(ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml")
    unresolved = json.loads(
        (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
    )
    bridge = json.loads(
        (ROOT / "config" / "registries" / "mw_du_missing_field_bridge_review.yaml").read_text(encoding="utf-8")
    )
    unresolved_entry = next(
        entry for entry in unresolved["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1"
    )
    bridge_entry = next(
        entry for entry in bridge["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1"
    )
    entry = build_readiness_entry(profile, unresolved_entry, bridge_entry)
    self.assertEqual(entry["readiness_status"], "DISCOVERY_ONLY_BLOCKED")
    self.assertEqual(entry["profile_status"], "PR_INPUT_READY")
    self.assertIn("PROFILE_NOT_PRODUCTION", entry["blocker_summary"]["overall_blockers"])
    self.assertEqual(entry["blocker_summary"]["missing_required_fields"], [])
    self.assertEqual(entry["blocker_summary"]["unapproved_required_fields"], [])
    self.assertEqual(entry["blocker_summary"]["required_competing_candidate_fields"], [])
    self.assertEqual(entry["blocker_summary"]["required_single_candidate_unverified_fields"], [])
    self.assertEqual(entry["blocker_summary"]["cross_model_bridge_fields"], [])
```

- [ ] **Step 4: Add action-queue and transition assertions**

Add to `tests/test_profile_action_queue.py`:

```python
def test_jendela_queue_has_no_header_or_missing_required_actions_after_approval(self):
    registry = json.loads(
        (ROOT / "config" / "registries" / "mw_du_profile_action_queue.yaml").read_text(encoding="utf-8")
    )
    entry = next(item for item in registry["entries"] if item["profile_id"] == "jendela_tx_migration_pr_v1")
    action_types = [item["action_type"] for item in entry["action_queue"]]
    self.assertNotIn("APPROVE_HEADER_HASH", action_types)
    self.assertNotIn("RESOLVE_MISSING_REQUIRED_FIELD", action_types)
    self.assertEqual(entry["action_queue"][-1]["action_type"], "HOLD_LIFECYCLE_PROMOTION")
```

Add to `tests/test_profile_transition_review.py`:

```python
def test_jendela_pr_input_ready_transition_is_eligible_but_production_is_denied(self):
    registry = json.loads(
        (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
    )
    entry = next(item for item in registry["entries"] if item["profile_id"] == "jendela_tx_migration_pr_v1")
    pr_input_ready = next(
        item for item in entry["transition_targets"] if item["target_status"] == "PR_INPUT_READY"
    )
    production = next(
        item for item in entry["transition_targets"] if item["target_status"] == "PRODUCTION"
    )
    self.assertTrue(pr_input_ready["eligible"])
    self.assertFalse(production["eligible"])
    self.assertEqual(production["denied_reasons"], ["PROFILE_NOT_PRODUCTION"])
```

- [ ] **Step 5: Run the focused governance tests before refresh**

```powershell
python -m unittest discover -s tests -p "test_unresolved_skill_field_review.py" -v
python -m unittest discover -s tests -p "test_missing_field_bridge_review.py" -v
python -m unittest discover -s tests -p "test_profile_readiness_review.py" -v
python -m unittest discover -s tests -p "test_profile_action_queue.py" -v
python -m unittest discover -s tests -p "test_profile_transition_review.py" -v
```

Expected: direct profile-based unresolved tests may pass, while registry-backed bridge, readiness, action-queue, and transition tests fail because the tracked packet still contains Jendela `DRAFT` state and missing-field blockers.

- [ ] **Step 6: Refresh the governance packet**

Run:

```powershell
python scripts/refresh_mw_du_discovery_packet.py
```

Expected Jendela outcomes:

- profile status becomes `PR_INPUT_READY` in generated registries;
- mapping version becomes `approved-2026-07-13-jendela-tx-migration-v1`;
- missing required fields become empty;
- cross-model bridge fields become empty;
- Header Hash approval action disappears;
- transition review allows `PR_INPUT_READY` and denies `PRODUCTION` with `PROFILE_NOT_PRODUCTION`;
- rollback baseline records profile version `0.2.0` and the approved Header Hash;
- traceability and coverage artifacts reference the approved profile metadata.

- [ ] **Step 7: Remove unrelated regenerated drift**

Use this exact allow-list review:

```powershell
$Allowed = @(
  "config/du_profiles/jendela_tx_migration_pr_v1.yaml",
  "config/registries/mw_du_profile_identity_registry.yaml",
  "config/registries/mw_du_export_coverage_review.yaml",
  "config/registries/mw_du_missing_field_bridge_review.yaml",
  "config/registries/mw_du_model_discovery_registry.yaml",
  "config/registries/mw_du_profile_action_queue.yaml",
  "config/registries/mw_du_profile_deprecation_review.yaml",
  "config/registries/mw_du_profile_readiness_review.yaml",
  "config/registries/mw_du_profile_review_matrix.yaml",
  "config/registries/mw_du_profile_rollback_readiness.yaml",
  "config/registries/mw_du_profile_traceability_audit.yaml",
  "config/registries/mw_du_profile_transition_review.yaml",
  "config/registries/mw_du_unresolved_skill_field_review.yaml",
  "docs/MW_DU_All_DU_Discovery_Mapping_Review.md",
  "docs/MW_DU_Export_Coverage_Review.md",
  "docs/MW_DU_Missing_Field_Bridge_Review.md",
  "docs/MW_DU_Profile_Action_Queue.md",
  "docs/MW_DU_Profile_Deprecation_Review.md",
  "docs/MW_DU_Profile_Readiness_Review.md",
  "docs/MW_DU_Profile_Review_Matrix.md",
  "docs/MW_DU_Profile_Rollback_Readiness.md",
  "docs/MW_DU_Profile_Traceability_Audit.md",
  "docs/MW_DU_Profile_Transition_Review.md",
  "docs/MW_DU_Unresolved_Skill_Field_Review.md",
  "tests/test_du_profile_loader.py",
  "tests/test_du_profile_identity_governance.py",
  "tests/test_du_export_adapter.py",
  "tests/test_unresolved_skill_field_review.py",
  "tests/test_missing_field_bridge_review.py",
  "tests/test_profile_readiness_review.py",
  "tests/test_profile_action_queue.py",
  "tests/test_profile_transition_review.py",
  "tests/test_profile_rollback_readiness.py"
)
$Unexpected = git diff --name-only | Where-Object { $_ -notin $Allowed }
if ($Unexpected) {
  $Unexpected | ForEach-Object { git restore -- $_ }
}
git diff --name-only
```

Expected: every remaining path is in `$Allowed`. No file under `Info/reference`, `output`, `scripts`, another profile YAML, workbook, CSV, or template remains changed.

- [ ] **Step 8: Run the focused governance tests again**

Run the five commands from Step 5 plus:

```powershell
python -m unittest discover -s tests -p "test_profile_rollback_readiness.py" -v
python -m unittest discover -s tests -p "test_du_profile_identity_governance.py" -v
```

Expected: all focused governance tests pass.

- [ ] **Step 9: Run consistency guards**

```powershell
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
```

Expected:

```text
Profile status consistency check passed.
Discovery packet consistency check passed.
```

- [ ] **Step 10: Commit synchronized governance outputs**

```powershell
git add config/registries `
        docs/MW_DU_All_DU_Discovery_Mapping_Review.md `
        docs/MW_DU_Export_Coverage_Review.md `
        docs/MW_DU_Missing_Field_Bridge_Review.md `
        docs/MW_DU_Profile_Action_Queue.md `
        docs/MW_DU_Profile_Deprecation_Review.md `
        docs/MW_DU_Profile_Readiness_Review.md `
        docs/MW_DU_Profile_Review_Matrix.md `
        docs/MW_DU_Profile_Rollback_Readiness.md `
        docs/MW_DU_Profile_Traceability_Audit.md `
        docs/MW_DU_Profile_Transition_Review.md `
        docs/MW_DU_Unresolved_Skill_Field_Review.md `
        tests/test_unresolved_skill_field_review.py `
        tests/test_missing_field_bridge_review.py `
        tests/test_profile_readiness_review.py `
        tests/test_profile_action_queue.py `
        tests/test_profile_transition_review.py
git commit -m "docs(du): refresh Jendela profile governance"
```

---

### Task 4: Complete repository verification and safety audit

**Files:**
- Verify only; no planned source modification.

**Interfaces:**
- Consumes: full test suite, profile-status guard, discovery consistency guard, Python compiler, Git diff.
- Produces: merge-ready evidence for Draft PR #31 while preserving non-production safety.

- [ ] **Step 1: Run the full test suite**

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: `Ran 290 tests` and `OK` when the test additions in this plan are applied exactly.

- [ ] **Step 2: Run repository guards and compilation**

```powershell
python scripts/check_profile_status_consistency.py
python scripts/check_discovery_packet_consistency.py
python -m compileall -q scripts
git diff --check
```

Expected: both guards pass; `compileall` and `git diff --check` produce no error output.

- [ ] **Step 3: Assert that no profile is production**

```powershell
python -c "import json,pathlib; p=pathlib.Path('config/du_profiles'); profiles=[json.loads(x.read_text(encoding='utf-8')) for x in p.glob('*.yaml')]; assert all(x['status']!='PRODUCTION' for x in profiles); print('No DU profile is PRODUCTION.')"
```

Expected:

```text
No DU profile is PRODUCTION.
```

- [ ] **Step 4: Assert customer-data hygiene**

```powershell
$Unsafe = git diff --name-only main...HEAD | Select-String -Pattern '(^|/)Info/reference/|(^|/)output/|\.xlsx$|\.xls$|\.csv$'
if ($Unsafe) {
  $Unsafe
  throw "Unsafe customer/reference artifact detected in branch diff."
}
```

Expected: no output and no exception.

- [ ] **Step 5: Review the final branch diff**

```powershell
git diff --stat main...HEAD
git diff --name-status main...HEAD
git status --short
```

Expected:

- the design and implementation plan remain present;
- one Jendela profile changed;
- one identity-registry status changed;
- Jendela adapter/lifecycle tests changed;
- only directly related generated governance files changed;
- no runtime script, generator, another DU profile, raw export, workbook, or template changed;
- working tree is clean.

---

### Task 5: Update Draft PR #31 with implementation evidence

**Files:**
- GitHub PR metadata only.

**Interfaces:**
- Consumes: branch commits and Task 4 verification output.
- Produces: a reviewable Draft PR; does not mark Ready or merge.

- [ ] **Step 1: Push the completed branch**

```powershell
git push -u origin feat/jendela-pr-input-ready
```

Expected: remote branch updates successfully.

- [ ] **Step 2: Replace the Draft PR body**

Use this body:

```markdown
## Summary

- advances Issue #21 for Jendela TX Migration
- promotes `jendela_tx_migration_pr_v1` from `DRAFT` to non-production `PR_INPUT_READY`
- approves the strict observed Header Hash
- approves seven exact four-layer runtime mappings
- adds TSS/TI subcontractor, PR-reference normalization, Header Hash, missing-source, alternate-candidate, and non-production tests
- synchronizes identity, readiness, bridge, transition, rollback, traceability, coverage, action-queue, and review artifacts

## Approved mappings

- `site_code`
- `tx_sow_raw`
- `region`
- `subcontractor_tss` — profile optional, TSS-scope required
- `subcontractor_ti`
- `existing_tss_pr_status`
- `existing_ti_pr_status`

Both existing-PR fields use `normalize_pr_reference_status`.

## Safety boundary

- no generator logic changed
- no ECC template or PR model changed
- no SOW business rule changed
- no other DU profile changed
- no raw iEPMS export or `Info/reference` file committed
- no profile is `PRODUCTION`
- ECC remains blocked by `DU_PROFILE_NOT_PRODUCTION`

## Verification

- focused Jendela profile, adapter, lifecycle, and governance tests passed
- full suite: 290 tests passed
- profile status consistency passed
- discovery packet consistency passed
- `python -m compileall -q scripts` passed
- `git diff --check` passed
- customer/reference artifact guard passed

## Review state

Keep this PR as Draft until the current head SHA and complete diff are independently reviewed.
```

- [ ] **Step 3: Confirm the PR remains Draft and points to the expected branch**

```powershell
gh pr view 31 --json number,state,isDraft,headRefName,baseRefName,headRefOid,mergeable
```

Expected:

- `number`: `31`
- `state`: `OPEN`
- `isDraft`: `true`
- `headRefName`: `feat/jendela-pr-input-ready`
- `baseRefName`: `main`
- `mergeable`: `MERGEABLE` after GitHub finishes recalculating.

Do not mark Ready, approve, or merge in this task.
