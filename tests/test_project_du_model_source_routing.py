import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from du_profile_resolver import DuProfileResolutionError, resolve_du_profile
from iepms_export_source_resolver import (
    SourceResolutionError,
    discover_latest_source_exports,
    load_identity_registry,
    parse_iepms_export_filename,
    resolve_profile_route,
)
from run_all_du_ecc_uat import resolve_v2_manifest_sources


REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
PROFILE_ROOT = ROOT / "config" / "du_profiles"
FIXTURE = ROOT / "tests" / "fixtures" / "tx_mini_du_export_fixture.xlsx"


class TestProjectDuModelSourceRouting(unittest.TestCase):
    def setUp(self):
        self.registry = load_identity_registry(REGISTRY_PATH)

    def test_parse_registered_project_du_model_and_view(self):
        identity = parse_iepms_export_filename(
            Path(
                "A-P202202168750_D002-2023 TX Rollout-"
                "Any PR_PO View-20260805090102.xlsx"
            ),
            self.registry,
        )
        self.assertEqual(identity["project_code"], "P202202168750_D002")
        self.assertEqual(identity["project_key"], "Malaysia_CelcomDigi_Project")
        self.assertEqual(identity["du_model_name"], "2023 TX Rollout")
        self.assertEqual(identity["view_name"], "Any PR_PO View")
        self.assertEqual(identity["export_timestamp"], "20260805090102")

    def test_profile_route_uses_project_and_du_model_only(self):
        first = resolve_profile_route(
            self.registry,
            project_key="Malaysia_CelcomDigi_Project",
            du_model_name="2023 TX Rollout",
        )
        second = resolve_profile_route(
            self.registry,
            project_key="Malaysia_CelcomDigi_Project",
            du_model_name="  2023   tx rollout  ",
        )
        self.assertEqual(first["profile_id"], "tx_rollout_2023_pr_v1")
        self.assertEqual(second["profile_id"], "tx_rollout_2023_pr_v1")

    def test_unknown_project_code_fails_closed(self):
        with self.assertRaises(SourceResolutionError) as context:
            parse_iepms_export_filename(
                Path("A-P000000000000_D000-TX Mini Project-View-20260805090102.xlsx"),
                self.registry,
            )
        self.assertEqual(context.exception.code, "PROJECT_CODE_UNREGISTERED")

    def test_unknown_du_model_fails_closed(self):
        with self.assertRaises(SourceResolutionError) as context:
            parse_iepms_export_filename(
                Path(
                    "A-P202202168750_D002-Unknown DU Model-View-"
                    "20260805090102.xlsx"
                ),
                self.registry,
            )
        self.assertEqual(context.exception.code, "DU_MODEL_UNREGISTERED")

    def test_latest_filename_timestamp_is_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            older = root / (
                "A-P202202168750_D002-TX Mini Project-View A-"
                "20260804090102.xlsx"
            )
            latest = root / (
                "A-P202202168750_D002-TX Mini Project-View B-"
                "20260805090102.xlsx"
            )
            older.touch()
            latest.touch()

            result = discover_latest_source_exports([root], self.registry)

            selected = result["selections"]["tx_mini_pr_v1"]
            self.assertEqual(Path(selected["source_path"]), latest.resolve())
            self.assertEqual(selected["candidate_count"], 2)
            self.assertEqual(selected["selection_policy"], "LATEST_FILENAME_TIMESTAMP")

    def test_same_latest_timestamp_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / (
                "A-P202202168750_D002-TX Mini Project-View A-"
                "20260805090102.xlsx"
            )
            second = root / (
                "A-P202202168750_D002-TX Mini Project-View B-"
                "20260805090102.xlsx"
            )
            first.touch()
            second.touch()

            result = discover_latest_source_exports([root], self.registry)

            self.assertNotIn("tx_mini_pr_v1", result["selections"])
            errors = [
                row for row in result["errors"]
                if row.get("profile_id") == "tx_mini_pr_v1"
            ]
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["code"], "SOURCE_EXPORT_TIMESTAMP_AMBIGUOUS")

    def test_valid_iepms_filename_routes_without_using_view_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / (
                "A-P202202168750_D002-TX Mini Project-"
                "Completely Different View Name-20260805090102.xlsx"
            )
            shutil.copy2(FIXTURE, source)

            resolution = resolve_du_profile(
                source,
                profile_root=PROFILE_ROOT,
                identity_registry_path=REGISTRY_PATH,
            )

            self.assertEqual(resolution["profile"]["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(resolution["project_key"], "Malaysia_CelcomDigi_Project")
            self.assertEqual(resolution["du_model_name"], "TX Mini Project")
            self.assertEqual(resolution["view_name"], "Completely Different View Name")
            self.assertEqual(resolution["profile_selection_basis"], "PROJECT_AND_DU_MODEL")

    def test_filename_project_du_model_must_match_workbook_du_model_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / (
                "A-P202202168750_D002-2023 TX Rollout-Any View-"
                "20260805090102.xlsx"
            )
            shutil.copy2(FIXTURE, source)

            with self.assertRaises(DuProfileResolutionError) as context:
                resolve_du_profile(
                    source,
                    profile_root=PROFILE_ROOT,
                    identity_registry_path=REGISTRY_PATH,
                )

            self.assertEqual(
                context.exception.code,
                "SOURCE_FILENAME_WORKBOOK_IDENTITY_MISMATCH",
            )

    def test_latest_invalid_export_blocks_without_falling_back_to_older_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            older = root / (
                "A-P202202168750_D002-TX Mini Project-Old View-"
                "20260804090102.xlsx"
            )
            latest = root / (
                "A-P202202168750_D002-TX Mini Project-New View-"
                "20260805090102.xlsx"
            )
            shutil.copy2(FIXTURE, older)
            shutil.copy2(FIXTURE, latest)
            workbook = load_workbook(latest)
            workbook["data"]["B4"] = "Unapproved Changed Display Header"
            workbook.save(latest)
            workbook.close()

            discovery = discover_latest_source_exports([root], self.registry)
            selected = Path(
                discovery["selections"]["tx_mini_pr_v1"]["source_path"]
            )
            self.assertEqual(selected, latest.resolve())

            with self.assertRaises(DuProfileResolutionError) as context:
                resolve_du_profile(
                    selected,
                    profile_root=PROFILE_ROOT,
                    identity_registry_path=REGISTRY_PATH,
                )

            self.assertEqual(
                context.exception.code,
                "HEADER_HASH_REVALIDATION_REQUIRED",
            )
            self.assertNotEqual(selected, older.resolve())

    def test_duplicate_project_du_model_route_fails_closed(self):
        registry = json.loads(json.dumps(self.registry))
        duplicate = dict(
            next(
                entry
                for entry in registry["profiles"]
                if entry["profile_id"] == "tx_rollout_2023_pr_v1"
            )
        )
        duplicate["profile_id"] = "duplicate_tx_rollout_profile"
        registry["profiles"].append(duplicate)

        with self.assertRaises(SourceResolutionError) as context:
            resolve_profile_route(
                registry,
                project_key="Malaysia_CelcomDigi_Project",
                du_model_name="2023 TX Rollout",
            )
        self.assertEqual(context.exception.code, "DU_PROFILE_IDENTITY_AMBIGUOUS")

    def test_v2_manifest_resolves_relative_source_root_and_builds_v1_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config_dir = workspace / "config"
            export_dir = workspace / "Info" / "reference" / "du_exports"
            config_dir.mkdir(parents=True)
            export_dir.mkdir(parents=True)
            selected = export_dir / (
                "A-P202202168750_D002-TX Mini Project-Any View-"
                "20260805090102.xlsx"
            )
            selected.touch()
            manifest = config_dir / "all_du_ecc_uat_manifest.local.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "source_roots": ["../Info/reference/du_exports"],
                        "selection_policy": "LATEST_FILENAME_TIMESTAMP",
                    }
                ),
                encoding="utf-8",
            )

            internal_manifest, discovery = resolve_v2_manifest_sources(
                manifest,
                identity_registry_path=REGISTRY_PATH,
            )

            self.assertEqual(internal_manifest["schema_version"], "1.0")
            entries = {
                entry["profile_id"]: entry
                for entry in internal_manifest["profiles"]
            }
            self.assertEqual(
                Path(entries["tx_mini_pr_v1"]["source_export"]),
                selected.resolve(),
            )
            self.assertEqual(
                discovery["selections"]["tx_mini_pr_v1"]["view_name"],
                "Any View",
            )


if __name__ == "__main__":
    unittest.main()
