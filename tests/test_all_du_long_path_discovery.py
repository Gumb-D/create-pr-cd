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
                if value.startswith("\\\\"):
                    return "\\\\?\\UNC\\" + value[2:]
                return "\\\\?\\" + value

            def fake_walk(raw_root):
                walk_roots.append(str(raw_root))
                for current, directories, files in real_walk(strip_extended(str(raw_root))):
                    yield add_extended(current), directories, files

            def fake_rename(raw_source, raw_target):
                rename_calls.append((str(raw_source), str(raw_target)))
                real_rename(strip_extended(str(raw_source)), strip_extended(str(raw_target)))

            def fake_rmtree(raw_path):
                real_rmtree(strip_extended(str(raw_path)))

            with mock.patch.object(batch, "_is_windows", return_value=True), mock.patch.object(
                batch.os, "walk", side_effect=fake_walk
            ), mock.patch.object(batch.os, "rename", side_effect=fake_rename), mock.patch.object(
                batch.shutil, "rmtree", side_effect=fake_rmtree
            ):
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


if __name__ == "__main__":
    unittest.main()
