import csv
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from discover_local_du_references import discover_reference_files, looks_like_iepms_four_layer_headers


class TestDiscoverLocalDuReferences(unittest.TestCase):
    def test_header_heuristic_recognizes_four_layer_shape(self):
        rows = [
            ["site|id", "sow|id", "region|id"],
            ["Identity", "Planning", "Location"],
            ["Customer Site", "TX SOW", "Region"],
            ["customer site code", "Tx SOW", "region"],
        ]
        self.assertTrue(looks_like_iepms_four_layer_headers(rows))

    def test_discover_reference_files_summarizes_excel_and_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "Info" / "reference"
            root.mkdir(parents=True)

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "DU Export"
            for row in (
                ["site|id", "sow|id", "region|id"],
                ["Identity", "Planning", "Location"],
                ["Customer Site", "TX SOW", "Region"],
                ["customer site code", "Tx SOW", "region"],
                ["A0001", "TX Mini", "Northern"],
            ):
                sheet.append(row)
            excel_path = root / "A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx"
            workbook.save(excel_path)

            csv_path = root / "sample.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerows(
                    [
                        ["site|id", "sow|id"],
                        ["Identity", "Planning"],
                        ["Customer Site", "TX SOW"],
                        ["customer site code", "Tx SOW"],
                        ["A0001", "TX Mini"],
                    ]
                )

            inventory = discover_reference_files(root)
            self.assertEqual(len(inventory), 2)

            excel_entry = next(item for item in inventory if item["extension"] == ".xlsx")
            self.assertEqual(excel_entry["candidate_du_model"], "TX Mini Project")
            self.assertTrue(excel_entry["appears_suitable_for_du_export_profiling"])
            self.assertEqual(excel_entry["sheet_names"], ["DU Export"])

            csv_entry = next(item for item in inventory if item["extension"] == ".csv")
            self.assertTrue(csv_entry["looks_like_iepms_four_layer_headers"])
            self.assertEqual(csv_entry["sheet_names"], ["CSV"])


if __name__ == "__main__":
    unittest.main()
