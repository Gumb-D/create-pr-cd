import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "Info" / "input" / "pr_model.xlsx"
BASELINE = ROOT / "config" / "pr_model_baseline.yaml"
APPROVAL = ROOT / "config" / "pr_model_approvals" / "issue_77_v4_1.json"
RETIRED_CANDIDATE = ROOT / "Info" / "input" / "pr_model_v4.1.xlsx"
ISSUE_77_V4_1_SHA256 = "6c4fda502a8998b41bd88704dd6c59d986dc6c46fe42b82947d12c0c0cd8178f"
EXPECTED_REASON_CODES = {
    "REMOVED_BUSINESS_ROWS",
    "NEW_SOW",
    "ADDED_MANDATORY_ROWS",
}


class TestIssue77V41Compatibility(unittest.TestCase):
    def test_current_authoritative_baseline_is_self_consistent(self):
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(baseline["status"], "PRODUCTION")
        self.assertEqual(baseline["workbook"]["path"], "Info/input/pr_model.xlsx")
        self.assertTrue(str(baseline["model"]["version"]).strip())
        self.assertEqual(
            hashlib.sha256(CANONICAL.read_bytes()).hexdigest(),
            str(baseline["workbook"]["sha256"]),
        )

    def test_issue_77_approval_preserves_exact_historical_v4_1_identity(self):
        approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
        self.assertEqual(approval["status"], "APPROVED")
        self.assertEqual(str(approval["candidate_version"]), "4.1")
        self.assertEqual(approval["candidate_sha256"], ISSUE_77_V4_1_SHA256)
        self.assertEqual(set(approval["approved_reason_codes"]), EXPECTED_REASON_CODES)
        self.assertTrue(any("Issue #77" in str(item) for item in approval["business_change_references"]))

    def test_promoted_v4_1_candidate_copy_remains_retired_from_runtime_tree(self):
        self.assertFalse(RETIRED_CANDIDATE.exists())


if __name__ == "__main__":
    unittest.main()
