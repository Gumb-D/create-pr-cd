import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import create_pr
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

        partitions = create_pr._partition_records(
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
        partitions = create_pr._partition_records([record], "TSS")
        self.assertEqual(partitions["candidates"], [record])
        self.assertEqual(partitions["duplicates"], [])

    def test_pr_input_ready_default_mode_is_blocked(self):
        resolver = getattr(create_pr, "_resolve_run_mode", None)
        self.assertIsNotNone(resolver, "create_pr must expose the structured lifecycle gate")
        with self.assertRaises(create_pr.CreatePrError) as context:
            resolver("PR_INPUT_READY", False)
        self.assertEqual(context.exception.code, "PROFILE_NOT_PRODUCTION")
        self.assertIn("not PRODUCTION", str(context.exception))

    def test_production_status_allows_formal_run_mode(self):
        resolver = getattr(create_pr, "_resolve_run_mode", None)
        self.assertIsNotNone(resolver, "create_pr must expose the structured lifecycle gate")
        self.assertEqual(resolver("PRODUCTION", False), "PRODUCTION")

    def test_explicit_uat_accepts_pr_input_ready(self):
        resolver = getattr(create_pr, "_resolve_run_mode", None)
        self.assertIsNotNone(resolver, "create_pr must expose the structured lifecycle gate")
        self.assertEqual(resolver("PR_INPUT_READY", True), "NON_PRODUCTION_UAT")

    def test_explicit_uat_rejects_draft_profile(self):
        resolver = getattr(create_pr, "_resolve_run_mode", None)
        self.assertIsNotNone(resolver, "create_pr must expose the structured lifecycle gate")
        with self.assertRaises(create_pr.CreatePrError) as context:
            resolver("DRAFT", True)
        self.assertEqual(context.exception.code, "PROFILE_NOT_UAT_ELIGIBLE")

    def test_uat_output_directory_is_marker_bearing_and_unique(self):
        resolver = getattr(create_pr, "_resolve_output_directory", None)
        self.assertIsNotNone(resolver, "create_pr must isolate non-production UAT output")
        requested = Path("output")
        output, run_id = resolver(requested, "NON_PRODUCTION_UAT", run_id="20260729T120000000000Z")
        self.assertEqual(
            output,
            requested / "NON_PRODUCTION_UAT" / "20260729T120000000000Z",
        )
        self.assertEqual(run_id, "20260729T120000000000Z")

    def test_production_output_directory_is_unchanged(self):
        resolver = getattr(create_pr, "_resolve_output_directory", None)
        self.assertIsNotNone(resolver, "create_pr must preserve production output behavior")
        requested = Path("output")
        output, run_id = resolver(requested, "PRODUCTION", run_id="ignored")
        self.assertEqual(output, requested)
        self.assertIsNone(run_id)

    def test_mark_uat_artifacts_inserts_marker_before_suffix(self):
        marker = getattr(create_pr, "_mark_uat_artifacts", None)
        self.assertIsNotNone(marker, "create_pr must visibly mark renderer-created UAT files")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "Central-GTSB Test TSS PR 20260729.xlsx"
            source.write_bytes(b"uat")
            renamed = marker([source])
            expected = root / "Central-GTSB Test TSS PR 20260729_NON_PRODUCTION_UAT.xlsx"
            self.assertEqual(renamed, [expected])
            self.assertFalse(source.exists())
            self.assertTrue(expected.exists())

    def test_official_cli_blocks_pr_input_ready_without_explicit_uat(self):
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
            self.assertEqual(result.returncode, 1, result.stdout)
            payload = json.loads(result.stderr)
            self.assertEqual(payload["code"], "PROFILE_NOT_PRODUCTION")
            self.assertEqual(list(Path(temp_dir).rglob("*.xlsx")), [])

    def test_official_cli_explicit_uat_is_visibly_isolated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "create_pr.py"),
                    "--site-data", str(FIXTURE),
                    "--output", temp_dir,
                    "--scope", "TSS",
                    "--all-sites",
                    "--non-production-uat",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary_paths = list(
                (Path(temp_dir) / "NON_PRODUCTION_UAT").glob(
                    "*/CREATE_PR_SUMMARY_TSS_NON_PRODUCTION_UAT.json"
                )
            )
            self.assertEqual(len(summary_paths), 1)
            summary = json.loads(summary_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(summary["entrypoint"], "create_pr.py")
            self.assertEqual(summary["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(summary["profile_status"], "PR_INPUT_READY")
            self.assertEqual(summary["run_mode"], "NON_PRODUCTION_UAT")
            self.assertTrue(summary["non_production_uat"])
            self.assertFalse(summary["production_ecc_allowed"])
            self.assertIn("NON_PRODUCTION_UAT", summary["output_root"])
            self.assertTrue(summary["run_id"])
            self.assertTrue(summary["created_files"])
            self.assertTrue(
                all("NON_PRODUCTION_UAT" in Path(path).name for path in summary["created_files"])
            )

    def test_run_production_mode_invokes_renderer_without_uat_marker(self):
        candidate = {
            "site": {"site_code": "PROD-1", "site_name": "Production Site", "du_key": "DU-1"},
            "pr_context": {
                "subcontractor_tss": "GTSB",
                "existing_tss_pr_status": "NO_PR",
                "tx_sow_normalized": "MW NEW LINK",
                "region": "Central",
            },
            "technical_context": {},
            "source_evidence": {
                "fields": {"tx_sow_normalized": {"normalization_status": "APPROVED"}}
            },
            "validation": {"pr_input_classification": "PR_INPUT_READY"},
        }
        metadata = {
            "profile_id": "production_profile",
            "profile_version": "1.0.0",
            "mapping_version": "approved-v1",
            "project_key": "project",
            "du_model_name": "Production DU",
            "du_model_id": "1",
            "view_id": "2",
            "header_hash": "abc",
        }
        resolution = {
            "profile": {"profile_id": "production_profile", "status": "PRODUCTION"},
            "inventory": [],
            "header_hash": "abc",
        }

        def fake_renderer(command, **_kwargs):
            output = Path(command[command.index("--output") + 1])
            (output / "Central-GTSB Production DU TSS PR 20260729.xlsx").write_bytes(b"formal")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            parsed = argparse.Namespace(
                site_data=Path("input.xlsx"),
                output=Path(temp_dir),
                scope="TSS",
                site_code=None,
                all_sites=True,
                pr_model=Path("pr_model.xlsx"),
                template=Path("template.xls"),
                mapping=Path("mapping.md"),
                non_production_uat=False,
            )
            with mock.patch.object(create_pr, "resolve_du_profile", return_value=resolution), mock.patch.object(
                create_pr,
                "build_canonical_records",
                return_value=([candidate], metadata),
            ), mock.patch.object(create_pr.subprocess, "run", side_effect=fake_renderer):
                summary = create_pr.run(parsed)

            self.assertEqual(summary["run_mode"], "PRODUCTION")
            self.assertEqual(summary["profile_status"], "PRODUCTION")
            self.assertFalse(summary["non_production_uat"])
            self.assertTrue(summary["production_ecc_allowed"])
            self.assertEqual(Path(summary["output_root"]), Path(temp_dir).resolve())
            self.assertIsNone(summary["run_id"])
            self.assertEqual(len(summary["created_files"]), 1)
            self.assertNotIn("NON_PRODUCTION_UAT", Path(summary["created_files"][0]).name)


if __name__ == "__main__":
    unittest.main()
