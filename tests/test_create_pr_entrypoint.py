import argparse
import importlib
import io
import json
import os
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
CONTRACT_PATH = ROOT / "Info" / "input" / "contract_info_reference.md"
POLICY_PATH = ROOT / "config" / "subcontractor_pr_policy.json"


def _last_json_object(text: str) -> dict:
    """Parse the final JSON object when dependencies emit warnings first."""
    starts = [index for index, char in enumerate(text) if char == "{"]
    for start in reversed(starts):
        try:
            payload = json.loads(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise AssertionError(f"No JSON object found in process output: {text!r}")


def _candidate_record(site_code: str = "TEST-1") -> dict:
    return {
        "site": {"site_code": site_code, "site_name": "Test Site", "du_key": "DU-1"},
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


def _metadata(profile_id: str = "test_profile") -> dict:
    return {
        "profile_id": profile_id,
        "profile_version": "1.0.0",
        "mapping_version": "approved-v1",
        "project_key": "project",
        "du_model_name": "Test DU",
        "du_model_id": "1",
        "view_id": "2",
        "header_hash": "abc",
    }


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

    def test_unregistered_view_is_runtime_layout_evidence_not_profile_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            changed = Path(temp_dir) / "unknown-view.xlsx"
            workbook = load_workbook(FIXTURE)
            workbook["data"]["A1"] = "site|fix00012|4188808420049567786|999999999"
            workbook.save(changed)
            workbook.close()

            resolution = resolve_du_profile(
                changed,
                profile_root=PROFILE_ROOT,
                identity_registry_path=IDENTITY_REGISTRY,
            )

            self.assertEqual(resolution["profile"]["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(resolution["view_id"], "999999999")
            self.assertEqual(resolution["profile_selection_basis"], "DU_MODEL_ID_FALLBACK")
            self.assertEqual(
                resolution["header_hash_approval_basis"],
                "VIEW_NORMALIZED_TO_APPROVED_LAYOUT",
            )

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

    def test_explicit_uat_accepts_production(self):
        resolver = getattr(create_pr, "_resolve_run_mode", None)
        self.assertIsNotNone(resolver, "create_pr must expose the structured lifecycle gate")
        self.assertEqual(resolver("PRODUCTION", True), "NON_PRODUCTION_UAT")

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

    def test_mark_uat_artifacts_handles_windows_extended_paths(self):
        marker = getattr(create_pr, "_mark_uat_artifacts", None)
        self.assertIsNotNone(marker, "create_pr must visibly mark renderer-created UAT files")

        def extended_path(path_str: str) -> str:
            if os.name != "nt":
                return path_str
            if path_str.startswith("\\\\?\\"):
                return path_str
            if path_str.startswith("\\\\"):
                return "\\\\?\\UNC\\" + path_str[2:]
            return "\\\\?\\" + path_str

        temp_dir = tempfile.mkdtemp()
        try:
            root = Path(temp_dir)
            max_source = 259
            suffix = ".xlsx"
            base_length = len(str(root)) + 1 + len(suffix)
            stem_length = max_source - base_length
            self.assertGreater(stem_length, 0, "Temporary root path is too long for the regression test")
            source = root / ("A" * stem_length + suffix)
            expected = source.with_name(f"{source.stem}_NON_PRODUCTION_UAT{source.suffix}")
            self.assertTrue(len(str(source)) < 260, f"Source path length should be below MAX_PATH: {len(str(source))}")
            self.assertTrue(len(str(expected)) > 260, f"Target path length should exceed MAX_PATH: {len(str(expected))}")
            source.write_bytes(b"uat")
            self.assertTrue(source.exists())
            self.assertTrue(expected.parent.exists())
            renamed = marker([source])
            self.assertEqual(renamed, [expected])
            self.assertFalse(source.exists())
            self.assertEqual([p.name for p in root.iterdir()], [expected.name])
        finally:
            expected_path = extended_path(str(expected))
            if os.path.exists(expected_path):
                os.remove(expected_path)
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass

    def test_generate_tss_pr_ecc_console_safe_print(self):
        class CP1252Writer:
            encoding = "cp1252"

            def __init__(self):
                self._buffer = []

            def write(self, text):
                text.encode(self.encoding)
                self._buffer.append(text)

            def getvalue(self):
                return "".join(self._buffer)

        writer = CP1252Writer()
        site_name = "\u200bW066N_W00832IB_MENARATANTAN"
        with self.assertRaises(UnicodeEncodeError):
            print(f"  1. site ({site_name})", file=writer)

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "run_generate_tss_helper.py"
            script_lines = [
                "import sys",
                "from importlib.util import spec_from_file_location, module_from_spec",
                "sys.path.insert(0, r'{}')".format(r"{}".format(str(ROOT / "scripts"))),
                "script_path = r'{}'".format(r"{}".format(str(ROOT / "scripts" / "generate_tss_pr_ecc.py"))),
                "site_data = r'{}'".format(r"{}".format(str(FIXTURE))),
                "output_dir = r'{}'".format(r"{}".format(str(temp_dir))),
                "spec = spec_from_file_location('generate_tss_pr_ecc', script_path)",
                "module = module_from_spec(spec)",
                "sys.argv = [",
                "    'generate_tss_pr_ecc.py',",
                "    '--site-data', site_data,",
                "    '--scope', 'TSS',",
                "    '--all-sites',",
                "    '--output', output_dir,",
                "]",
                "spec.loader.exec_module(module)",
                "print(module._console_safe_text('  1. site (\u200bW066N_W00832IB_MENARATANTAN)', encoding='cp1252'))",
            ]
            script_text = "\n".join(script_lines) + "\n"
            script_path.write_text(script_text, encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertIn("\\u200b", result.stdout)

    def test_official_cli_allows_production_tx_mini_without_uat_marker(self):
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
            self.assertTrue(summary_path.is_file())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["entrypoint"], "create_pr.py")
            self.assertEqual(summary["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(summary["profile_status"], "PRODUCTION")
            self.assertEqual(summary["run_mode"], "PRODUCTION")
            self.assertTrue(summary["production_ecc_allowed"])
            self.assertFalse(summary["non_production_uat"])
            self.assertEqual(Path(summary["output_root"]), Path(temp_dir).resolve())
            self.assertIsNone(summary["run_id"])
            self.assertTrue(summary["created_files"])
            self.assertTrue(
                all("NON_PRODUCTION_UAT" not in Path(path).name for path in summary["created_files"])
            )

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
            self.assertEqual(summary["profile_status"], "PRODUCTION")
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
                mapping=CONTRACT_PATH,
                subcontractor_policy=POLICY_PATH,
                non_production_uat=False,
            )
            with mock.patch.object(create_pr, "resolve_du_profile", return_value=resolution), mock.patch.object(
                create_pr,
                "build_canonical_records",
                return_value=([_candidate_record("PROD-1")], _metadata("production_profile")),
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

    def test_uat_renderer_failure_marks_partial_artifacts_before_raising(self):
        resolution = {
            "profile": {"profile_id": "uat_profile", "status": "PR_INPUT_READY"},
            "inventory": [],
            "header_hash": "abc",
        }

        def failing_renderer(command, **_kwargs):
            output = Path(command[command.index("--output") + 1])
            (output / "Central-GTSB Test DU TSS PR 20260729.xlsx").write_bytes(b"partial")
            return SimpleNamespace(returncode=1, stdout="", stderr="renderer failed")

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
            )
            with mock.patch.object(create_pr, "resolve_du_profile", return_value=resolution), mock.patch.object(
                create_pr,
                "build_canonical_records",
                return_value=([_candidate_record()], _metadata("uat_profile")),
            ), mock.patch.object(create_pr.subprocess, "run", side_effect=failing_renderer):
                with self.assertRaises(create_pr.CreatePrError) as context:
                    create_pr.run(parsed)

            self.assertEqual(context.exception.code, "ECC_RENDERER_FAILED")
            partial_files = list((Path(temp_dir) / "NON_PRODUCTION_UAT").rglob("*.xlsx"))
            self.assertEqual(len(partial_files), 1)
            self.assertIn("NON_PRODUCTION_UAT", partial_files[0].name)
            self.assertEqual(context.exception.details["partial_artifacts"], [str(partial_files[0].resolve())])


if __name__ == "__main__":
    unittest.main()