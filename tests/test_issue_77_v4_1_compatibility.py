import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analyze_pr_model_change import analyze_pr_model_change


CURRENT = ROOT / "Info" / "input" / "pr_model.xlsx"
CANDIDATE = ROOT / "Info" / "input" / "pr_model_v4.1.xlsx"
EXPECTED_CANDIDATE_SHA256 = "6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f"


class TestIssue77V41Compatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_pr_model_change(CURRENT, CANDIDATE)
        print("ISSUE77_V41_COMPATIBILITY=" + json.dumps(cls.report, ensure_ascii=False, sort_keys=True))

    def test_candidate_bytes_match_issue_77_approval_identity(self):
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), EXPECTED_CANDIDATE_SHA256)

    def test_change_analyzer_returns_reviewable_report_not_invalid(self):
        self.assertIn(self.report["status"], {"COMPATIBLE", "REVIEW_REQUIRED"})
        self.assertIn("reason_codes", self.report)
        self.assertNotEqual(self.report["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
