import json
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from canonical_input_pipeline import build_canonical_records
from du_export_adapter import resolve_profile_field_mappings
from du_profile_resolver import DuProfileResolutionError, resolve_du_profile
from pr_input_guard import evaluate_record
from profile_du_export import (
    build_header_inventory,
    calculate_header_hash,
    calculate_structural_header_hash,
    fingerprint_key,
    structural_fingerprint_key,
)

FIXTURE = ROOT / "tests" / "fixtures" / "tx_mini_du_export_fixture.xlsx"
PROFILE_ROOT = ROOT / "config" / "du_profiles"
REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
SOW_REGISTRY_PATH = ROOT / "config" / "registries" / "canonical_sow_registry.yaml"
PROFILE_PATH = PROFILE_ROOT / "tx_mini_pr_v1.yaml"
OLD_VIEW_ID = "2477626672974883536"
NEW_VIEW_ID = "9999999999999999999"
MODEL_ID = "4188808420049567786"


def _changed_view_fixture(path: Path) -> None:
    shutil.copy2(FIXTURE, path)
    workbook = load_workbook(path)
    workbook["data"]["A1"] = f"site|fix00012|{MODEL_ID}|{NEW_VIEW_ID}"
    workbook.save(path)
    workbook.close()


class TestIssue64ViewIndependentIdentity(unittest.TestCase):
    def test_worker_filename_routes_unique_model_id_with_unseen_view(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "worker-upload.xlsx"
            _changed_view_fixture(source)

            resolution = resolve_du_profile(
                source,
                profile_root=PROFILE_ROOT,
                identity_registry_path=REGISTRY_PATH,
            )

            self.assertEqual(resolution["profile"]["profile_id"], "tx_mini_pr_v1")
            self.assertEqual(resolution["profile_selection_basis"], "DU_MODEL_ID_FALLBACK")
            self.assertEqual(resolution["du_model_id"], MODEL_ID)
            self.assertEqual(resolution["view_id"], NEW_VIEW_ID)
            self.assertNotEqual(resolution["raw_header_hash"], resolution["structural_header_hash"])

    def test_duplicate_model_id_fallback_is_ambiguous_even_when_views_differ(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "worker-upload.xlsx"
            _changed_view_fixture(source)
            registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            duplicate = deepcopy(
                next(entry for entry in registry["profiles"] if entry["profile_id"] == "tx_mini_pr_v1")
            )
            duplicate["profile_id"] = "duplicate_model_profile"
            duplicate["project_key"] = "Another_Project"
            duplicate["accepted_view_ids"] = [NEW_VIEW_ID]
            registry["profiles"].append(duplicate)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            with self.assertRaises(DuProfileResolutionError) as context:
                resolve_du_profile(
                    source,
                    profile_root=PROFILE_ROOT,
                    identity_registry_path=registry_path,
                )

            self.assertEqual(context.exception.code, "DU_PROFILE_IDENTITY_AMBIGUOUS")

    def test_view_only_change_changes_raw_hash_not_structural_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            changed = Path(temp_dir) / "changed-view.xlsx"
            _changed_view_fixture(changed)
            original_inventory = build_header_inventory(FIXTURE)
            changed_inventory = build_header_inventory(changed)

            self.assertNotEqual(
                calculate_header_hash(original_inventory),
                calculate_header_hash(changed_inventory),
            )
            self.assertEqual(
                calculate_structural_header_hash(original_inventory),
                calculate_structural_header_hash(changed_inventory),
            )

    def test_structural_key_normalizes_only_site_identity_view_suffix(self):
        old_site = {
            "field_code": f"site|fix00012|{MODEL_ID}|{OLD_VIEW_ID}",
            "wbs_stage": "Site Basic Info",
            "task_name": "Site Basic Info",
            "display_header": "customer site code",
        }
        new_site = {**old_site, "field_code": f"site|fix00012|{MODEL_ID}|{NEW_VIEW_ID}"}
        different_model = {
            **old_site,
            "field_code": f"site|fix00012|0000000000000000000|{NEW_VIEW_ID}",
        }
        changed_display = {**new_site, "display_header": "changed site header"}
        non_site_old = {**old_site, "field_code": f"docata|{OLD_VIEW_ID}"}
        non_site_new = {**old_site, "field_code": f"docata|{NEW_VIEW_ID}"}

        self.assertEqual(structural_fingerprint_key(old_site), structural_fingerprint_key(new_site))
        self.assertNotEqual(
            structural_fingerprint_key(old_site),
            structural_fingerprint_key(different_model),
        )
        self.assertNotEqual(
            structural_fingerprint_key(old_site),
            structural_fingerprint_key(changed_display),
        )
        self.assertNotEqual(
            structural_fingerprint_key(non_site_old),
            structural_fingerprint_key(non_site_new),
        )

    def test_mapping_matches_new_view_but_preserves_runtime_raw_fingerprint(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        old_fingerprint = profile["field_mapping"]["site_code"]["source_candidates"][0]["fingerprint"]
        new_fingerprint = {
            **old_fingerprint,
            "field_code": f"site|fix00012|{MODEL_ID}|{NEW_VIEW_ID}",
        }
        inventory = {
            "sheets": [
                {
                    "sheet_name": "data",
                    "columns": [
                        {
                            "fingerprint": new_fingerprint,
                            "fingerprint_key": fingerprint_key(new_fingerprint),
                        }
                    ],
                }
            ]
        }

        resolved = resolve_profile_field_mappings(inventory, profile)

        self.assertEqual(resolved["site_code"]["status"], "RESOLVED")
        self.assertEqual(resolved["site_code"]["matches"][0]["fingerprint"], new_fingerprint)

    def test_multiple_view_candidates_deduplicate_one_runtime_column(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        first = profile["field_mapping"]["site_code"]["source_candidates"][0]
        second = deepcopy(first)
        second["fingerprint"]["field_code"] = (
            f"site|fix00012|{MODEL_ID}|8888888888888888888"
        )
        second["mapping_status"] = "VERIFIED"
        profile["field_mapping"]["site_code"]["source_candidates"] = [first, second]
        runtime_fingerprint = {
            **first["fingerprint"],
            "field_code": f"site|fix00012|{MODEL_ID}|{NEW_VIEW_ID}",
        }
        inventory = {
            "sheets": [
                {
                    "sheet_name": "data",
                    "columns": [
                        {
                            "fingerprint": runtime_fingerprint,
                            "fingerprint_key": fingerprint_key(runtime_fingerprint),
                        }
                    ],
                }
            ]
        }

        resolved = resolve_profile_field_mappings(inventory, profile)

        self.assertEqual(resolved["site_code"]["status"], "RESOLVED")
        self.assertEqual(len(resolved["site_code"]["matches"]), 1)
        self.assertEqual(
            resolved["site_code"]["matches"][0]["mapping_status"],
            "APPROVED",
        )
        self.assertEqual(
            resolved["site_code"]["matches"][0]["fingerprint"],
            runtime_fingerprint,
        )

    def test_canonical_pipeline_preserves_runtime_view_and_raw_fingerprint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "worker-upload.xlsx"
            _changed_view_fixture(source)
            resolution = resolve_du_profile(
                source,
                profile_root=PROFILE_ROOT,
                identity_registry_path=REGISTRY_PATH,
            )

            records, metadata = build_canonical_records(
                input_path=source,
                profile=resolution["profile"],
                inventory=resolution["inventory"],
                header_hash=resolution["raw_header_hash"],
                scope="TSS",
                sow_registry_path=SOW_REGISTRY_PATH,
            )

            self.assertTrue(records)
            self.assertEqual(metadata["view_id"], NEW_VIEW_ID)
            self.assertEqual(metadata["raw_header_hash"], resolution["raw_header_hash"])
            self.assertEqual(
                metadata["structural_header_hash"],
                resolution["structural_header_hash"],
            )
            for record in records:
                self.assertEqual(record["identity"]["view_id"], NEW_VIEW_ID)
                site_evidence = record["source_evidence"]["fields"]["site_code"]
                self.assertEqual(
                    site_evidence["source_header_fingerprint"]["field_code"],
                    f"site|fix00012|{MODEL_ID}|{NEW_VIEW_ID}",
                )

    def test_pr_input_guard_does_not_reject_new_view_only(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        profile["status"] = "PRODUCTION"
        for config in profile["field_mapping"].values():
            config["source_candidates"] = [
                candidate
                for candidate in config.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
        record = {
            "identity": {
                "project_key": profile["identity"]["project_key"],
                "du_model_name": profile["identity"]["accepted_du_models"][0],
                "du_model_id": MODEL_ID,
                "view_id": NEW_VIEW_ID,
                "header_hash": profile["export_structure"]["approved_header_hashes"][0],
            },
            "site": {"site_code": "A0001"},
            "pr_context": {
                "tx_sow_raw": "MW Swap",
                "tx_sow_normalized": "MW SWAP",
                "region": "Northern",
                "subcontractor_ti": "GTSB",
                "existing_tss_pr_status": "NO_PR",
                "existing_ti_pr_status": "NO_PR",
            },
            "technical_context": {},
            "source_evidence": {"fields": {}},
            "validation": {},
        }

        gate = evaluate_record(record, profile, scope="TSS")

        self.assertNotIn("UNKNOWN_DU_MODEL_OR_VIEW", gate["blocking_reasons"])
        self.assertNotIn("UNKNOWN_DU_MODEL", gate["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
