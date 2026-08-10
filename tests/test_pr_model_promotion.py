import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from promote_pr_model import PrModelPromotionError, promote_pr_model


def _write_model(path: Path, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "TX Line Item (After 21-Apr 26)"
    ws.append(["TX Site Survey"])
    ws.append(["TSS Model", "Code", "Description", "Unit", "Quantity", "Rules", "Remarks", "Remarks2"])
    ws.append(["BBU Patching", 1, "Survey", "Site", 1, "Mandatory", None, None])
    ws.append([])
    ws.append(["TX Installation"])
    ws.append(["TI Model", "Code", "Description", "Unit", "Quantity", "Rules", "Remarks", "Remarks2"])
    for row in rows:
        ws.append(row)
    wb.save(path)


def _write_baseline(root: Path, workbook: Path, version="4.0"):
    config = {
        "schema_version": "1.0",
        "baseline_id": "celcomdigi_tx_pr_model_current",
        "status": "PRODUCTION",
        "model": {"name": "CelcomDigi TX PR Model", "version": version},
        "workbook": {
            "path": "Info/input/pr_model.xlsx",
            "sha256": sha256(workbook.read_bytes()).hexdigest(),
        },
        "validation": {"mismatch_policy": "FAIL_CLOSED", "error_code": "PR_MODEL_BASELINE_MISMATCH"},
        "history_policy": {"runtime_keeps_only_current": True, "historical_source": "git_history"},
    }
    (root / "config").mkdir(exist_ok=True)
    (root / "config/pr_model_baseline.yaml").write_text(json.dumps(config, indent=2), encoding="utf-8")


def _write_approval(root: Path, candidate: Path, version: str, reason_codes, candidate_sha=None):
    approval = {
        "schema_version": "1.0",
        "status": "APPROVED",
        "candidate_version": version,
        "candidate_sha256": candidate_sha or sha256(candidate.read_bytes()).hexdigest(),
        "approved_reason_codes": list(reason_codes),
        "business_change_references": ["#77"],
    }
    path = root / "approval.json"
    path.write_text(json.dumps(approval, indent=2), encoding="utf-8")
    return path


def _write_audit_metadata(root: Path, current_sha: str):
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "config/registries").mkdir(parents=True, exist_ok=True)
    (root / "docs/pr_model_history.md").write_text(
        "# PR Model Production History\n\n"
        "| Version | SHA-256 | Production status | Notes |\n"
        "|---|---|---|---|\n"
        f"| v4.0 | `{current_sha}` | CURRENT | Current approved production workbook. |\n"
        "| v4.1 | `candidate` | CANDIDATE / REVIEW_REQUIRED | Pending. |\n\n"
        "## Operating standard\n\nRules.\n",
        encoding="utf-8",
    )
    (root / "docs/pr_model_reference_inventory.md").write_text(
        "# Inventory\n\n"
        "## Current production invariant\n\n"
        "```text\n"
        "version = 4.0\n"
        "path = Info/input/pr_model.xlsx\n"
        f"sha256 = {current_sha}\n"
        "```\n\n"
        "## v4.1 candidate status\n\nCandidate is blocked.\n\n"
        "## Historical isolation rule\n\nKeep history isolated.\n",
        encoding="utf-8",
    )
    registry = {
        "schema_version": "1.1",
        "source_evidence": "Evidence present in current approved PR Model v4.0.",
        "notes": ["runtime PR Model v4.0 validation remains authoritative"],
    }
    (root / "config/registries/canonical_sow_registry.yaml").write_text(
        json.dumps(registry, indent=2) + "\n",
        encoding="utf-8",
    )


class TestPrModelPromotion(unittest.TestCase):
    def test_review_required_candidate_does_not_touch_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            _write_model(current, [["MW Installation", 200, "Install", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [])
            _write_baseline(root, current)
            before_bytes = current.read_bytes()
            before_config = (root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8")

            with self.assertRaises(PrModelPromotionError) as ctx:
                promote_pr_model(candidate, "4.1", root=root)

            self.assertEqual(ctx.exception.code, "PR_MODEL_PROMOTION_REVIEW_REQUIRED")
            self.assertEqual(current.read_bytes(), before_bytes)
            self.assertEqual((root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8"), before_config)

    def test_review_approval_with_wrong_candidate_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            _write_model(current, [["MW Installation", 200, "Install", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [])
            _write_baseline(root, current)
            approval = _write_approval(root, candidate, "4.1", ["REMOVED_BUSINESS_ROWS"], candidate_sha="0" * 64)

            with self.assertRaises(PrModelPromotionError) as ctx:
                promote_pr_model(candidate, "4.1", root=root, approval_path=approval)

            self.assertEqual(ctx.exception.code, "PR_MODEL_PROMOTION_APPROVAL_INVALID")

    def test_review_approval_must_cover_every_reported_reason_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            _write_model(current, [["MW Installation", 200, "Install", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [["Brand New SOW", 300, "New", "Hop", 1, "Mandatory", None, None]])
            _write_baseline(root, current)
            approval = _write_approval(root, candidate, "4.1", ["REMOVED_BUSINESS_ROWS"])

            with self.assertRaises(PrModelPromotionError) as ctx:
                promote_pr_model(candidate, "4.1", root=root, approval_path=approval)

            self.assertEqual(ctx.exception.code, "PR_MODEL_PROMOTION_APPROVAL_INVALID")
            self.assertIn("NEW_SOW", ctx.exception.details["unapproved_reason_codes"])

    def test_valid_review_approval_unlocks_reviewed_changes_but_still_requires_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            _write_model(current, [["MW Installation", 200, "Install", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [])
            _write_baseline(root, current)
            approval = _write_approval(root, candidate, "4.1", ["REMOVED_BUSINESS_ROWS"])

            with patch("promote_pr_model._run_regression_gate", return_value={"status": "PASS"}) as gate:
                result = promote_pr_model(candidate, "4.1", root=root, approval_path=approval)

            gate.assert_called_once_with(root)
            self.assertEqual(result["status"], "PROMOTED")
            self.assertEqual(result["approval"]["business_change_references"], ["#77"])

    def test_regression_failure_rolls_back_workbook_config_and_audit_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            rows = [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]]
            _write_model(current, rows)
            _write_model(candidate, rows)
            _write_baseline(root, current)
            current_sha = sha256(current.read_bytes()).hexdigest()
            _write_audit_metadata(root, current_sha)
            tracked = [
                current,
                root / "config/pr_model_baseline.yaml",
                root / "docs/pr_model_history.md",
                root / "docs/pr_model_reference_inventory.md",
                root / "config/registries/canonical_sow_registry.yaml",
            ]
            before = {path: path.read_bytes() for path in tracked}

            failure = PrModelPromotionError(
                "PR_MODEL_REGRESSION_FAILED",
                "Regression gate failed.",
                {"returncode": 1},
            )
            with patch("promote_pr_model._run_regression_gate", side_effect=failure):
                with self.assertRaises(PrModelPromotionError) as ctx:
                    promote_pr_model(candidate, "4.1", root=root)

            self.assertEqual(ctx.exception.code, "PR_MODEL_REGRESSION_FAILED")
            for path, payload in before.items():
                self.assertEqual(path.read_bytes(), payload, path)

    def test_compatible_candidate_replaces_current_and_updates_identity_and_audit_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            rows = [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]]
            _write_model(current, rows)
            _write_model(candidate, rows)
            _write_baseline(root, current)
            current_sha = sha256(current.read_bytes()).hexdigest()
            _write_audit_metadata(root, current_sha)

            with patch("promote_pr_model._run_regression_gate", return_value={"status": "PASS"}) as gate:
                result = promote_pr_model(candidate, "4.1", root=root)
            config = json.loads((root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8"))
            candidate_sha = sha256(candidate.read_bytes()).hexdigest()

            gate.assert_called_once_with(root)
            self.assertEqual(result["status"], "PROMOTED")
            self.assertEqual(result["regression"]["status"], "PASS")
            self.assertEqual(config["model"]["version"], "4.1")
            self.assertEqual(config["workbook"]["sha256"], candidate_sha)
            self.assertEqual(current.read_bytes(), candidate.read_bytes())

            history = (root / "docs/pr_model_history.md").read_text(encoding="utf-8")
            self.assertIn(f"| v4.0 | `{current_sha}` | RETIRED |", history)
            self.assertIn(f"| v4.1 | `{candidate_sha}` | CURRENT |", history)

            inventory = (root / "docs/pr_model_reference_inventory.md").read_text(encoding="utf-8")
            self.assertIn("version = 4.1", inventory)
            self.assertIn(f"sha256 = {candidate_sha}", inventory)
            self.assertIn("## v4.1 production status", inventory)
            self.assertNotIn("## v4.1 candidate status", inventory)

            registry = (root / "config/registries/canonical_sow_registry.yaml").read_text(encoding="utf-8")
            self.assertIn("PR Model v4.1", registry)
            self.assertNotIn("PR Model v4.0", registry)
            self.assertEqual(
                set(result["audit_metadata_updated"]),
                {
                    "docs/pr_model_history.md",
                    "docs/pr_model_reference_inventory.md",
                    "config/registries/canonical_sow_registry.yaml",
                },
            )


if __name__ == "__main__":
    unittest.main()
