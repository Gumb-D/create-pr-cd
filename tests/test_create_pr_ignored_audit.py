import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import create_pr


CONTRACT_PATH = ROOT / "Info" / "input" / "contract_info_reference.md"
POLICY_PATH = ROOT / "config" / "subcontractor_pr_policy.json"


def sm_record():
    return {
        "identity": {"source_row_number": 12},
        "site": {"site_code": "SM-001", "site_name": "SM Site", "du_key": "DU-SM"},
        "pr_context": {
            "region": "Central",
            "tx_sow_normalized": "MW NEW LINK",
            "subcontractor_tss": " sm ",
            "subcontractor_ti": " sm ",
            "existing_tss_pr_status": "NO_PR",
            "existing_ti_pr_status": "NO_PR",
        },
        "technical_context": {},
        "source_evidence": {
            "fields": {"tx_sow_normalized": {"normalization_status": "APPROVED"}}
        },
        "validation": {
            "profile_id": "test_profile",
            "pr_input_classification": "PR_INPUT_READY",
            "blocking_reasons": [],
        },
    }


class TestCreatePrIgnoredAudit(unittest.TestCase):
    def test_sm_ignored_record_is_persisted_with_reason_and_summary_reference(self):
        resolution = {
            "profile": {"profile_id": "test_profile", "status": "PR_INPUT_READY"},
            "inventory": [],
            "header_hash": "abc",
        }
        metadata = {
            "profile_id": "test_profile",
            "profile_version": "1.0.0",
            "mapping_version": "approved-v1",
            "project_key": "project",
            "du_model_name": "Test DU",
            "du_model_id": "1",
            "view_id": "2",
            "header_hash": "abc",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            parsed = argparse.Namespace(
                site_data=Path("input.xlsx"),
                output=Path(temp_dir),
                scope="TSS",
                site_code=None,
                all_sites=True,
                pr_model=Path("pr_model.xlsx"),
                template=Path("template.xls"),
                mapping=CONTRACT_PATH,
                subcontractor_policy=POLICY_PATH,
                non_production_uat=True,
                uat_run_id="IGNORED-AUDIT",
            )
            with mock.patch.object(create_pr, "resolve_du_profile", return_value=resolution), mock.patch.object(
                create_pr,
                "build_canonical_records",
                return_value=([sm_record()], metadata),
            ), mock.patch.object(create_pr.subprocess, "run") as renderer:
                summary = create_pr.run(parsed)

            renderer.assert_not_called()
            self.assertEqual(summary["candidate_count"], 0)
            self.assertEqual(summary["ignored_count"], 1)
            self.assertEqual(summary["sm_excluded_count"], 1)
            ignored_path = Path(summary["ignored_report"])
            self.assertTrue(ignored_path.is_file())
            self.assertIn("NON_PRODUCTION_UAT", ignored_path.name)
            text = ignored_path.read_text(encoding="utf-8-sig")
            self.assertIn("SM-001", text)
            self.assertIn("IGNORED", text)
            self.assertIn("PR_NOT_REQUIRED_OUTSOURCED_TO_OTHER_VENDOR", text)
            self.assertIn("Work is assigned to another vendor; no PR shall be issued.", text)

            persisted = json.loads(Path(summary["summary_path"]).read_text(encoding="utf-8"))
            self.assertEqual(persisted["ignored_report"], str(ignored_path.resolve()))


if __name__ == "__main__":
    unittest.main()
