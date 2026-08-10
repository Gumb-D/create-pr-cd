import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analyze_pr_model_change import analyze_pr_model_change


def _write_model(path: Path, ti_rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "TX Line Item (After 21-Apr 26)"
    ws.append(["TX Site Survey"])
    ws.append(["TSS Model", "Code", "Description", "Unit", "Quantity", "Rules", "Remarks", "Remarks2"])
    ws.append(["BBU Patching", 1, "Survey", "Site", 1, "Mandatory", None, None])
    ws.append([])
    ws.append(["TX Installation"])
    ws.append(["TI Model", "Code", "Description", "Unit", "Quantity", "Rules", "Remarks", "Remarks2"])
    for row in ti_rows:
        ws.append(row)
    wb.save(path)


class TestPrModelChangeAnalyzer(unittest.TestCase):
    def test_identical_models_are_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current.xlsx"
            candidate = Path(tmp) / "candidate.xlsx"
            rows = [["MW Hardware Upgrade", 100, "Swap IDU", "Hop", 1, "Mandatory", None, None]]
            _write_model(current, rows)
            _write_model(candidate, rows)
            report = analyze_pr_model_change(current, candidate)
        self.assertEqual(report["status"], "COMPATIBLE")
        self.assertEqual(report["removed_count"], 0)
        self.assertEqual(report["added_count"], 0)

    def test_removed_current_business_row_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current.xlsx"
            candidate = Path(tmp) / "candidate.xlsx"
            _write_model(current, [["MW Installation", 200, "Install", "Hop", 1, "Mandatory", "Jendela", None]])
            _write_model(candidate, [])
            report = analyze_pr_model_change(current, candidate)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["removed_count"], 1)
        self.assertIn("REMOVED_BUSINESS_ROWS", report["reason_codes"])

    def test_new_sow_requires_business_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current.xlsx"
            candidate = Path(tmp) / "candidate.xlsx"
            _write_model(current, [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [
                ["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None],
                ["Brand New SOW", 300, "New", "Hop", 1, "Mandatory", None, None],
            ])
            report = analyze_pr_model_change(current, candidate)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertIn("NEW_SOW", report["reason_codes"])
        self.assertEqual(report["new_sows"], ["Brand New SOW"])

    def test_added_optional_row_under_existing_sow_is_compatible_but_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current.xlsx"
            candidate = Path(tmp) / "candidate.xlsx"
            _write_model(current, [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [
                ["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None],
                ["MW Swap", 101, "Optional extra", "Hop", 1, "Optional", None, None],
            ])
            report = analyze_pr_model_change(current, candidate)
        self.assertEqual(report["status"], "COMPATIBLE")
        self.assertEqual(report["added_count"], 1)

    def test_added_mandatory_row_under_existing_sow_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current.xlsx"
            candidate = Path(tmp) / "candidate.xlsx"
            _write_model(current, [["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None]])
            _write_model(candidate, [
                ["MW Swap", 100, "Swap", "Hop", 1, "Mandatory", None, None],
                ["MW Swap", 102, "Mandatory extra", "Hop", 1, "Mandatory", None, None],
            ])
            report = analyze_pr_model_change(current, candidate)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertIn("ADDED_MANDATORY_ROWS", report["reason_codes"])
        self.assertEqual(report["added_mandatory_count"], 1)


if __name__ == "__main__":
    unittest.main()
