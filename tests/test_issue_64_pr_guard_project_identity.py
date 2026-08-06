import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from pr_input_guard import evaluate_record

PROFILE_PATH = ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml"


class TestIssue64PrGuardProjectIdentity(unittest.TestCase):
    def test_missing_runtime_project_key_fails_closed(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        profile["status"] = "PRODUCTION"
        record = {
            "identity": {
                "project_key": "",
                "du_model_name": profile["identity"]["accepted_du_models"][0],
                "du_model_id": profile["identity"]["accepted_du_model_ids"][0],
                "view_id": "unseen-view-is-audit-only",
                "header_hash": profile["export_structure"]["approved_header_hashes"][0],
            },
            "site": {},
            "pr_context": {},
            "technical_context": {},
            "source_evidence": {"fields": {}},
            "validation": {},
        }

        gate = evaluate_record(record, profile, scope="TSS")

        self.assertFalse(gate["allow_output"])
        self.assertIn("UNKNOWN_DU_MODEL", gate["blocking_reasons"])

    def test_wrong_runtime_project_key_fails_closed(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        profile["status"] = "PRODUCTION"
        record = {
            "identity": {
                "project_key": "Wrong_Project",
                "du_model_name": profile["identity"]["accepted_du_models"][0],
                "du_model_id": profile["identity"]["accepted_du_model_ids"][0],
                "view_id": "unseen-view-is-audit-only",
                "header_hash": profile["export_structure"]["approved_header_hashes"][0],
            },
            "site": {},
            "pr_context": {},
            "technical_context": {},
            "source_evidence": {"fields": {}},
            "validation": {},
        }

        gate = evaluate_record(record, profile, scope="TSS")

        self.assertFalse(gate["allow_output"])
        self.assertIn("UNKNOWN_DU_MODEL", gate["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
