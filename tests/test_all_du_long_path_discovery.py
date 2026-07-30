import argparse
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import run_all_du_ecc_uat as batch


class TestAllDuLongPathDiscovery(unittest.TestCase):
    def test_materialize_discovers_and_moves_long_windows_paths(self):
        temp_root = Path(tempfile.mkdtemp())
        try:
            scope_dir = temp_root / "FULL_PACK" / "TSS"
            engine_root = scope_dir / "_ENGINE"
            source = (
                engine_root
                / "NON_PRODUCTION_UAT"
                / ("child-" + "a" * 100)
                / ("nested-" + "b" * 100)
                / ("Central-Datasco " + "c" * 80 + ".xlsx")
            )
            self.assertGreater(len(str(source)), 260)

            source_parent = batch._windows_extended_path(source.parent) if os.name == "nt" else str(source.parent)
            source_name = batch._windows_extended_path(source) if os.name == "nt" else str(source)
            os.makedirs(source_parent, exist_ok=True)
            with open(source_name, "wb") as handle:
                handle.write(b"uat")

            summary = {
                "scope": "TSS",
                "created_files": [str(source)],
                "summary_path": str(engine_root / "summary.json"),
                "review_report": None,
                "contract_mapping_review_report": None,
                "ignored_report": None,
            }

            real_walk = os.walk
            real_rename = os.rename
            real_makedirs = os.makedirs
            real_exists = os.path.exists
            real_isfile = os.path.isfile
            real_rmtree = shutil.rmtree
            walk_roots = []
            rename_calls = []

            def strip_extended(value: str) -> str:
                if value.startswith("\\\\?\\UNC\\"):
                    return "\\\\" + value[len("\\\\?\\UNC\\") :]
                if value.startswith("\\\\?\\"):
                    return value[len("\\\\?\\") :]
                return value

            def add_extended(value: str) -> str:
                if value.startswith("\\\\?\\"):
                    return value
                if value.startswith("\\\\"):
                    return "\\\\?\\UNC\\" + value[2:]
                return "\\\\?\\" + value

            def native_argument(value) -> str:
                raw = str(value)
                return raw if os.name == "nt" else strip_extended(raw)

            def fake_walk(raw_root):
                walk_roots.append(str(raw_root))
                for current, directories, files in real_walk(native_argument(raw_root)):
                    yielded_current = current if os.name == "nt" else add_extended(current)
                    yield yielded_current, directories, files

            def fake_rename(raw_source, raw_target):
                rename_calls.append((str(raw_source), str(raw_target)))
                real_rename(native_argument(raw_source), native_argument(raw_target))

            def fake_makedirs(raw_path, exist_ok=False):
                real_makedirs(native_argument(raw_path), exist_ok=exist_ok)

            def fake_exists(raw_path):
                return real_exists(native_argument(raw_path))

            def fake_isfile(raw_path):
                return real_isfile(native_argument(raw_path))

            def fake_rmtree(raw_path):
                real_rmtree(native_argument(raw_path))

            with mock.patch.object(batch, "_is_windows", return_value=True), mock.patch.object(
                batch.os, "walk", side_effect=fake_walk
            ), mock.patch.object(batch.os, "rename", side_effect=fake_rename), mock.patch.object(
                batch.os, "makedirs", side_effect=fake_makedirs
            ), mock.patch.object(batch.os.path, "exists", side_effect=fake_exists), mock.patch.object(
                batch.os.path, "isfile", side_effect=fake_isfile
            ), mock.patch.object(batch.shutil, "rmtree", side_effect=fake_rmtree):
                adjusted, generated = batch.materialize_scope_artifacts(
                    engine_root,
                    scope_dir,
                    summary,
                    "FULL_PACK",
                    "RUN-1",
                )

            expected = scope_dir / batch._impl._artifact_name(source, "FULL_PACK", "RUN-1")
            self.assertTrue(walk_roots)
            self.assertTrue(all(root.startswith("\\\\?\\") for root in walk_roots))
            self.assertEqual(len(rename_calls), 1)
            self.assertTrue(rename_calls[0][0].startswith("\\\\?\\"))
            self.assertTrue(rename_calls[0][1].startswith("\\\\?\\"))
            self.assertFalse(os.path.exists(source_name))
            self.assertTrue(expected.is_file())
            self.assertEqual(generated, [expected.absolute()])
            self.assertEqual(adjusted["created_files"], [str(expected.absolute())])
            self.assertFalse(engine_root.exists())
            self.assertTrue(Path(adjusted["summary_path"]).is_file())
            json.loads(Path(adjusted["summary_path"]).read_text(encoding="utf-8"))
        finally:
            cleanup_root = batch._windows_extended_path(temp_root) if os.name == "nt" else str(temp_root)
            shutil.rmtree(cleanup_root, ignore_errors=True)

    def test_run_scope_pack_uses_short_temporary_renderer_staging(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_export = root / "source.xlsx"
            source_export.write_bytes(b"source")
            scope_dir = root / ("final-" + "x" * 120) / "REVIEW_PACK" / "TSS"
            args = argparse.Namespace(
                pr_model=Path("pr_model.xlsx"),
                template=Path("template.xls"),
                mapping=Path("mapping.md"),
                subcontractor_policy=Path("policy.json"),
            )
            observed = {}

            def fake_create_pr_run(parsed):
                engine_root = Path(parsed.output)
                observed["engine_root"] = engine_root
                observed["child_run_id"] = parsed.uat_run_id
                artifact_root = engine_root / batch._impl.UAT_MARKER / parsed.uat_run_id
                artifact_root.mkdir(parents=True, exist_ok=True)
                artifact = artifact_root / "Central-GTSB Test TSS PR.xlsx"
                artifact.write_bytes(b"uat")
                summary_path = artifact_root / "summary.json"
                summary = {
                    "scope": "TSS",
                    "created_files": [str(artifact)],
                    "summary_path": str(summary_path),
                    "review_report": None,
                    "contract_mapping_review_report": None,
                    "ignored_report": None,
                }
                summary_path.write_text(json.dumps(summary), encoding="utf-8")
                return summary

            def fake_materialize(engine_root, final_scope_dir, summary, pack_type, batch_run_id):
                observed["materialize_engine_root"] = Path(engine_root)
                observed["final_scope_dir"] = Path(final_scope_dir)
                return summary, []

            with mock.patch.object(batch._impl.create_pr, "run", side_effect=fake_create_pr_run), mock.patch.object(
                batch, "materialize_scope_artifacts", side_effect=fake_materialize
            ), mock.patch.object(
                batch._impl, "materialize_scope_artifacts", side_effect=fake_materialize
            ):
                result = batch.run_scope_pack(
                    source_export,
                    scope_dir,
                    "TSS",
                    "REVIEW_PACK",
                    ["SITE-1"],
                    "celcomdigi_bau_2023_pr_v1",
                    "20260730T055547239667Z",
                    args,
                )

            engine_root = observed["engine_root"]
            self.assertEqual(observed["materialize_engine_root"], engine_root)
            self.assertEqual(observed["final_scope_dir"], scope_dir)
            self.assertNotEqual(engine_root, scope_dir / "_ENGINE")
            self.assertNotIn(scope_dir, engine_root.parents)
            self.assertLess(len(str(engine_root)), 160)
            self.assertLess(len(observed["child_run_id"]), 80)
            self.assertFalse(engine_root.exists())
            self.assertEqual(result[1], [])


if __name__ == "__main__":
    unittest.main()
