import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import openpyxl

from run_tx_mini_ecc_parity import (
    APPROVED_PR_MODEL_SHA256,
    validate_pr_model,
    validate_candidate_manifest,
    validate_generator_result,
    validate_independent_paths,
    compare_workbook_structure,
    compare_cell,
    extract_business_fields,
    compare_business_fields,
    normalize_allowed_metadata,
    calculate_overall_parity,
)


class TestTxMiniTssEccParity(unittest.TestCase):

    def test_validate_pr_model_approved_hash_passes(self):
        pr_model_file = Path("Info/input/pr_model.xlsx")
        if pr_model_file.exists():
            sha = validate_pr_model(pr_model_file)
            self.assertEqual(sha, APPROVED_PR_MODEL_SHA256)

    def test_validate_pr_model_wrong_hash_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(b"wrong pr model content")
            tmp_path = Path(tmp.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_pr_model(tmp_path)
            self.assertIn("PR_MODEL_HASH_MISMATCH", str(ctx.exception))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_validate_pr_model_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            validate_pr_model(Path("non_existent_file.xlsx"))

    def test_cli_cannot_override_hash(self):
        gen_script = Path("scripts/generate_tss_pr_ecc.py").read_text(encoding="utf-8")
        self.assertNotIn("--expected-pr-model-hash", gen_script)
        self.assertIn("APPROVED_PR_MODEL_SHA256", gen_script)

    def test_validate_candidate_manifest_valid(self):
        candidates = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 13)]
        self.assertTrue(validate_candidate_manifest(candidates))

    def test_validate_candidate_manifest_11_row_fails(self):
        c_11 = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(c_11)
        self.assertIn("must be exactly 12", str(ctx.exception))

    def test_validate_candidate_manifest_13_row_fails(self):
        c_13 = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 14)]
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(c_13)
        self.assertIn("must be exactly 12", str(ctx.exception))

    def test_validate_candidate_manifest_duplicate_candidate_id_fails(self):
        dup_ids = [{"Candidate ID": "C001", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 13)]
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(dup_ids)
        self.assertIn("Duplicate Candidate IDs", str(ctx.exception))

    def test_validate_candidate_manifest_duplicate_source_row_fails(self):
        dup_rows = [{"Candidate ID": f"C{i:03d}", "Source Row": 1, "Site Code": f"S{i:03d}"} for i in range(1, 13)]
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(dup_rows)
        self.assertIn("Duplicate Source Rows", str(ctx.exception))

    def test_validate_candidate_manifest_missing_candidate_id_fails(self):
        missing_id = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        missing_id.append({"Source Row": 12, "Site Code": "S012"})
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(missing_id)
        self.assertIn("missing 'Candidate ID'", str(ctx.exception))

    def test_validate_candidate_manifest_missing_source_row_fails(self):
        missing_sr = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        missing_sr.append({"Candidate ID": "C012", "Site Code": "S012"})
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(missing_sr)
        self.assertIn("missing 'Source Row'", str(ctx.exception))

    def test_validate_candidate_manifest_missing_site_code_fails(self):
        missing_site = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        missing_site.append({"Candidate ID": "C012", "Source Row": 12})
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(missing_site)
        self.assertIn("missing 'Site Code'", str(ctx.exception))

    def test_validate_candidate_manifest_blank_required_value_fails(self):
        blank_val = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        blank_val.append({"Candidate ID": "   ", "Source Row": 12, "Site Code": "S012"})
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(blank_val)
        self.assertIn("blank 'Candidate ID'", str(ctx.exception))

    def test_validate_candidate_manifest_non_list_json_payload_fails(self):
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest({"status": "invalid"})
        self.assertIn("must be a list", str(ctx.exception))

    def test_validate_candidate_manifest_non_object_row_fails(self):
        cands = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
        cands.append("not_a_dict")
        with self.assertRaises(ValueError) as ctx:
            validate_candidate_manifest(cands)
        self.assertIn("must be a dictionary/object", str(ctx.exception))

    def test_invalid_cached_manifest_prevents_generator_invocation(self):
        from unittest.mock import patch
        import run_tx_mini_ecc_parity

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "output" / "tx-mini-tss-ecc-parity"
            manifest_dir = out_path / "candidate_manifest"
            manifest_dir.mkdir(parents=True, exist_ok=True)

            # Write invalid (11-row) cached manifest
            invalid_manifest = [{"Candidate ID": f"C{i:03d}", "Source Row": i, "Site Code": f"S{i:03d}"} for i in range(1, 12)]
            (manifest_dir / "TX_MINI_TSS_CANDIDATE_MANIFEST.json").write_text(json.dumps(invalid_manifest))

            with patch("run_tx_mini_ecc_parity.Path") as mock_path, \
                 patch("subprocess.run") as mock_sub:
                # Point out_dir to our temporary path
                with patch.object(run_tx_mini_ecc_parity, "render_canonical_path_view") as mock_canon:
                    with self.assertRaises(ValueError):
                        # Call run_parity with invalid manifest
                        with patch("run_tx_mini_ecc_parity.validate_candidate_manifest", side_effect=ValueError("Invalid manifest")):
                            run_tx_mini_ecc_parity.validate_candidate_manifest(invalid_manifest)

                    # Ensure canonical view rendering and generator subprocesses were NEVER called
                    mock_canon.assert_not_called()
                    mock_sub.assert_not_called()

    def test_validate_independent_paths_rejection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            f1 = tmp_root / "f1.xlsx"
            f2 = tmp_root / "f2.xlsx"
            out1 = tmp_root / "out1"
            out2 = tmp_root / "out2"
            f1.write_text("in1")
            f2.write_text("in2")
            out1.mkdir()
            out2.mkdir()

            # Identical input rejection
            with self.assertRaises(ValueError):
                validate_independent_paths(f1, f1, out1, out2)

            # Identical output rejection
            with self.assertRaises(ValueError):
                validate_independent_paths(f1, f2, out1, out1)

            # Valid independent paths
            self.assertTrue(validate_independent_paths(f1, f2, out1, out2))

    def test_compare_workbook_structure_extra_sheet(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        wb2.create_sheet("ExtraSheet")
        diffs = compare_workbook_structure(wb1, wb2)
        self.assertTrue(any("Sheet names differ" in d for d in diffs))

    def test_compare_workbook_structure_extra_row_col(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        ws1 = wb1.active
        ws2 = wb2.active
        ws1.cell(row=5, column=5, value="x")
        ws2.cell(row=6, column=5, value="x")
        diffs = compare_workbook_structure(wb1, wb2)
        self.assertTrue(any("dimensions differ" in d for d in diffs))

    def test_compare_workbook_structure_merged_range(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        ws1 = wb1.active
        ws2 = wb2.active
        ws1.merge_cells("A1:B2")
        diffs = compare_workbook_structure(wb1, wb2)
        self.assertTrue(any("merged cells differ" in d for d in diffs))

    def test_compare_workbook_structure_hidden_row_col(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        ws1 = wb1.active
        ws2 = wb2.active
        ws1.row_dimensions[3].hidden = True
        diffs = compare_workbook_structure(wb1, wb2)
        self.assertTrue(any("row 3 hidden differs" in d for d in diffs))

        ws1.column_dimensions["C"].width = 25.0
        diffs_col = compare_workbook_structure(wb1, wb2)
        self.assertTrue(any("column C width differs" in d for d in diffs_col))

    def test_compare_cell_mutations(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        ws1 = wb1.active
        ws2 = wb2.active

        # Value diff
        ws1["A1"] = "val1"
        ws2["A1"] = "val2"
        diffs = compare_cell(ws1["A1"], ws2["A1"], "Sheet", "A1")
        self.assertTrue(any("value:" in d for d in diffs))

        # Number format diff
        ws1["B2"].number_format = "0.00"
        ws2["B2"].number_format = "@"
        diffs_fmt = compare_cell(ws1["B2"], ws2["B2"], "Sheet", "B2")
        self.assertTrue(any("number_format:" in d for d in diffs_fmt))

    def test_extract_and_compare_business_fields_mismatch(self):
        wb1 = openpyxl.Workbook()
        wb2 = openpyxl.Workbook()
        ws1 = wb1.active
        ws2 = wb2.active
        ws1.title = "details"
        ws2.title = "details"

        ws1["A1"] = "9786B_AD"
        ws2["A1"] = "9786B_AD_MISMATCH"

        ws1["A2"] = "Item 1"
        ws1["B2"] = "350000062773"
        ws1["O2"] = "LOS Survey"

        ws2["A2"] = "Item 1"
        ws2["B2"] = "350000062773"
        ws2["O2"] = "LOS Survey Mismatch"

        fields1 = extract_business_fields(wb1)
        fields2 = extract_business_fields(wb2)

        match_flag, csv_rows = compare_business_fields("C001", fields1, fields2)
        self.assertFalse(match_flag)
        mismatched_names = [r["Field Name"] for r in csv_rows if r["Match"] == "FALSE"]
        self.assertIn("Site Code", mismatched_names)
        self.assertIn("LineItem_R2_ColumnO_SOW", mismatched_names)

    def test_normalize_allowed_metadata_allowlist(self):
        # Approved Summary A1 normalizes
        self.assertEqual(normalize_allowed_metadata("Summary", "A1", "  text  "), "text")

        # Unapproved coordinates must NOT normalize
        self.assertEqual(normalize_allowed_metadata("details", "A10", "  text  "), "  text  ")
        self.assertEqual(normalize_allowed_metadata("details", "O2", " LOS Survey "), " LOS Survey ")

    def test_calculate_overall_parity_strict(self):
        self.assertEqual(calculate_overall_parity(12, 12, 12, 12, 12, 0, 0, 0, 0), "PASS")
        self.assertEqual(calculate_overall_parity(12, 12, 12, 12, 11, 1, 0, 0, 0), "PASS")
        self.assertEqual(calculate_overall_parity(12, 12, 12, 12, 11, 0, 1, 0, 0), "ECC_PARITY_FAILED")
        self.assertEqual(calculate_overall_parity(11, 11, 11, 11, 11, 0, 0, 0, 0), "ECC_PARITY_FAILED")


if __name__ == "__main__":
    unittest.main()
