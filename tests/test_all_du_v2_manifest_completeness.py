import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from iepms_export_source_resolver import load_identity_registry
from run_all_du_ecc_uat import resolve_v2_manifest_sources


REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"


class TestAllDuV2ManifestCompleteness(unittest.TestCase):
    def test_v2_manifest_contains_every_registered_profile_even_when_source_is_missing(self):
        registry = load_identity_registry(REGISTRY_PATH)
        registered_profile_ids = {
            str(entry["profile_id"])
            for entry in registry["profiles"]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config_dir = workspace / "config"
            source_root = workspace / "Info" / "reference" / "du_exports"
            config_dir.mkdir(parents=True)
            source_root.mkdir(parents=True)
            selected = source_root / (
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

            internal_manifest, _ = resolve_v2_manifest_sources(
                manifest,
                identity_registry_path=REGISTRY_PATH,
            )

        entries = {
            str(entry["profile_id"]): entry
            for entry in internal_manifest["profiles"]
        }
        self.assertEqual(set(entries), registered_profile_ids)
        self.assertEqual(
            Path(entries["tx_mini_pr_v1"]["source_export"]),
            selected.resolve(),
        )
        self.assertEqual(
            entries["tx_rollout_2023_pr_v1"]["source_export"],
            "",
        )

    def test_ambiguous_latest_export_keeps_profile_entry_blank_for_fail_closed_batch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config_dir = workspace / "config"
            source_root = workspace / "Info" / "reference" / "du_exports"
            config_dir.mkdir(parents=True)
            source_root.mkdir(parents=True)
            for view_name in ("View A", "View B"):
                (
                    source_root
                    / (
                        "A-P202202168750_D002-TX Mini Project-"
                        f"{view_name}-20260805090102.xlsx"
                    )
                ).touch()

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

        entries = {
            str(entry["profile_id"]): entry
            for entry in internal_manifest["profiles"]
        }
        self.assertEqual(entries["tx_mini_pr_v1"]["source_export"], "")
        self.assertTrue(
            any(
                error.get("code") == "SOURCE_EXPORT_TIMESTAMP_AMBIGUOUS"
                and error.get("profile_id") == "tx_mini_pr_v1"
                for error in discovery["errors"]
            )
        )


if __name__ == "__main__":
    unittest.main()
