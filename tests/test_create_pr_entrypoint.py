import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from create_pr import _partition_records
from du_profile_resolver import DuProfileResolutionError, resolve_du_profile


FIXTURE = ROOT / "tests" / "fixtures" / "tx_mini_du_export_fixture.xlsx"
PROFILE_ROOT = ROOT / "config" / "du_profiles"
IDENTITY_REGISTRY = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"


class TestCreatePrEntrypoint(unittest.TestCase):
    def test_resolver_identifies_profile_from_model_view_and_header_hash(self):
        resolution = resolve_du_profile(
            FIXTURE,
            profile_root=PROFILE_ROOT,
            identity_registry_path=IDENTITY_REGISTRY,
        )
        self.assertEqual(resolution["profile"]["profile_id"], "tx_mini_pr_v1")
        self.assertEqual(resolution["du_model_id"], "4188808420049567786")
        self.assertEqual(resolution["view_id"], "2477626672974883536")

    def test_unregistered_view_fails_as_profile_error_before_field_access(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            changed = Path(temp_dir) / "unknown-view.xlsx"
            workbook = load_workbook(FIXTURE)
            workbook["data"]["A1"] = "site|fix00012|4188808420049567786|999999999"
            workbook.save(changed)
            workbook.close()
            with self.assertRaises(DuProfileResolutionError) as context:
                resolve_du_profile(
                    changed,
                    profile_root=PROFILE_ROOT,
                    identity_registry_path=IDENTITY_REGISTRY,
                )
            self.assertEqual(context.exception.code, "DU_PROFILE_VIEW_NOT_APPROVED")

    def test_partition_blocks_duplicate_and_invalid_canonical_rows(self):
        def record(site, status, classification, normalization="APPROVED"):
            return {
                "site": {"site_code": site},
                "pr_context": {
                    "subcontractor_ti": "GTSB",
                    "existing_ti_pr_status": status,
                },
                "source_evidence": {
                    "fields": {
                        "tx_sow_normalized": {"normalization_status": normalization}
                    }
                },
                "validation": {"pr_input_classification": classification},
            }

        partitions = _partition_records(
            [
                record("READY", "NO_PR", "PR_INPUT_READY"),
                record("DUP", "PR_EXISTS", "PR_INPUT_READY"),
                record("BAD", "NO_PR", "PR_INPUT_INCOMPLETE"),
            ],
            "TI",
        )
        self.assertEqual([row["site"]["site_code"] for row in partitions["candidates"]], ["READY"])
        self.assertEqual([row["site"]["site_code"] for row in partitions["duplicates"]], ["DUP"])
        self.assertEqual([row["site"]["site_code"] for row in partitions["review_required"]], ["BAD"])

    def test_tss_preserves_existing_entitlement_for_final_po_audit(self):
        record = {
            "site": {"site_code": "TSS-EXISTING"},
            "pr_context": {
                "subcontractor_tss": "GTSB",
                "existing_tss_pr_status": "PR_EXISTS",
            },
            "source_evidence": {
                "fields": {
                    "tx_sow_normalized": {"normalization_status": "APPROVED"}
                }
            },
            "validation": {"pr_input_classification": "PR_INPUT_READY"},
        }
        partitions = _partition_records([record], "TSS")
        self.assertEqual(partitions["candidates"], [record])
        self.assertEqual(partitions["duplicates"], [])

    def test_official_cli_owns_profile_and_canonical_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "create_pr.py"),
                    "--site-data", str(FIXTURE),
                    "--output", temp_dir,
                    "--scope", "TSS",
                    "--all-sites",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary_path = Path(temp_dir) / "CREATE_PR_SUMMARY_TSS.json"
            self.assertTrue(summary_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["entrypoint"], "create_pr.py")
            self.assertEqual(summary["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(summary["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
