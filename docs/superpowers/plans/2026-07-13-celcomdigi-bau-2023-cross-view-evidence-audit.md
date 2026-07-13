# 2023 Celcomdigi BAU Cross-View Evidence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic, local-only evidence packet that audits every local `Malaysia_CelcomDigi_Project + 2023 Celcomdigi BAU` export across Views and decides whether a later non-production `PR_INPUT_READY` onboarding design can be prepared.

**Architecture:** Reuse the repository's read-only local inventory and four-header profiler. Add one ignored local aggregation helper plus one ignored local test module under the audit output directory. The helper identifies the target Project + DU Model, profiles exact four-layer fingerprints, gathers redacted value statistics, classifies seven target fields, writes the required packet, and conditionally writes an onboarding design draft without changing tracked implementation.

**Tech Stack:** Python 3, standard library (`argparse`, `csv`, `hashlib`, `json`, `re`, `collections`, `pathlib`), `openpyxl`, `unittest`, Windows PowerShell, Git.

## Global Constraints

- Repository: `Gumb-D/create-pr-cd`.
- Local repository path: `C:\dev\create-pr-cd`.
- Approved spec: `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md`.
- Target Project: `Malaysia_CelcomDigi_Project`.
- Target Project export token: `P202202168750`.
- Target DU Model: `2023 Celcomdigi BAU`.
- Target DU Model ID: `8296022438223590261`.
- Target tracked profile: `celcomdigi_bau_2023_pr_v1`.
- Target profile must remain `DRAFT` throughout this audit.
- View ID is evidence metadata, not an identity boundary.
- Audit exactly: `site_code`, `tx_sow_raw`, `region`, `subcontractor_tss`, `subcontractor_ti`, `existing_tss_pr_status`, `existing_ti_pr_status`.
- Other DU Models may provide search vocabulary only; they may not provide approval evidence.
- All runtime helpers, tests, inventories, statistics, decisions, logs, and drafts must remain under `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/`.
- Do not modify any tracked Profile, registry, script, test, ECC template, PR model, SOW rule, or documentation during audit execution.
- Do not add or force-add anything under `Info/reference` or `output`.
- Do not generate PR or ECC output.
- Do not create an onboarding PR.
- Do not promote any profile to `PR_INPUT_READY` or `PRODUCTION`.
- Write `onboarding_design_draft.md` only when `decision.json.result` is exactly `ONBOARDING_DESIGN_READY`.
- Git working tree must be clean before and after the audit.

## File Map

Tracked files used read-only:

- `scripts/discover_local_du_references.py` — inventories local reference files and infers candidate DU Model names.
- `scripts/profile_du_export.py` — reads four Header layers and calculates deterministic Header Hashes.
- `config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml` — current DRAFT baseline.
- `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md` — approved contract.

Local-only files created:

- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/run_cross_view_audit.py`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/test_run_cross_view_audit.py`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/progress_ledger.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/preflight_tracked_files.txt`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.json`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/local_reference_inventory.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/profiles/<file-key>/header_inventory.json`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/profiles/<file-key>/header_hash.txt`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/audit_summary.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/export_inventory.json`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/header_hash_matrix.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/pr_field_candidate_review.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/non_empty_statistics.json`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/rejected_candidates.md`
- `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/decision.json`
- conditional: `output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit/onboarding_design_draft.md`

---

### Task 1: Establish a Clean Local Audit Workspace

**Files:**
- Read: approved spec and current DRAFT profile.
- Create: `progress_ledger.md` and `preflight_tracked_files.txt` under the audit root.

**Interfaces:**
- Consumes: clean checkout of `docs/celcomdigi-bau-2023-evidence-audit-design`.
- Produces: stable audit root and tracked-state baseline.

- [ ] **Step 1: Check out the documentation branch and verify a clean tree**

```powershell
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location C:\dev\create-pr-cd

git fetch origin --prune
git switch docs/celcomdigi-bau-2023-evidence-audit-design
git pull --ff-only origin docs/celcomdigi-bau-2023-evidence-audit-design

$Dirty = git status --short
if ($Dirty) {
    $Dirty
    throw "Working tree must be clean before the audit."
}

git log -4 --oneline
```

Expected: clean tree; log includes the approved spec and this plan.

- [ ] **Step 2: Create the ignored audit root and baseline files**

```powershell
$AuditRoot = "output/all_remaining_du_human_review/celcomdigi_bau_2023_cross_view_audit"
New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null

git ls-files | Sort-Object | Set-Content "$AuditRoot/preflight_tracked_files.txt" -Encoding utf8

@"
# 2023 Celcomdigi BAU Cross-View Audit Progress

- Repository preflight: PASS
- Target Project: Malaysia_CelcomDigi_Project
- Target DU Model: 2023 Celcomdigi BAU
- Target DU Model ID: 8296022438223590261
- Tracked lifecycle: DRAFT
- Task 1: IN_PROGRESS
- Task 2: PENDING
- Task 3: PENDING
- Task 4: PENDING
- Task 5: PENDING
- Task 6: PENDING
"@ | Set-Content "$AuditRoot/progress_ledger.md" -Encoding utf8
```

- [ ] **Step 3: Verify local references exist and sensitive paths are untracked**

```powershell
if (-not (Test-Path "Info/reference")) { throw "Info/reference is missing." }
$ReferenceFiles = Get-ChildItem "Info/reference" -Recurse -File | Where-Object {
    $_.Extension.ToLowerInvariant() -in ".xlsx", ".xlsm", ".csv", ".xls"
}
if (-not $ReferenceFiles) { throw "No local reference exports were found." }

$TrackedSensitive = git ls-files "Info/reference/**" "output/**"
if ($TrackedSensitive) {
    $TrackedSensitive
    throw "Sensitive local files are tracked."
}
```

Expected: at least one local reference; no tracked `Info/reference` or `output` path.

- [ ] **Step 4: Record Task 1 as PASS**

Update the local ledger. Do not commit any local output.

---

### Task 2: Build the Local-Only Aggregator with TDD

**Files:**
- Create: `run_cross_view_audit.py` under the audit root.
- Create: `test_run_cross_view_audit.py` under the audit root.
- Read: `scripts/discover_local_du_references.py` and `scripts/profile_du_export.py`.

**Interfaces:**
- Consumes:
  - `discover_reference_files(reference_root: Path) -> list[dict]`
  - `build_header_inventory(input_path: Path) -> dict`
  - `calculate_header_hash(inventory: Mapping[str, Any]) -> str`
- Produces:
  - `safe_value_pattern(value: Any) -> str`
  - `classify_value_type(values: Sequence[Any]) -> str`
  - `extract_identity_evidence(inventory: Mapping[str, Any]) -> dict`
  - `candidate_matches_target(fingerprint: Mapping[str, str], target_field: str) -> bool`
  - `collect_column_statistics(path: Path, sheet_name: str, one_based_index: int) -> dict`
  - `classify_candidate(target_field: str, fingerprint: Mapping[str, str], statistics: Mapping[str, Any]) -> dict`
  - `decide_audit(field_reviews: Mapping[str, Any]) -> str`
  - `run_audit(reference_root: Path, output_root: Path) -> dict`

- [ ] **Step 1: Write the failing local tests**

Create `test_run_cross_view_audit.py`:

```python
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

MODULE_PATH = Path(__file__).with_name("run_cross_view_audit.py")
spec = importlib.util.spec_from_file_location("run_cross_view_audit", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class TestCrossViewAudit(unittest.TestCase):
    def test_safe_value_pattern_redacts_values(self):
        self.assertEqual(module.safe_value_pattern("PR-2023-000123"), "AA-9999-999999")
        self.assertEqual(module.safe_value_pattern("Approved"), "TEXT[len=8]")
        self.assertEqual(module.safe_value_pattern("2026-07-13"), "DATE_PATTERN")

    def test_identity_is_extracted_from_site_code_field(self):
        inventory = {
            "sheets": [{
                "sheet_name": "DU Export",
                "columns": [{
                    "fingerprint": {
                        "field_code": "site|fix00012|8296022438223590261|6611960521271999255",
                        "wbs_stage": "Site Basic Info",
                        "task_name": "Site Basic Info",
                        "display_header": "customer site code",
                    }
                }],
            }]
        }
        evidence = module.extract_identity_evidence(inventory)
        self.assertEqual(evidence["du_model_ids"], ["8296022438223590261"])
        self.assertEqual(evidence["view_ids"], ["6611960521271999255"])
        self.assertFalse(evidence["conflict"])

    def test_candidate_matching_uses_all_header_layers(self):
        fingerprint = {
            "field_code": "docata|ZDCSZ641766",
            "wbs_stage": "Installation",
            "task_name": "Wireless RAN",
            "display_header": "Subcon PR - TSS",
        }
        self.assertTrue(module.candidate_matches_target(fingerprint, "existing_tss_pr_status"))
        self.assertFalse(module.candidate_matches_target(fingerprint, "existing_ti_pr_status"))

    def test_milestone_date_is_rejected(self):
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

    def test_xlsx_and_csv_statistics_are_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xlsx = root / "sample.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "DU Export"
            for row in [["id"], ["stage"], ["task"], ["Subcon PR - TSS"], ["PR-1"], [None], ["PR-2"]]:
                sheet.append(row)
            workbook.save(xlsx)

            csv_path = root / "sample.csv"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
                csv.writer(handle).writerows([["id"], ["stage"], ["task"], ["Subcon PR - TSS"], ["PR-1"], [""], ["PR-2"]])

            for path, sheet_name in ((xlsx, "DU Export"), (csv_path, "CSV")):
                stats = module.collect_column_statistics(path, sheet_name, 1)
                self.assertEqual(stats["total_data_rows"], 3)
                self.assertEqual(stats["non_empty_rows"], 2)
                self.assertEqual(stats["blank_rows"], 1)

    def test_decision_requires_all_seven_unique_direct_candidates(self):
        ready = {
            field: {"status": "DIRECT_APPROVAL_CANDIDATE", "unique_per_header_hash": True}
            for field in module.TARGET_FIELDS
        }
        self.assertEqual(module.decide_audit(ready), "ONBOARDING_DESIGN_READY")
        ready["existing_ti_pr_status"] = {"status": "MISSING", "unique_per_header_hash": False}
        self.assertEqual(module.decide_audit(ready), "KEEP_DRAFT_QUARANTINED")

    def test_design_is_conditional_and_json_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.write_conditional_design(root, "HUMAN_REVIEW_REQUIRED", {})
            self.assertFalse((root / "onboarding_design_draft.md").exists())
            module.write_conditional_design(root, "ONBOARDING_DESIGN_READY", {"field_reviews": {}})
            self.assertTrue((root / "onboarding_design_draft.md").exists())

            path = root / "payload.json"
            module.write_json(path, {"b": 2, "a": 1})
            first = path.read_bytes()
            module.write_json(path, {"a": 1, "b": 2})
            self.assertEqual(first, path.read_bytes())
            self.assertEqual(json.loads(first), {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and confirm the expected red state**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
```

Expected: failure because `run_cross_view_audit.py` does not exist.

- [ ] **Step 3: Implement the helper constants, imports, redaction, identity extraction, matching, and deterministic JSON**

The helper must begin with:

```python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from discover_local_du_references import discover_reference_files
from profile_du_export import build_header_inventory, calculate_header_hash

TARGET_PROJECT = "Malaysia_CelcomDigi_Project"
TARGET_PROJECT_EXPORT_TOKEN = "P202202168750"
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
SITE_ID_FIELD_RE = re.compile(
    r"^site\|fix00012\|(?P<du_model_id>\d+)\|(?P<view_id>\d+)$",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T].*)?$")
TOKEN_RE = re.compile(r"[A-Za-z]+|\d+")
FIELD_TERMS = {
    "site_code": (("customer", "site", "code"),),
    "tx_sow_raw": (("tx", "sow"),),
    "region": (("region",),),
    "subcontractor_tss": (("subcon", "tss"), ("subcontractor", "tss")),
    "subcontractor_ti": (("subcon", "ti"), ("subcontractor", "ti")),
    "existing_tss_pr_status": (("subcon", "pr", "tss"), ("pr", "tss", "status"), ("tss", "pr")),
    "existing_ti_pr_status": (("subcon", "pr", "ti"), ("pr", "ti", "status"), ("ti", "pr")),
}


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
    if any(character.isdigit() for character in text):
        tokens = TOKEN_RE.findall(text)
        separators = re.findall(r"[^A-Za-z0-9]+", text)
        masked = [("9" * len(token)) if token.isdigit() else ("A" * len(token)) for token in tokens]
        result = masked[0]
        for separator, token in zip(separators, masked[1:]):
            result += separator + token
        return result
    return f"TEXT[len={len(text)}]"


def header_text(fingerprint: Mapping[str, str]) -> str:
    return " ".join(
        normalize(fingerprint.get(key, ""))
        for key in ("field_code", "wbs_stage", "task_name", "display_header")
    ).lower()


def extract_identity_evidence(inventory: Mapping[str, Any]) -> dict[str, Any]:
    model_ids: set[str] = set()
    view_ids: set[str] = set()
    for sheet in inventory.get("sheets", []):
        for column in sheet.get("columns", []):
            field_code = normalize(column.get("fingerprint", {}).get("field_code"))
            match = SITE_ID_FIELD_RE.match(field_code)
            if match:
                model_ids.add(match.group("du_model_id"))
                view_ids.add(match.group("view_id"))
    return {
        "du_model_ids": sorted(model_ids),
        "view_ids": sorted(view_ids),
        "conflict": len(model_ids) > 1 or (bool(model_ids) and TARGET_DU_MODEL_ID not in model_ids),
    }


def candidate_matches_target(fingerprint: Mapping[str, str], target_field: str) -> bool:
    text = header_text(fingerprint)
    return any(all(term in text for term in terms) for terms in FIELD_TERMS[target_field])
```

- [ ] **Step 4: Implement value typing and both XLSX/CSV statistics paths**

```python
def classify_value_type(values: Sequence[Any]) -> str:
    non_empty = [value for value in values if normalize(value)]
    if not non_empty:
        return "empty"
    patterns = [safe_value_pattern(value) for value in non_empty]
    if set(patterns) == {"DATE_PATTERN"}:
        return "date"
    lowered = {normalize(value).lower() for value in non_empty}
    if lowered <= {"yes", "no", "y", "n", "true", "false", "0", "1"}:
        return "boolean_like"
    if all(any(character.isdigit() for character in normalize(value)) for value in non_empty):
        return "reference_or_mixed_identifier"
    if len(lowered) <= 20:
        return "status_or_categorical_text"
    return "free_text_or_mixed"


def read_column_values(path: Path, sheet_name: str, one_based_index: int) -> list[Any]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            worksheet = workbook[sheet_name]
            return [
                row[0].value
                for row in worksheet.iter_rows(
                    min_row=5,
                    min_col=one_based_index,
                    max_col=one_based_index,
                )
            ]
        finally:
            workbook.close()
    if suffix == ".csv":
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                with path.open("r", encoding=encoding, newline="") as handle:
                    rows = list(csv.reader(handle))[4:]
                return [row[one_based_index - 1] if len(row) >= one_based_index else "" for row in rows]
            except UnicodeDecodeError as error:
                last_error = error
        raise last_error or ValueError(f"Unable to decode CSV: {path}")
    raise ValueError(f"Unsupported statistics format: {suffix}")


def collect_column_statistics(path: Path, sheet_name: str, one_based_index: int) -> dict[str, Any]:
    values = read_column_values(path, sheet_name, one_based_index)
    non_empty = [value for value in values if normalize(value)]
    patterns = Counter(safe_value_pattern(value) for value in non_empty)
    return {
        "total_data_rows": len(values),
        "non_empty_rows": len(non_empty),
        "blank_rows": len(values) - len(non_empty),
        "unique_non_empty_values": len({normalize(value) for value in non_empty}),
        "value_type": classify_value_type(non_empty),
        "safe_example_patterns": [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted(patterns.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
    }
```

- [ ] **Step 5: Implement classification and exact decision rules**

```python
def classify_candidate(
    target_field: str,
    fingerprint: Mapping[str, str],
    statistics: Mapping[str, Any],
) -> dict[str, Any]:
    text = header_text(fingerprint)
    non_empty = int(statistics.get("non_empty_rows", 0))
    value_type = statistics.get("value_type", "empty")
    mismatch_terms = (
        "plan_start_date",
        "actual_start_date",
        "planned start time",
        "actual start time",
        "tssr customer approval",
    )

    if target_field in {"existing_tss_pr_status", "existing_ti_pr_status"}:
        if value_type == "date" or any(term in text for term in mismatch_terms):
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif target_field == "existing_ti_pr_status" and "planning" in text:
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif not candidate_matches_target(fingerprint, target_field):
            classification = "REJECTED_SEMANTIC_MISMATCH"
        elif non_empty == 0:
            classification = "HUMAN_REVIEW_REQUIRED"
        elif value_type in {
            "status_or_categorical_text",
            "reference_or_mixed_identifier",
            "free_text_or_mixed",
        }:
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
    statuses = {
        field: field_reviews.get(field, {}).get("status", "MISSING")
        for field in TARGET_FIELDS
    }
    for duplicate_field in ("existing_tss_pr_status", "existing_ti_pr_status"):
        if statuses[duplicate_field] in {"MISSING", "REJECTED_SEMANTIC_MISMATCH"}:
            return "KEEP_DRAFT_QUARANTINED"
    if all(
        statuses[field] == "DIRECT_APPROVAL_CANDIDATE"
        and field_reviews[field].get("unique_per_header_hash") is True
        for field in TARGET_FIELDS
    ):
        return "ONBOARDING_DESIGN_READY"
    return "HUMAN_REVIEW_REQUIRED"
```

- [ ] **Step 6: Implement deterministic source selection and packet generation**

`run_audit(reference_root, output_root)` must implement this exact sequence:

1. Call `discover_reference_files(reference_root)`.
2. For each `.xlsx`, `.xlsm`, or `.csv` file, build the four-header inventory and identity evidence.
3. Include a file only when:
   - `candidate_du_model == "2023 Celcomdigi BAU"`;
   - filename contains `P202202168750`;
   - identity evidence is not conflicting;
   - if a DU Model ID is present, it equals `8296022438223590261`.
4. Exclude `.xls` as `UNSUPPORTED_LEGACY_FORMAT` and document it.
5. Record excluded files with one exact reason from:
   - `OTHER_DU_MODEL`;
   - `PROJECT_TOKEN_MISMATCH`;
   - `DU_MODEL_ID_CONFLICT`;
   - `UNSUPPORTED_LEGACY_FORMAT`;
   - `READ_ERROR`.
6. Set included export metadata fields:
   - `file_key` = first 16 hex characters of SHA-256 of the file's relative path;
   - `relative_path`;
   - `source_file_name`;
   - `source_file_hash` from profiler inventory;
   - `project_key = TARGET_PROJECT`;
   - `du_model_name = TARGET_DU_MODEL`;
   - detected DU Model IDs;
   - detected View IDs;
   - Header Hash;
   - sheet names;
   - inclusion rationale.
7. Save each exact profiler inventory under `profiles/<file-key>/header_inventory.json` and Header Hash under `profiles/<file-key>/header_hash.txt`.
8. Search every complete fingerprint against every target field.
9. Gather safe statistics from the exact sheet and `one_based_index`.
10. Classify every candidate.
11. Consolidate candidates by target field and Header Hash.
12. For each field:
    - `DIRECT_APPROVAL_CANDIDATE` only when every included Header Hash has exactly one direct candidate;
    - `HUMAN_REVIEW_REQUIRED` when any Header Hash has multiple direct/plausible candidates, an empty plausible candidate, or incompatible View-specific semantics;
    - `REJECTED_SEMANTIC_MISMATCH` when same-DU candidates exist but all are rejected;
    - `MISSING` when no same-DU candidate exists.
13. Set `unique_per_header_hash = true` only when every included Header Hash resolves to exactly one direct candidate.
14. Call `decide_audit`.
15. Write the seven required packet files with sorted keys, stable ordering, no generation timestamp, and no unrestricted raw value.
16. Call `write_conditional_design`.
17. Return the full deterministic audit payload.

The CLI must be:

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local-only 2023 Celcomdigi BAU cross-View evidence audit"
    )
    parser.add_argument("--reference-root", default="Info/reference")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_audit(Path(args.reference_root), Path(args.output_root))
    print(f"Included exports: {len(result['included_exports'])}")
    print(f"Excluded exports: {len(result['excluded_exports'])}")
    print(f"Decision: {result['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: Implement conditional onboarding design output**

`write_conditional_design(output_root, decision, audit)` must:

- delete an existing design draft when decision is not `ONBOARDING_DESIGN_READY`;
- otherwise write:
  - retained profile ID;
  - proposed profile version `0.2.0`;
  - proposed mapping version placeholder format `approved-YYYY-MM-DD-2023-celcomdigi-bau-v1` clearly marked as a draft value;
  - Project + DU Model identity;
  - all detected View IDs;
  - all proposed Header Hashes;
  - exact accepted four-layer fingerprints for all seven fields;
  - `normalize_pr_reference_status` for both existing-PR fields;
  - changed-hash, missing-column, ambiguous-source, and blank scope-specific subcontractor tests;
  - rollback baseline;
  - lifecycle ceiling `PR_INPUT_READY`;
  - ECC remains blocked until separate `PRODUCTION` approval and golden-output evidence.

- [ ] **Step 8: Run tests and compile check**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
python -m py_compile "$AuditRoot/run_cross_view_audit.py" "$AuditRoot/test_run_cross_view_audit.py"
```

Expected: `Ran 7 tests`, `OK`, and compile exit code `0`.

- [ ] **Step 9: Record Task 2 as PASS**

Update the ledger with test count and compile result. Confirm `git status --short` is empty. Do not commit ignored helper code.

---

### Task 3: Inventory and Profile All In-Scope Exports

**Files:**
- Create: local inventory metadata and per-export profiler outputs.
- Verify: included/excluded export identity.

**Interfaces:**
- Consumes: tracked inventory helper and tested local aggregator.
- Produces: exact included export set, View IDs, DU Model IDs, and Header Hashes.

- [ ] **Step 1: Run the tracked reference inventory**

```powershell
python scripts/discover_local_du_references.py `
  --reference-root "Info/reference" `
  --output "$AuditRoot/local_reference_inventory.json"
```

- [ ] **Step 2: Run the cross-View audit**

```powershell
python "$AuditRoot/run_cross_view_audit.py" `
  --reference-root "Info/reference" `
  --output-root "$AuditRoot"
```

Expected: at least one included export and one exact decision value.

- [ ] **Step 3: Verify identity of every included export**

```powershell
$Inventory = Get-Content "$AuditRoot/export_inventory.json" -Raw | ConvertFrom-Json
if (-not $Inventory.included_exports) { throw "No target exports were included." }
foreach ($Export in $Inventory.included_exports) {
    if ($Export.project_key -ne "Malaysia_CelcomDigi_Project") { throw "Project mismatch" }
    if ($Export.du_model_name -ne "2023 Celcomdigi BAU") { throw "DU Model mismatch" }
    if ($Export.source_file_name -notmatch "P202202168750") { throw "Project token mismatch" }
    foreach ($ModelId in $Export.detected_du_model_ids) {
        if ($ModelId -ne "8296022438223590261") { throw "DU Model ID mismatch" }
    }
    if (-not $Export.header_hash) { throw "Missing Header Hash" }
}
```

- [ ] **Step 4: Verify complete fingerprints and safe statistics**

```powershell
$Stats = Get-Content "$AuditRoot/non_empty_statistics.json" -Raw | ConvertFrom-Json
foreach ($Entry in $Stats.entries) {
    foreach ($Key in "field_code", "wbs_stage", "task_name", "display_header") {
        if ($null -eq $Entry.fingerprint.$Key) { throw "Incomplete fingerprint" }
    }
    if ($Entry.safe_example_patterns.Count -gt 10) { throw "Too many example patterns" }
}
```

- [ ] **Step 5: Record Task 3 as PASS**

Record discovered, included, excluded, View ID, and Header Hash counts in the ledger.

---

### Task 4: Review Seven Fields and Validate the Decision

**Files:**
- Verify: `pr_field_candidate_review.md`, `non_empty_statistics.json`, `rejected_candidates.md`, `decision.json`.

**Interfaces:**
- Consumes: exact fingerprints and safe statistics.
- Produces: one status per target field and one exact decision.

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

- [ ] **Step 2: Manually verify duplicate-prevention semantics**

Confirm in the generated Markdown reviews that:

- planned/actual timestamps are rejected;
- TSSR approval dates are rejected;
- `Subcon PR - Planning` is rejected for TI duplicate prevention;
- fields from another DU Model are not accepted;
- accepted existing-PR candidates have non-empty, non-date value evidence;
- redacted pattern examples are sufficient to identify status/reference semantics without revealing raw site rows.

Any violation requires a local regression test, helper correction, and full Task 3 rerun.

- [ ] **Step 3: Validate the exact decision contract**

```powershell
$Allowed = @("ONBOARDING_DESIGN_READY", "HUMAN_REVIEW_REQUIRED", "KEEP_DRAFT_QUARANTINED")
if ($Decision.result -notin $Allowed) { throw "Invalid decision" }

if ($Decision.result -eq "ONBOARDING_DESIGN_READY") {
    foreach ($Field in $ExpectedFields) {
        $Review = $Decision.field_reviews.$Field
        if ($Review.status -ne "DIRECT_APPROVAL_CANDIDATE") { throw "Non-direct ready field: $Field" }
        if ($Review.unique_per_header_hash -ne $true) { throw "Non-unique ready field: $Field" }
    }
}

if ($Decision.result -eq "KEEP_DRAFT_QUARANTINED") {
    $Tss = $Decision.field_reviews.existing_tss_pr_status.status
    $Ti = $Decision.field_reviews.existing_ti_pr_status.status
    if (($Tss -notin @("MISSING", "REJECTED_SEMANTIC_MISMATCH")) -and
        ($Ti -notin @("MISSING", "REJECTED_SEMANTIC_MISMATCH"))) {
        throw "Quarantine lacks duplicate-prevention blocker"
    }
}
```

- [ ] **Step 4: Record Task 4 as PASS**

Record each field status, accepted/rejected candidate counts, and the exact decision.

---

### Task 5: Generate or Suppress the Conditional Design Draft

**Files:**
- Conditional: `onboarding_design_draft.md`.
- Verify: `decision.json`.

**Interfaces:**
- Consumes: final decision and accepted candidate matrix.
- Produces: onboarding design only for a ready result.

- [ ] **Step 1: Enforce conditional existence**

```powershell
$Decision = Get-Content "$AuditRoot/decision.json" -Raw | ConvertFrom-Json
$DesignPath = "$AuditRoot/onboarding_design_draft.md"
if ($Decision.result -eq "ONBOARDING_DESIGN_READY") {
    if (-not (Test-Path $DesignPath)) { throw "Ready decision requires design draft" }
} elseif (Test-Path $DesignPath) {
    throw "Non-ready decision must not produce design draft"
}
```

- [ ] **Step 2: For a ready result, verify mandatory controls**

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
      "ambiguous",
      "rollback baseline",
      "ECC",
      "PRODUCTION"
    )
    foreach ($Term in $RequiredTerms) {
        if ($Design -notmatch [regex]::Escape($Term)) { throw "Design missing: $Term" }
    }
}
```

- [ ] **Step 3: Record Task 5 as PASS**

State whether the design was generated or correctly suppressed. Do not modify the tracked profile.

---

### Task 6: Prove Determinism and Repository Safety

**Files:**
- Verify: all packet files and Git state.

**Interfaces:**
- Consumes: completed local packet.
- Produces: final reproducibility and safety verdict.

- [ ] **Step 1: Hash deterministic packet files**

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
if (Test-Path "$AuditRoot/onboarding_design_draft.md") {
    $DeterministicFiles += "onboarding_design_draft.md"
}
$Before = @{}
foreach ($Name in $DeterministicFiles) {
    $Before[$Name] = (Get-FileHash "$AuditRoot/$Name" -Algorithm SHA256).Hash
}
```

- [ ] **Step 2: Rerun the audit and compare hashes**

```powershell
python "$AuditRoot/run_cross_view_audit.py" `
  --reference-root "Info/reference" `
  --output-root "$AuditRoot"

foreach ($Name in $DeterministicFiles) {
    $After = (Get-FileHash "$AuditRoot/$Name" -Algorithm SHA256).Hash
    if ($After -ne $Before[$Name]) { throw "Non-deterministic output: $Name" }
}
```

- [ ] **Step 3: Reconcile packet references**

```powershell
$Inventory = Get-Content "$AuditRoot/export_inventory.json" -Raw | ConvertFrom-Json
$Stats = Get-Content "$AuditRoot/non_empty_statistics.json" -Raw | ConvertFrom-Json
$Decision = Get-Content "$AuditRoot/decision.json" -Raw | ConvertFrom-Json

$IncludedKeys = @($Inventory.included_exports.file_key | Sort-Object -Unique)
foreach ($Key in @($Stats.entries.file_key | Sort-Object -Unique)) {
    if ($Key -notin $IncludedKeys) { throw "Statistics reference unknown export: $Key" }
}
if (@($Decision.field_reviews.PSObject.Properties.Name).Count -ne 7) {
    throw "Decision must contain exactly seven field reviews"
}
```

- [ ] **Step 4: Run final local tests and compile check**

```powershell
python "$AuditRoot/test_run_cross_view_audit.py" -v
python -m py_compile "$AuditRoot/run_cross_view_audit.py" "$AuditRoot/test_run_cross_view_audit.py"
```

Expected: `Ran 7 tests`, `OK`, compile exit `0`.

- [ ] **Step 5: Verify tracked state is unchanged**

```powershell
$Dirty = git status --short
if ($Dirty) {
    $Dirty
    throw "Audit changed tracked repository state"
}

$TrackedSensitive = git ls-files "Info/reference/**" "output/**"
if ($TrackedSensitive) {
    $TrackedSensitive
    throw "Sensitive local path became tracked"
}

$CurrentTracked = git ls-files | Sort-Object
$PreflightTracked = Get-Content "$AuditRoot/preflight_tracked_files.txt" | Sort-Object
$TrackedDiff = Compare-Object $PreflightTracked $CurrentTracked
if ($TrackedDiff) {
    $TrackedDiff
    throw "Tracked file set changed during audit"
}
```

- [ ] **Step 6: Verify no PR/ECC deliverable was generated**

```powershell
$Forbidden = Get-ChildItem $AuditRoot -Recurse -File | Where-Object {
    $_.Name -match "(?i)(ecc_output|pr_output|purchase_requisition|\.zip$)"
}
if ($Forbidden) {
    $Forbidden.FullName
    throw "Forbidden PR/ECC artifact generated"
}
```

- [ ] **Step 7: Finalize the progress ledger**

Record:

- discovered, included, and excluded export counts;
- included filenames, View IDs, and Header Hashes;
- seven field statuses;
- duplicate-prevention candidates and safe statistics;
- rejected semantic false positives;
- exact decision;
- design draft generated or suppressed;
- local test result;
- deterministic rerun result;
- clean Git result;
- confirmation that no tracked file changed.

Set overall status to exactly one of:

```text
DONE_READY_FOR_HUMAN_ONBOARDING_DESIGN_REVIEW
DONE_HUMAN_REVIEW_REQUIRED
DONE_KEEP_DRAFT_QUARANTINED
```

Do not commit local audit outputs and do not create an onboarding PR.

---

## Final Execution Report

The agent's final response must include:

- Status;
- branch and current commit SHA;
- target identity;
- total local reference files discovered;
- included and excluded target export counts;
- included filenames, View IDs, and Header Hashes;
- seven-field classification table;
- exact duplicate-prevention fingerprints and safe non-empty statistics;
- rejected false positives;
- `decision.json.result`;
- whether `onboarding_design_draft.md` exists;
- local unit-test and compile results;
- deterministic rerun result;
- `git status --short` result;
- confirmation that no tracked Profile, registry, script, test, `Info/reference`, or `output` artifact changed or was committed;
- local packet path;
- remaining concerns and next human decision.
