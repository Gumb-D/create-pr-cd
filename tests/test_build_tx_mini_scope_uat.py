import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_tx_mini_scope_uat

class TestBuildTxMiniScopeUat(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.config_path = Path(self.temp_dir.name) / "config.json"
        
        # Base valid config
        self.config_data = {
            "profile_id": "tx_mini_pr_v1",
            "config_version": "1.0.0",
            "status": "UAT_ONLY",
            "scopes": {
                "TSS": {
                    "rule": "actual_end_required",
                    "actual_end_fingerprint": {
                        "field_code": "WP10400|AC0000111560|actual_end_date",
                        "wbs_stage": "Survey&Design",
                        "task_name": "Physical Survey",
                        "display_header": "actual end time"
                    }
                },
                "TI": {
                    "rule": "actual_end_required",
                    "actual_end_fingerprint": {
                        "field_code": "WP11100|AC0000111567|actual_end_date",
                        "wbs_stage": "Telecom Installation",
                        "task_name": "Equipment Installation",
                        "display_header": "actual end time"
                    }
                }
            }
        }
        
        self.input_file = ROOT / "Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx"
        self.profile = ROOT / "config/du_profiles/tx_mini_pr_v1.yaml"
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def write_config(self):
        self.config_path.write_text(json.dumps(self.config_data))
        
    def run_main(self):
        self.write_config()
        args = [
            "build_tx_mini_scope_uat.py",
            "--input", str(self.input_file),
            "--profile", str(self.profile),
            "--scope-config", str(self.config_path),
            "--output", str(self.output_dir)
        ]
        with patch.object(sys, 'argv', args):
            build_tx_mini_scope_uat.main()
            
    def test_missing_tss_config_fails(self):
        del self.config_data["scopes"]["TSS"]
        with self.assertRaisesRegex(ValueError, "Missing TSS config"):
            self.run_main()

    def test_missing_ti_config_fails(self):
        del self.config_data["scopes"]["TI"]
        with self.assertRaisesRegex(ValueError, "Missing TI config"):
            self.run_main()
            
    def test_wrong_profile_id_fails(self):
        self.config_data["profile_id"] = "wrong_profile"
        with self.assertRaisesRegex(ValueError, "PROFILE_ID_MISMATCH"):
            self.run_main()
            
    def test_tss_fingerprint_changed_fails(self):
        self.config_data["scopes"]["TSS"]["actual_end_fingerprint"]["task_name"] = "Wrong Task"
        with self.assertRaisesRegex(ValueError, "FINGERPRINT_NOT_FOUND"):
            self.run_main()

    def test_ti_fingerprint_changed_fails(self):
        self.config_data["scopes"]["TI"]["actual_end_fingerprint"]["task_name"] = "Wrong Task"
        with self.assertRaisesRegex(ValueError, "FINGERPRINT_NOT_FOUND"):
            self.run_main()

    def test_successful_run_writes_manifest_with_config_version_and_status(self):
        self.run_main()
        manifest_path = self.output_dir / "TX_MINI_ELIGIBILITY_MANIFEST.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["scope_config_version"], "1.0.0")
        self.assertEqual(manifest["scope_config_status"], "UAT_ONLY")

if __name__ == "__main__":
    unittest.main()
