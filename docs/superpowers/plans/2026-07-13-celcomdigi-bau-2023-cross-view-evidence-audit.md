# 2023 Celcomdigi BAU Cross-View Evidence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic, local-only evidence packet that audits every local `Malaysia_CelcomDigi_Project + 2023 Celcomdigi BAU` export across Views and decides whether a later non-production `PR_INPUT_READY` onboarding design can be prepared.

**Architecture:** Reuse the tracked read-only inventory and four-header profiler modules, then add one ignored local aggregation helper and one ignored local test module under the audit output directory. The helper inventories matching exports, profiles exact four-layer fingerprints, gathers redacted value statistics, classifies seven target fields, writes the required packet, and conditionally writes an onboarding design draft without modifying tracked code or configuration.

**Tech Stack:** Python 3, `pathlib`, `json`, `hashlib`, `re`, `collections`, `openpyxl`, `unittest`, existing `scripts/discover_local_du_references.py`, existing `scripts/profile_du_export.py`, Windows PowerShell, Git.

## Global Constraints

- Repository: `Gumb-D/create-pr-cd`.
- Local repository path: `C:\dev\create-pr-cd`.
- Approved spec: `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md`.
- Target identity is exactly Project `Malaysia_CelcomDigi_Project`, DU Model `2023 Celcomdigi BAU`, DU Model ID `8296022438223590261`.
- View ID is evidence metadata, not an identity boundary.
- Target profile remains `celcomdigi_bau_2023_pr_v1` with lifecycle `DRAFT` throughout this audit.
- Audit all local exports under `Info/reference` attributable to the target Project + DU Model identity.
- Other DU Models may improve search terminology only; they cannot supply approval evidence.
- Audit exactly these runtime fields: `site_code`, `tx_sow_raw`, `region`, `subcontractor_tss`, `subcontractor_ti`, `existing_tss_pr_status`, `existing_ti_pr_status`.
- All generated helpers, tests, inventories, logs, statistics, decisions, and drafts must remain under `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/`.
- Do not modify any tracked script, profile, registry, test, ECC template, PR model, SOW rule, or documentation during audit execution.
- Do not add or force-add anything under `Info/reference` or `output`.
- Do not create PR or ECC output.
- Do not promote any profile to `PR_INPUT_READY` or `PRODUCTION`.
- Generate `onboarding_design_draft.md` only when `decision.json.result` is exactly `ONBOARDING_DESIGN_READY`.
- Repository working tree must be clean before and after execution.

## File Structure

Tracked files used read-only:

- `scripts/discover_local_du_references.py` — inventory all local reference files and infer candidate DU model names.
- `scripts/profile_du_export.py` — preserve exact four-header fingerprints, calculate deterministic Header Hashes, and produce UNVERIFIED profiler output.
- `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml` — current DRAFT baseline, read-only.
- `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md` — approved audit contract.

Local-only files created during execution:

- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/run_cross_view_audit.py` — deterministic multi-export audit aggregator.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/test_run_cross_view_audit.py` — local-only unit tests for classification, redaction, decision, and deterministic output behavior.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.json` — raw inventory metadata produced by the tracked discovery helper.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.md` — human-readable inventory metadata.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/profiles/<file-key>/` — per-export tracked-profiler outputs.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/audit_summary.md` — final audit summary.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/export_inventory.json` — included and excluded export evidence.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/header_hash_matrix.md` — cross-View Header Hash and field-presence matrix.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/pr_field_candidate_review.md` — seven-field candidate review.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/non_empty_statistics.json` — safe value statistics.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/rejected_candidates.md` — false positives and exclusion reasons.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/decision.json` — final machine-readable result.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/onboarding_design_draft.md` — conditional evidence-derived design draft.
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/progress_ledger.md` — durable task status and verification evidence.

---

### Task 1: Establish a Clean, Reproducible Audit Workspace

**Files:**
- Read: `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md`
- Read: `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/progress_ledger.md`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/preflight_tracked_files.txt`

**Interfaces:**
- Consumes: clean Git checkout containing the approved spec and current DRAFT profile.
- Produces: stable audit root, preflight Git snapshot, and task ledger used by all later tasks.

- [ ] **Step 1: Check out the approved documentation branch and verify the exact spec commit ancestry**

```powershell
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location C:\dev\create-pr-cd

git fetch origin --prune
git switch docs/celcomdigi-bau-2023-evidence-audit-design
git pull --ff-only origin docs/celcomdigi-bau-2023-evidence-audit-design

git status --short
if (git status --short) { throw "Working tree must be clean before the audit." }

git log -3 --oneline
```

Expected: clean output from `git status --short`; recent history includes the spec commit and this plan commit.

- [ ] **Step 2: Create the ignored audit directory and snapshot tracked state**

```powershell
$AuditRoot = "output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit"
New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null

git ls-files | Sort-Object | Set-Content "$AuditRoot/preflight_tracked_files.txt" -Encoding utf8
@
# 2023 Celcomdigi BAU Cross-View Audit Progress

- Repository preflight: PASS
- Target Project: Malaysia_CelcomDigi_Project
- Target DU Model: 2023 Celcomdigi BAU
- Target DU Model ID: 8296022438223590261
- Tracked profile lifecycle: DRAFT
- Task 1: IN_PROGRESS
- Task 2: PENDING
- Task 3: PENDING
- Task 4: PENDING
- Task 5: PENDING
- Task 6: PENDING
@ | Set-Content "$AuditRoot/progress_ledger.md" -Encoding utf8
```

Expected: files exist under ignored `output/`; `git status --short` remains empty.

- [ ] **Step 3: Verify local sources exist and remain untracked**

```powershell
if (-not (Test-Path "Info/reference")) { throw "Info/reference is missing." }
$ReferenceFiles = Get-ChildItem "Info/reference" -Recurse -File | Where-Object { $_.Extension -in ".xlsx", ".xlsm", ".csv", ".xls" }
if (-not $ReferenceFiles) { throw "No local DU reference files were found." }

$TrackedSensitive = git ls-files "Info/reference/**" "output/**"
if ($TrackedSensitive) {
    $TrackedSensitive
    throw "Sensitive local reference/output files are tracked. Stop before audit."
}
```

Expected: at least one reference file and no tracked paths under `Info/reference` or `output`.

- [ ] **Step 4: Record the checkpoint without committing local outputs**

Update `progress_ledger.md` to `Task 1: PASS`. Do not run `git add` or `git commit`; all Task 1 artifacts are intentionally local-only.

---

### Task 2: Build and Test the Local-Only Audit Aggregator

**Files:**
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/run_cross_view_audit.py`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/test_run_cross_view_audit.py`
- Read: `scripts/discover_local_du_references.py`
- Read: `scripts/profile_du_export.py`

**Interfaces:**
- Consumes:
  - `discover_local_du_references.discover_reference_files(reference_root: Path) -> list[dict]`
  - `profile_du_export.build_header_inventory(input_path: Path) -> dict`
  - `profile_du_export.calculate_header_hash(inventory: Mapping[str, Any]) -> str`
- Produces:
  - `safe_value_pattern(value: Any) -> str`
  - `classify_value_type(values: Sequence[Any]) -> str`
  - `candidate_matches_target(fingerprint: Mapping[str, str], target_field: str) -> bool`
  - `collect_column_statistics(path: Path, sheet_name: str, one_based_index: int) -> dict`
  - `decide_audit(field_reviews: Mapping[str, Any]) -> str`
  - `run_audit(reference_root: Path, output_root: Path) -> dict`

- [ ] **Step 1: Write failing tests for redaction, semantic matching, and decision behavior**

Create `test_run_cross_view_audit.py` with these tests:

```python
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("run_cross_view_audit.py")
spec = importlib.util.spec_from_file_location("run_cross_view_audit", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class TestCrossViewAudit(unittest.TestCase):
    def test_safe_value_pattern_redacts_reference_and_text(self):
        self.assertEqual(module.safe_value_pattern("PR-2023-000123"), "AA-9999-999999")
        self.assertEqual(module.safe_value_pattern("Approved"), "TEXT[len=8]")
        self.assertEqual(module.safe_value_pattern("2026-07-13"), "DATE_PATTERN")

    def test_candidate_matching_uses_all_four_header_layers(self):
        fingerprint = {
            "field_code": "docata|ZDCSZ641766",
            "wbs_stage": "Installation",
            "task_name": "Wireless RAN",
            "display_header": "Subcon PR - TSS",
        }
        self.assertTrue(module.candidate_matches_target(fingerprint, "existing_tss_pr_status"))
        self.assertFalse(module.candidate_matches_target(fingerprint, "existing_ti_pr_status"))

    def test_milestone_date_is_rejected_for_existing_pr_status(self):
        review = module.classify_candidate(
            "existing_tss_pr_status",
            {
                "field_code": "WP10400|AC0000086573|plan_start_date",
                "wbs_stage": "Survey&Design",
                "task_name": "TSSR Customer Approval",
                "display_header": "planned start time",
            },
            {"non_empty_rows": 12, "value_type": "date", "unique_non_empty_values": 12},
        )
        self.assertEqual(review["classification"], "REJECTED_SEMANTIC_MISMATCH")

    def test_decision_ready_requires_all_seven_direct_candidates(self):
        ready = {
            field: {"status": "DIRECT_APPROVAL_CANDIDATE", "unique_per_header_hash": True}
            for field in module.TARGET_FIELDS
        }
        self.assertEqual(module.decide_audit(ready), "ONBOARDING_DESIGN_READY")
        ready["existing_ti_pr_status"] = {"status": "MISSING", "unique_per_header_hash": False}
        self.assertEqual(module.decide_audit(ready), "KEEP_DRAFT_QUARANTINED")

    def test_design_draft_is_written_only_for_ready_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.write_conditional_design(root, "HUMAN_REVIEW_REQUIRED", {})
            self.assertFalse((root / "onboarding_design_draft.md").exists())
            module.write_conditional_design(root, "ONBOARDING_DESIGN_READY", {"field_reviews": {}})
            self.assertTrue((root / "onboarding_design_draft.md").exists())

    def test_json_writer_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            module.write_json(path, {"b": 2, "a": 1})
            first = path.read_bytes()
            module.write_json(path, {"a": 1, "b": 2})
            self.assertEqual(first, path.read_bytes())
            self.assertEqual(json.loads(first), {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify they fail because the helper does not exist**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
```

Expected: FAIL with `FileNotFoundError` for `run_cross_view_audit.py`.

- [ ] **Step 3: Implement the local-only helper with exact constants and deterministic writers**

Create `run_cross_view_audit.py` with these required constants and interfaces:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))

from discover_local_du_references import discover_reference_files
from profile_du_export import build_header_inventory, calculate_header_hash

TARGET_PROJECT = "Malaysia_CelcomDigi_Project"
TARGET_DU_MODEL = "2023 Celcomdigi BAU"
TARGET_DU_MODEL_ID = "8296022438223590261"
TARGET_PROFILE_ID = "celcomdigi_bau_2023_pr_v1"
TARGET_FIELDS = (
    "site_code",
    "tx_sow_raw",
    "region",
    "subcontractor_tss",
    "subcontractor_ti",
    "existing_tss_pr_status",
    "existing_ti_pr_status",
)

FIELD_TERMS = {
    "site_code": (("customer", "site", "code"),),
    "tx_sow_raw": (("tx", "sow"),),
    "region": (("region",),),
    "subcontractor_tss": (("subcon", "tss"), ("subcontractor", "tss")),
    "subcontractor_ti": (("subcon", "ti"), ("subcontractor", "ti")),
    "existing_tss_pr_status": (
        ("subcon", "pr", "tss"),
        ("pr", "tss", "status"),
        ("tss", "pr"),
    ),
    "existing_ti_pr_status": (
        ("subcon", "pr", "ti"),
        ("pr", "ti", "status"),
        ("ti", "pr"),
    ),
}

DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T].*)?$")
TOKEN_RE = re.compile(r"[A-Za-z]+|\d+")


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\u00a0", " ").split())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def safe_value_pattern(value: Any) -> str:
    text = normalize(value)
    if not text:
        return "BLANK"
    if isinstance(value, (datetime, date)) or DATE_RE.match(text):
        return "DATE_PATTERN"
    if re.fullmatch(r"[A-Za-z]+(?:[-_/][A-Za-z0-9]+)+", text) or re.search(r"\d", text):
        parts = []
        for token in TOKEN_RE.findall(text):
            if token.isdigit():
                parts.append("9" * len(token))
            else:
                parts.append("A" * len(token))
        separators = re.findall(r"[^A-Za-z0-9]+", text)
        rebuilt = parts[0]
        for separator, part in zip(separators, parts[1:]):
            rebuilt += separator + part
        return rebuilt
    return f"TEXT[len={len(text)}]"


def classify_value_type(values: Sequence[Any]) -> str:
    non_empty = [value for value in values if normalize(value)]
    if not non_empty:
        return "empty"
    patterns = {safe_value_pattern(value) for value in non_empty}
    if patterns == {"DATE_PATTERN"}:
        return "date"
    texts = {normalize(value).lower() for value in non_empty}
    if texts <= {"yes", "no", "y", "n", "true", "false", "0", "1"}:
        return "boolean_like"
    if all(pattern not in {"DATE_PATTERN"} and any(char.isdigit() for char in normalize(value)) for pattern, value in zip(map(safe_value_pattern, non_empty), non_empty)):
        return "reference_or_mixed_identifier"
    if len(texts) <= 20:
        return "status_or_categorical_text"
    return "free_text_or_mixed"


def header_text(fingerprint: Mapping[str, str]) -> str:
    return " ".join(normalize(fingerprint.get(key, "")) for key in ("field_code", "wbs_stage", "task_name", "display_header")).lower()


def candidate_matches_target(fingerprint: Mapping[str, str], target_field: str) -> bool:
    text = header_text(fingerprint)
    return any(all(term in text for term in terms) for terms in FIELD_TERMS[target_field])


def classify_candidate(target_field: str, fingerprint: Mapping[str, str], statistics: Mapping[str, Any]) -> dict[str, Any]:
    text = header_text(fingerprint)
    value_type = statistics.get("value_type", "empty")
    non_empty = int(statistics.get("non_empty_rows", 0))
    if target_field in {"existing_tss_pr_status", "existing_ti_pr_status"}:
        mismatch_terms = ("plan_start_date", "actual_start_date", "planned start time", "actual start time", "tssr customer approval", "rectification")
        if value_type == "date" or any(term in text for term in mismatch_terms):
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif "planning" in text and target_field == "existing_ti_pr_status":
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif not candidate_matches_target(fingerprint, target_field):
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif non_empty == 0:
            classification = "HUMAN_REVIEW_REQUIRED"
        elif value_type in {"status_or_categorical_text", "reference_or_mixed_identifier", "free_text_or_mixed"}:
            classification = "DIRECT_APPROVAL_CANDIDATE"
        else:
            classification = "HUMAN_REVIEW_REQUIRED"
    else:
        if not candidate_matches_target(fingerprint, target_field):
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif non_empty == 0:
            classification = "HUMAN_REVIEW_REQUIRED"
        else:
            classification = "DIRECT_APPROVAL_CANDIDATE"
    return {
        "target_field": target_field,
        "classification": classification,
        "fingerprint": dict(fingerprint),
        "statistics": dict(statistics),
    }


def decide_audit(field_reviews: Mapping[str, Any]) -> str:
    statuses = {field: field_reviews.get(field, {}).get("status", "MISSING") for field in TARGET_FIELDS}
    if statuses["existing_tss_pr_status"] in {"MISSING", "REJECTED_SEMANTIC_MISMATCH"}:
        return "KEEP_DRAFT_QUARANTINED"
    if statuses["existing_ti_pr_status"] in {"MISSING", "REJECTED_SEMANTIC_MISMATCH"}:
        return "KEEP_DRAFT_QUARANTINED"
    if all(
        statuses[field] == "DIRECT_APPROVAL_CANDIDATE"
        and field_reviews[field].get("unique_per_header_hash") is True
        for field in TARGET_FIELDS
    ):
        return "ONBOARDING_DESIGN_READY"
    return "HUMAN_REVIEW_REQUIRED"


def write_conditional_design(output_root: Path, decision: str, audit: Mapping[str, Any]) -> None:
    path = output_root / "onboarding_design_draft.md"
    if decision != "ONBOARDING_DESIGN_READY":
        path.unlink(missing_ok=True)
        return
    field_reviews = audit.get("field_reviews", {})
    lines = [
        "# 2023 Celcomdigi BAU PR_INPUT_READY Onboarding Design Draft",
        "",
        "Evidence-derived local draft only. No mapping or Header Hash is approved by this file.",
        "",
        f"- Profile ID: `{TARGET_PROFILE_ID}`",
        "- Proposed profile version: `0.2.0`",
        "- Proposed mapping version: `approved-YYYY-MM-DD-2023-celcomdigi-bau-v1`",
        f"- Project: `{TARGET_PROJECT}`",
        f"- DU Model: `{TARGET_DU_MODEL}`",
        f"- DU Model ID: `{TARGET_DU_MODEL_ID}`",
        "- Proposed lifecycle ceiling: `PR_INPUT_READY`",
        "- ECC: remains blocked until separate `PRODUCTION` approval and golden-output evidence",
        "",
        "## Seven Runtime Mappings",
        "",
    ]
    for field in TARGET_FIELDS:
        review = field_reviews.get(field, {})
        lines.append(f"### `{field}`")
        for candidate in review.get("accepted_candidates", []):
            fp = candidate["fingerprint"]
            lines.append(
                "- `{field_code}` | `{wbs_stage}` | `{task_name}` | `{display_header}`".format(**fp)
            )
        if field in {"existing_tss_pr_status", "existing_ti_pr_status"}:
            lines.append("- Transform: `normalize_pr_reference_status`")
        lines.append("")
    lines.extend([
        "## Required Fail-Closed Tests",
        "",
        "- changed Header Hash is quarantined;",
        "- missing approved source column is quarantined;",
        "- ambiguous candidate resolution is quarantined;",
        "- blank scope-specific subcontractor value is rejected;",
        "- profile remains non-production and ECC is blocked;",
        "- rollback baseline preserves the pre-onboarding DRAFT profile.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
```

Complete the helper with these additional functions:

```python
def collect_column_statistics(path: Path, sheet_name: str, one_based_index: int) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        worksheet = workbook[sheet_name]
        values = [row[0].value for row in worksheet.iter_rows(min_row=5, min_col=one_based_index, max_col=one_based_index)]
    finally:
        workbook.close()
    non_empty_values = [value for value in values if normalize(value)]
    patterns = Counter(safe_value_pattern(value) for value in non_empty_values)
    return {
        "total_data_rows": len(values),
        "non_empty_rows": len(non_empty_values),
        "blank_rows": len(values) - len(non_empty_values),
        "unique_non_empty_values": len({normalize(value) for value in non_empty_values}),
        "value_type": classify_value_type(non_empty_values),
        "safe_example_patterns": [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted(patterns.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
    }


def file_key(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
```

`run_audit(reference_root, output_root)` must:

1. call `discover_reference_files(reference_root)`;
2. include only files whose `candidate_du_model` equals `2023 Celcomdigi BAU`, whose filename or profiler evidence does not conflict with Project `Malaysia_CelcomDigi_Project`, and whose extension is `.xlsx`, `.xlsm`, or `.csv`;
3. record every excluded file with a deterministic exclusion reason;
4. call `build_header_inventory(path)` and `calculate_header_hash(inventory)` for every included export;
5. write each profiler inventory to `profiles/<file-key>/header_inventory.json` and Header Hash to `profiles/<file-key>/header_hash.txt`;
6. search every complete fingerprint for each target field;
7. gather statistics using the column's `one_based_index` and sheet name;
8. classify every candidate;
9. consolidate identical fingerprints by Header Hash;
10. set a field review to:
    - `DIRECT_APPROVAL_CANDIDATE` only when every proposed Header Hash has exactly one direct candidate;
    - `HUMAN_REVIEW_REQUIRED` when a Header Hash has multiple plausible candidates, an empty plausible candidate, or inconsistent fingerprints requiring human selection;
    - `REJECTED_SEMANTIC_MISMATCH` when candidates exist but all are rejected;
    - `MISSING` when no same-DU candidate exists;
11. set `unique_per_header_hash` to `True` only when each included Header Hash resolves to exactly one direct candidate;
12. call `decide_audit(field_reviews)`;
13. write all required JSON and Markdown packet files with no generation timestamp;
14. call `write_conditional_design`;
15. return the complete deterministic audit payload.

Add a CLI:

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local-only 2023 Celcomdigi BAU cross-View evidence audit")
    parser.add_argument("--reference-root", default="Info/reference")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_audit(Path(args.reference_root), Path(args.output_root))
    print(f"Included exports: {len(result['included_exports'])}")
    print(f"Decision: {result['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the local tests and fix only the local helper until they pass**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
```

Expected: `Ran 6 tests` and `OK`.

- [ ] **Step 5: Compile the local helper**

```powershell
python -m py_compile "$AuditRoot/run_cross_view_audit.py" "$AuditRoot/test_run_cross_view_audit.py"
```

Expected: exit code `0` and no output.

- [ ] **Step 6: Record the checkpoint without committing local code**

Update `progress_ledger.md` to `Task 2: PASS`, including the six-test result. Confirm `git status --short` is still empty. Do not commit the ignored helper or tests.

---

### Task 3: Inventory and Profile Every In-Scope Export

**Files:**
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.json`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.md`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/profiles/<file-key>/header_inventory.json`
- Create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/profiles/<file-key>/header_hash.txt`

**Interfaces:**
- Consumes: tracked discovery helper and tested local aggregator.
- Produces: deterministic included/excluded export set and per-export exact four-layer evidence.

- [ ] **Step 1: Run the tracked local reference inventory**

```powershell
python scripts/discover_local_du_references.py `
  --reference-root "Info/reference" `
  --output "$AuditRoot/local_reference_inventory.json"
```

Expected: command reports the number of discovered files; JSON and Markdown inventory files exist.

- [ ] **Step 2: Execute the local cross-View audit**

```powershell
python "$AuditRoot/run_cross_view_audit.py" `
  --reference-root "Info/reference" `
  --output-root "$AuditRoot"
```

Expected: at least one included export and one of the three exact decisions:

```text
ONBOARDING_DESIGN_READY
HUMAN_REVIEW_REQUIRED
KEEP_DRAFT_QUARANTINED
```

- [ ] **Step 3: Verify every included export has the correct identity**

```powershell
$Inventory = Get-Content "$AuditRoot/export_inventory.json" -Raw | ConvertFrom-Json
if (-not $Inventory.included_exports) { throw "No target exports were included." }
foreach ($Export in $Inventory.included_exports) {
    if ($Export.project_key -ne "Malaysia_CelcomDigi_Project") { throw "Project identity mismatch: $($Export.source_file_name)" }
    if ($Export.du_model_name -ne "2023 Celcomdigi BAU") { throw "DU Model mismatch: $($Export.source_file_name)" }
    if ($Export.du_model_id -and $Export.du_model_id -ne "8296022438223590261") { throw "DU Model ID mismatch: $($Export.source_file_name)" }
    if (-not $Export.header_hash) { throw "Missing Header Hash: $($Export.source_file_name)" }
}
```

Expected: no exception.

- [ ] **Step 4: Verify every fingerprint has four non-null keys**

```powershell
$Stats = Get-Content "$AuditRoot/non_empty_statistics.json" -Raw | ConvertFrom-Json
foreach ($Entry in $Stats.entries) {
    foreach ($Key in "field_code", "wbs_stage", "task_name", "display_header") {
        if ($null -eq $Entry.fingerprint.$Key) { throw "Incomplete fingerprint for $($Entry.target_field)" }
    }
}
```

Expected: no exception.

- [ ] **Step 5: Record the checkpoint**

Update `progress_ledger.md` with included file count, excluded file count, distinct Header Hash count, and `Task 3: PASS`. Do not commit any audit output.

---

### Task 4: Review the Seven Fields and Produce the Audit Decision

**Files:**
- Verify: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/pr_field_candidate_review.md`
- Verify: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/non_empty_statistics.json`
- Verify: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/rejected_candidates.md`
- Verify: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/decision.json`

**Interfaces:**
- Consumes: per-export inventories and safe value statistics.
- Produces: one evidence-backed classification per field and one exact audit decision.

- [ ] **Step 1: Assert all seven field reviews exist**

```powershell
$Decision = Get-Content "$AuditRoot/decision.json" -Raw | ConvertFrom-Json
$ExpectedFields = @(
  "site_code",
  "tx_sow_raw",
  "region",
  "subcontractor_tss",
  "subcontractor_ti",
  "existing_tss_pr_status",
  "existing_ti_pr_status"
)
foreach ($Field in $ExpectedFields) {
    if (-not ($Decision.field_reviews.PSObject.Properties.Name -contains $Field)) {
        throw "Missing field review: $Field"
    }
}
```

Expected: no exception.

- [ ] **Step 2: Check duplicate-prevention candidates manually against exact rejection rules**

Open `pr_field_candidate_review.md` and `rejected_candidates.md`. Confirm:

- milestone planned/actual timestamps are rejected;
- TSSR approval dates are rejected;
- `Subcon PR - Planning` is rejected for `existing_ti_pr_status`;
- rectification-only milestones are rejected unless value evidence clearly represents an active duplicate-prevention reference/status;
- no candidate from another DU Model appears as accepted evidence;
- accepted candidates have non-empty safe statistics.

If any rule is violated, fix only `run_cross_view_audit.py`, add a regression test to `test_run_cross_view_audit.py`, rerun the six existing tests plus the new test, and rerun Task 3.

- [ ] **Step 3: Validate the decision contract**

```powershell
$Allowed = @("ONBOARDING_DESIGN_READY", "HUMAN_REVIEW_REQUIRED", "KEEP_DRAFT_QUARANTINED")
if ($Decision.result -notin $Allowed) { throw "Invalid decision result: $($Decision.result)" }

if ($Decision.result -eq "ONBOARDING_DESIGN_READY") {
    foreach ($Field in $ExpectedFields) {
        $Review = $Decision.field_reviews.$Field
        if ($Review.status -ne "DIRECT_APPROVAL_CANDIDATE") { throw "Ready decision has non-direct field: $Field" }
        if ($Review.unique_per_header_hash -ne $true) { throw "Ready decision has non-unique field: $Field" }
    }
}

if ($Decision.result -eq "KEEP_DRAFT_QUARANTINED") {
    $Tss = $Decision.field_reviews.existing_tss_pr_status.status
    $Ti = $Decision.field_reviews.existing_ti_pr_status.status
    if (($Tss -notin @("MISSING", "REJECTED_SEMANTIC_MISMATCH")) -and ($Ti -notin @("MISSING", "REJECTED_SEMANTIC_MISMATCH"))) {
        throw "Quarantine decision lacks a duplicate-prevention blocker."
    }
}
```

Expected: no exception.

- [ ] **Step 4: Record the evidence result**

Update `progress_ledger.md` with each field's status and the exact decision. Mark `Task 4: PASS` only after the manual semantic review is complete.

---

### Task 5: Generate or Suppress the Conditional Onboarding Design

**Files:**
- Conditionally create: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/onboarding_design_draft.md`
- Verify: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/decision.json`

**Interfaces:**
- Consumes: exact decision and accepted candidate matrix.
- Produces: evidence-derived onboarding design only for a ready result.

- [ ] **Step 1: Enforce conditional existence**

```powershell
$Decision = Get-Content "$AuditRoot/decision.json" -Raw | ConvertFrom-Json
$DesignPath = "$AuditRoot/onboarding_design_draft.md"
if ($Decision.result -eq "ONBOARDING_DESIGN_READY") {
    if (-not (Test-Path $DesignPath)) { throw "Ready decision requires onboarding_design_draft.md" }
} else {
    if (Test-Path $DesignPath) { throw "Non-ready decision must not produce onboarding_design_draft.md" }
}
```

Expected: no exception.

- [ ] **Step 2: For a ready result, verify the design contains every required control**

```powershell
if ($Decision.result -eq "ONBOARDING_DESIGN_READY") {
    $Design = Get-Content $DesignPath -Raw
    $RequiredTerms = @(
      "celcomdigi_bau_2023_pr_v1",
      "Malaysia_CelcomDigi_Project",
      "2023 Celcomdigi BAU",
      "8296022438223590261",
      "PR_INPUT_READY",
      "normalize_pr_reference_status",
      "changed Header Hash",
      "missing approved source column",
      "ambiguous candidate",
      "ECC",
      "PRODUCTION",
      "rollback baseline"
    )
    foreach ($Term in $RequiredTerms) {
        if ($Design -notmatch [regex]::Escape($Term)) { throw "Design draft missing: $Term" }
    }
}
```

Expected: no exception.

- [ ] **Step 3: Record the checkpoint**

Mark `Task 5: PASS` and state whether the design draft was generated or intentionally suppressed. Do not promote the tracked profile or create an onboarding PR.

---

### Task 6: Prove Determinism, Reconcile Counts, and Verify Safety

**Files:**
- Verify all local packet files.
- Verify tracked repository state.

**Interfaces:**
- Consumes: complete local audit packet.
- Produces: final reproducibility and safety verdict.

- [ ] **Step 1: Snapshot deterministic packet hashes**

```powershell
$DeterministicFiles = @(
  "audit_summary.md",
  "export_inventory.json",
  "header_hash_matrix.md",
  "pr_field_candidate_review.md",
  "non_empty_statistics.json",
  "rejected_candidates.md",
  "decision.json"
)
if (Test-Path "$AuditRoot/onboarding_design_draft.md") { $DeterministicFiles += "onboarding_design_draft.md" }

$Before = @{}
foreach ($Name in $DeterministicFiles) {
    $Before[$Name] = (Get-FileHash "$AuditRoot/$Name" -Algorithm SHA256).Hash
}
```

- [ ] **Step 2: Rerun the audit against the same inputs**

```powershell
python "$AuditRoot/run_cross_view_audit.py" `
  --reference-root "Info/reference" `
  --output-root "$AuditRoot"
```

Expected: included export count and decision are unchanged.

- [ ] **Step 3: Compare packet hashes**

```powershell
foreach ($Name in $DeterministicFiles) {
    $After = (Get-FileHash "$AuditRoot/$Name" -Algorithm SHA256).Hash
    if ($After -ne $Before[$Name]) { throw "Non-deterministic output: $Name" }
}
```

Expected: no exception.

- [ ] **Step 4: Reconcile inventory, statistics, matrix, and decision counts**

```powershell
$Inventory = Get-Content "$AuditRoot/export_inventory.json" -Raw | ConvertFrom-Json
$Stats = Get-Content "$AuditRoot/non_empty_statistics.json" -Raw | ConvertFrom-Json
$Decision = Get-Content "$AuditRoot/decision.json" -Raw | ConvertFrom-Json

$IncludedKeys = @($Inventory.included_exports.file_key | Sort-Object -Unique)
$StatsKeys = @($Stats.entries.file_key | Sort-Object -Unique)
foreach ($Key in $StatsKeys) {
    if ($Key -notin $IncludedKeys) { throw "Statistics reference excluded/unknown export: $Key" }
}
if (@($Decision.field_reviews.PSObject.Properties.Name).Count -ne 7) {
    throw "Decision must contain exactly seven field reviews."
}
```

Expected: no exception.

- [ ] **Step 5: Run final local tests and compile check**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
python -m py_compile "$AuditRoot/run_cross_view_audit.py" "$AuditRoot/test_run_cross_view_audit.py"
```

Expected: all local tests pass and compile exits `0`.

- [ ] **Step 6: Verify no tracked changes or sensitive tracked files exist**

```powershell
$Dirty = git status --short
if ($Dirty) {
    $Dirty
    throw "Audit modified tracked repository state."
}

$TrackedSensitive = git ls-files "Info/reference/**" "output/**"
if ($TrackedSensitive) {
    $TrackedSensitive
    throw "Local reference/output artifacts became tracked."
}

$CurrentTracked = git ls-files | Sort-Object
$PreflightTracked = Get-Content "$AuditRoot/preflight_tracked_files.txt" | Sort-Object
$Diff = Compare-Object $PreflightTracked $CurrentTracked
if ($Diff) {
    $Diff
    throw "Tracked file set changed during audit."
}
```

Expected: clean working tree, no tracked sensitive paths, and unchanged tracked file set.

- [ ] **Step 7: Verify no PR or ECC artifacts were generated**

```powershell
$Forbidden = Get-ChildItem $AuditRoot -Recurse -File | Where-Object {
    $_.Name -match "(?i)(ecc|pr_output|purchase_requisition|\.zip$)"
}
if ($Forbidden) {
    $Forbidden.FullName
    throw "Forbidden PR/ECC artifact generated."
}
```

Expected: no forbidden files.

- [ ] **Step 8: Finalize the progress ledger**

Record:

- included and excluded export counts;
- distinct View IDs and Header Hashes;
- status of all seven fields;
- final decision;
- whether `onboarding_design_draft.md` exists;
- local test count and result;
- deterministic rerun result;
- clean Git result;
- confirmation that no tracked file changed.

Mark `Task 6: PASS` and overall status as one of:

```text
DONE_READY_FOR_HUMAN_ONBOARDING_DESIGN_REVIEW
DONE_HUMAN_REVIEW_REQUIRED
DONE_KEEP_DRAFT_QUARANTINED
```

Do not commit any local output and do not create an onboarding PR.

---

## Final Execution Report

The agent's final response must contain:

- Status;
- branch and current commit SHA;
- target identity;
- number of local reference files discovered;
- number of included and excluded target exports;
- included filenames, View IDs, and Header Hashes;
- seven-field classification table;
- duplicate-prevention candidate fingerprints and safe non-empty statistics;
- rejected false positives;
- exact `decision.json.result`;
- whether `onboarding_design_draft.md` exists;
- local test and compile results;
- deterministic rerun result;
- `git status --short` result;
- confirmation that no tracked file, Profile, registry, script, `Info/reference`, or `output` artifact was changed or committed;
- path to the local audit packet;
- remaining concerns and the next human decision required.
