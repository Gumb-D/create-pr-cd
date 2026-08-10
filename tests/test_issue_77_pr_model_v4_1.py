import unittest
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent.parent
CANDIDATE = ROOT / "Info" / "input" / "pr_model_v4.1.xlsx"
STARLINK_SOW = "Starlink Dismantle (Return/MRCF included) & Migration"


class TestIssue77PrModelV41(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workbook = load_workbook(CANDIDATE, read_only=True, data_only=True)
        worksheet = workbook["TX Line Item (After 21-Apr 26)"]
        ti_header_row = next(
            row[0].row
            for row in worksheet.iter_rows()
            if isinstance(row[0].value, str) and "TI Model" in row[0].value
        )
        cls.rows = [
            tuple(cell.value for cell in row[:7])
            for row in worksheet.iter_rows(min_row=ti_header_row + 1)
            if row[1].value is not None
        ]
        workbook.close()
        keywords = ("starlink", "mw", "microwave", "patch", "dismant", "install")
        cls.relevant_sows = sorted(
            {
                str(row[0])
                for row in cls.rows
                if row[0] is not None and any(keyword in str(row[0]).casefold() for keyword in keywords)
            }
        )
        print("ISSUE77_V41_RELEVANT_SOWS=" + repr(cls.relevant_sows))

    def _rows_for_sow(self, sow):
        return [row for row in self.rows if row[0] == sow]

    def test_starlink_dismantle_rows_and_required_pboms_exist(self):
        rows = self._rows_for_sow(STARLINK_SOW)
        self.assertTrue(rows, f"Missing v4.1 SOW: {STARLINK_SOW}; relevant={self.relevant_sows}")
        pboms = {str(row[1]) for row in rows if row[1] is not None}
        self.assertTrue({"350000597850", "350000597852"}.issubset(pboms), pboms)

    def test_mw_dismantle_sow_exists(self):
        self.assertTrue(self._rows_for_sow("MW Dismantle"), f"Missing v4.1 SOW: MW Dismantle; relevant={self.relevant_sows}")

    def test_mw_installation_sow_exists(self):
        self.assertTrue(self._rows_for_sow("MW Installation"), f"Missing v4.1 SOW: MW Installation; relevant={self.relevant_sows}")

    def test_patching_model_exists_as_combined_or_exact_split_models(self):
        combined = self._rows_for_sow("BBU Patching / MW IDU Patching")
        bbu = self._rows_for_sow("BBU Patching")
        idu = self._rows_for_sow("MW IDU Patching")
        self.assertTrue(
            combined or (bbu and idu),
            "v4.1 must contain either combined BBU Patching / MW IDU Patching or both exact BBU Patching and MW IDU Patching SOWs; "
            f"relevant={self.relevant_sows}",
        )


if __name__ == "__main__":
    unittest.main()
