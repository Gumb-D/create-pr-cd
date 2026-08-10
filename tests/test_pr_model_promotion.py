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

    def test_regression_failure_does_not_touch_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            rows = [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]]
            _write_model(current, rows)
            _write_model(candidate, rows)
            _write_baseline(root, current)
            before_bytes = current.read_bytes()
            before_config = (root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8")

            failure = PrModelPromotionError(
                "PR_MODEL_REGRESSION_FAILED",
                "Regression gate failed.",
                {"returncode": 1},
            )
            with patch("promote_pr_model._run_regression_gate", side_effect=failure):
                with self.assertRaises(PrModelPromotionError) as ctx:
                    promote_pr_model(candidate, "4.1", root=root)

            self.assertEqual(ctx.exception.code, "PR_MODEL_REGRESSION_FAILED")
            self.assertEqual(current.read_bytes(), before_bytes)
            self.assertEqual((root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8"), before_config)

    def test_compatible_candidate_replaces_current_and_updates_identity_after_regression_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Info/input").mkdir(parents=True)
            current = root / "Info/input/pr_model.xlsx"
            candidate = root / "candidate.xlsx"
            rows = [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]]
            _write_model(current, rows)
            _write_model(candidate, rows)
            _write_baseline(root, current)

            with patch("promote_pr_model._run_regression_gate", return_value={"status": "PASS"}) as gate:
                result = promote_pr_model(candidate, "4.1", root=root)
            config = json.loads((root / "config/pr_model_baseline.yaml").read_text(encoding="utf-8"))

            gate.assert_called_once_with(root)
            self.assertEqual(result["status"], "PROMOTED")
            self.assertEqual(result["regression"]["status"], "PASS")
            self.assertEqual(config["model"]["version"], "4.1")
            self.assertEqual(config["workbook"]["sha256"], sha256(candidate.read_bytes()).hexdigest())
            self.assertEqual(current.read_bytes(), candidate.read_bytes())


if __name__ == "__main__":
    unittest.main()
