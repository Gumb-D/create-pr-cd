import json
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from profile_du_export import calculate_header_hash, profile_export


class TestDuExportProfiler(unittest.TestCase):
    def _write_fixture(self, path: Path) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "DU Export"
        rows = [
            ["site|id", "sow|id", "region|id", "subcon|ti", "ti|pr", "lat", "lon"],
            ["Identity", "TX Planning", "Location", "Subcontractor", "PR", "Location", "Location"],
            ["Customer Site", "TX SOW", "Region", "TI Team", "TI PR Status", "Latitude", "Longitude"],
            ["customer site code", "Tx SOW", "region", "SubCon - TI Team", "Subcon PR - TI", "Latitude (North Plus South Minus)", "Longitude (East Plus West Minus)"],
            ["A0001", "MW Swap", "Northern", "GTSB", "", 6.1, 100.1],
        ]
        for row in rows:
            worksheet.append(row)
        workbook.save(path)

    def test_outputs_are_complete_and_header_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.xlsx"
            out_one = tmp / "out_one"
            out_two = tmp / "out_two"
            self._write_fixture(source)

            first = profile_export(source, out_one, project_key="CelcomDigi_MW", du_model_name="MW EOS Swap")
            second = profile_export(source, out_two, project_key="CelcomDigi_MW", du_model_name="MW EOS Swap")

            self.assertEqual(calculate_header_hash(first["inventory"]), calculate_header_hash(second["inventory"]))
            self.assertEqual(first["profile"]["status"], "DRAFT")
            self.assertTrue((out_one / "header_inventory.json").exists())
            self.assertTrue((out_one / "header_inventory.md").exists())
            self.assertTrue((out_one / "header_hash.txt").exists())
            self.assertTrue((out_one / "canonical_field_candidates.json").exists())
            self.assertTrue((out_one / "missing_pr_critical_fields.md").exists())
            self.assertTrue((out_one / "draft_du_profile.yaml").exists())

            inventory = json.loads((out_one / "header_inventory.json").read_text(encoding="utf-8"))
            first_column = inventory["sheets"][0]["columns"][0]
            self.assertEqual(first_column["raw_header_values"], ["site|id", "Identity", "Customer Site", "customer site code"])
            self.assertEqual(first_column["fingerprint"]["display_header"], "customer site code")

            candidates = json.loads((out_one / "canonical_field_candidates.json").read_text(encoding="utf-8"))
            self.assertEqual(candidates["fields"]["site_code"]["status"], "UNVERIFIED")
            self.assertEqual(candidates["fields"]["site_code"]["candidates"][0]["mapping_status"], "UNVERIFIED")
            self.assertIn("subcontractor_ti", (out_one / "missing_pr_critical_fields.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
