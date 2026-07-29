#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pr_helpers import resolve_subcontractor_column


class TestSubcontractorColumnResolution(unittest.TestCase):
    def test_tss_resolves_current_header(self):
        self.assertEqual(
            resolve_subcontractor_column(["customer site code", "Subcon -TSS"], "TSS"),
            "Subcon -TSS",
        )

    def test_tss_resolves_all_approved_du_headers(self):
        for header in ("Subcon - TSS", "SubCon - TSS", "SubCon - TSS Team"):
            with self.subTest(header=header):
                self.assertEqual(
                    resolve_subcontractor_column(["customer site code", header], "TSS"),
                    header,
                )

    def test_ti_resolves_all_approved_du_headers(self):
        for header in ("Subcon -TI", "Subcon - TI", "SubCon - TI", "SubCon - TI Team"):
            with self.subTest(header=header):
                self.assertEqual(
                    resolve_subcontractor_column(["customer site code", header], "TI"),
                    header,
                )

    def test_resolution_tolerates_case_and_spacing_variation(self):
        self.assertEqual(
            resolve_subcontractor_column(["subcon- tss"], "tss"),
            "subcon- tss",
        )

    def test_missing_header_raises_clear_schema_error(self):
        with self.assertRaisesRegex(
            ValueError,
            r"TSS subcontractor column not found.*Subcon -TSS",
        ):
            resolve_subcontractor_column(["customer site code", "region"], "TSS")


if __name__ == "__main__":
    unittest.main()
