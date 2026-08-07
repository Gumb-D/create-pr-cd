import csv
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from profile_du_export import (
    build_header_inventory,
    calculate_header_hash,
    calculate_structural_header_hash,
    resolve_approved_header_structure,
)


DU_MODEL_ID = "1027190858144623081"
VIEW_ID = "8530399820526021092"
ALT_VIEW_ID = "8043814649254951526"


def _column(field_code, wbs, task, display):
    fingerprint = {
        "field_code": field_code,
        "wbs_stage": wbs,
        "task_name": task,
        "display_header": display,
    }
    return {"fingerprint": fingerprint}


def _inventory(*sheets):
    return {
        "schema_version": "1.0",
        "source": {
            "file_name": "synthetic.xlsx",
            "source_file_hash": "synthetic",
            "format": "xlsx",
            "header_row_count": 4,
        },
        "sheets": list(sheets),
    }


def _data_sheet(view_id=VIEW_ID, *, display="customer site code", sheet_name="data"):
    return {
        "sheet_name": sheet_name,
        "header_row_count": 4,
        "columns": [
            _column(
                f"site|fix00012|{DU_MODEL_ID}|{view_id}",
                "Site Basic Info",
                "Site Basic Info",
                display,
            ),
            _column(
                "docata|ZDCSZ640242",
                "Subcon Info",
                "SubCon - TI",
                "SubCon - TI",
            ),
        ],
    }


def _drop_down_sheet(seed="A", *, count=250, sheet_name="drop_down"):
    return {
        "sheet_name": sheet_name,
        "header_row_count": 4,
        "columns": [
            _column(
                f"lookup|{index}|{seed}",
                "dynamic lookup",
                f"person {index}",
                f"option {seed}-{index}",
            )
            for index in range(count)
        ],
    }


def _profile(approved_hash, *, sheet_selector=None, approved_view_id=VIEW_ID):
    return {
        "identity": {
            "project_key": "Malaysia_CelcomDigi_Project",
            "accepted_du_models": ["2023 TX Rollout"],
            "accepted_du_model_ids": [DU_MODEL_ID],
        },
        "export_structure": {
            "sheet_selector": sheet_selector,
            "approved_header_hashes": [approved_hash],
        },
        "field_mapping": {
            "site_code": {
                "source_candidates": [
                    {
                        "mapping_status": "APPROVED",
                        "fingerprint": {
                            "field_code": f"site|fix00012|{DU_MODEL_ID}|{approved_view_id}",
                            "wbs_stage": "Site Basic Info",
                            "task_name": "Site Basic Info",
                            "display_header": "customer site code",
                        },
                    }
                ]
            }
        },
    }


class TestIssue67AuthoritativeHeaderHash(unittest.TestCase):
    def test_dynamic_auxiliary_sheet_does_not_change_approval_hash(self):
        first = _inventory(_data_sheet(), _drop_down_sheet("A"))
        second = _inventory(_data_sheet(), _drop_down_sheet("B"))

        self.assertEqual(calculate_header_hash(first), calculate_header_hash(second))
        self.assertEqual(
            calculate_structural_header_hash(first),
            calculate_structural_header_hash(second),
        )

    def test_full_inventory_is_preserved_for_audit(self):
        inventory = _inventory(_data_sheet(), _drop_down_sheet("A"))

        self.assertEqual([sheet["sheet_name"] for sheet in inventory["sheets"]], ["data", "drop_down"])
        self.assertEqual(len(inventory["sheets"][1]["columns"]), 250)

    def test_authoritative_header_change_changes_hash(self):
        original = _inventory(_data_sheet(), _drop_down_sheet("A"))
        changed = _inventory(
            _data_sheet(display="customer site code changed"),
            _drop_down_sheet("A"),
        )

        self.assertNotEqual(calculate_header_hash(original), calculate_header_hash(changed))
        self.assertNotEqual(
            calculate_structural_header_hash(original),
            calculate_structural_header_hash(changed),
        )

    def test_view_only_change_preserves_structural_hash_and_can_match_approved_layout(self):
        approved_inventory = _inventory(_data_sheet(VIEW_ID), _drop_down_sheet("A"))
        runtime_inventory = _inventory(_data_sheet(ALT_VIEW_ID), _drop_down_sheet("B"))
        approved_hash = calculate_header_hash(approved_inventory)
        profile = _profile(approved_hash, approved_view_id=VIEW_ID)

        self.assertNotEqual(
            calculate_header_hash(approved_inventory),
            calculate_header_hash(runtime_inventory),
        )
        self.assertEqual(
            calculate_structural_header_hash(approved_inventory),
            calculate_structural_header_hash(runtime_inventory),
        )
        result = resolve_approved_header_structure(runtime_inventory, profile)
        self.assertTrue(result["approved"])
        self.assertEqual(result["approval_basis"], "VIEW_NORMALIZED_TO_APPROVED_LAYOUT")

    def test_multiple_site_identity_sheets_fail_closed_without_explicit_selector(self):
        inventory = _inventory(
            _data_sheet(sheet_name="data"),
            _data_sheet(sheet_name="data_copy"),
            _drop_down_sheet("A"),
        )

        with self.assertRaisesRegex(ValueError, "authoritative"):
            calculate_header_hash(inventory)

    def test_explicit_sheet_selector_wins_over_auto_detection(self):
        inventory = _inventory(
            _data_sheet(sheet_name="records"),
            _data_sheet(sheet_name="archive"),
        )
        records_only = _inventory(_data_sheet(sheet_name="records"))
        expected_hash = calculate_header_hash(records_only)
        profile = _profile(expected_hash, sheet_selector="records")

        result = resolve_approved_header_structure(inventory, profile)

        self.assertTrue(result["approved"])
        self.assertEqual(result["approved_header_hash"], expected_hash)

    def test_single_sheet_csv_behavior_remains_supported_without_site_identity_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "single.csv"
            rows = [
                ["site|id", "sow|id"],
                ["Identity", "TX Planning"],
                ["Customer Site", "TX SOW"],
                ["customer site code", "Tx SOW"],
                ["A0001", "MW Swap"],
            ]
            with source.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerows(rows)

            inventory = build_header_inventory(source)
            first_hash = calculate_header_hash(inventory)
            second_hash = calculate_header_hash(deepcopy(inventory))

            self.assertEqual(first_hash, second_hash)
            self.assertEqual(inventory["sheets"][0]["sheet_name"], "CSV")


if __name__ == "__main__":
    unittest.main()
