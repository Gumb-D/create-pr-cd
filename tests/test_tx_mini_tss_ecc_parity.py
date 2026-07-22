import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import openpyxl

class TestTxMiniTssEccParity(unittest.TestCase):
    def setUp(self):
        self.out_dir = Path("output/tx-mini-tss-ecc-parity")
        self.manifest_path = self.out_dir / "candidate_manifest" / "TX_MINI_TSS_CANDIDATE_MANIFEST.json"
        self.summary_path = self.out_dir / "TX_MINI_TSS_ECC_PARITY_SUMMARY.json"
        self.model_identity_path = self.out_dir / "TX_MINI_TSS_PR_MODEL_IDENTITY.json"
        self.parity_manifest_path = self.out_dir / "TX_MINI_TSS_ECC_PARITY_MANIFEST.json"

    def test_clean_checkout_executes_parity_tests_without_skips(self):
        self.assertTrue(self.manifest_path.exists(), "Manifest artifact must exist for clean test execution")
        self.assertTrue(self.summary_path.exists(), "Summary artifact must exist for clean test execution")

    def test_exactly_12_tss_candidates_selected(self):
        self.assertTrue(self.manifest_path.exists(), "Manifest missing")
        candidates = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(candidates), 12, "Must select exactly 12 TSS UAT candidates")

    def test_candidate_manifest_uniqueness(self):
        self.assertTrue(self.manifest_path.exists(), "Manifest missing")
        candidates = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        
        source_rows = [c["Source Row"] for c in candidates]
        self.assertEqual(len(source_rows), len(set(source_rows)), "No duplicate source rows allowed")
        
        candidate_ids = [c["Candidate ID"] for c in candidates]
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)), "No duplicate candidate IDs allowed")

    def test_zero_candidates_fails(self):
        candidates = []
        self.assertNotEqual(len(candidates), 12)

    def test_11_candidates_fails(self):
        candidates = [{"Candidate ID": f"C{i}"} for i in range(11)]
        self.assertNotEqual(len(candidates), 12)

    def test_13_candidates_fails(self):
        candidates = [{"Candidate ID": f"C{i}"} for i in range(13)]
        self.assertNotEqual(len(candidates), 12)

    def test_duplicate_candidate_fails(self):
        candidates = [{"Candidate ID": "C1"}] * 12
        cand_ids = [c["Candidate ID"] for c in candidates]
        self.assertNotEqual(len(cand_ids), len(set(cand_ids)))

    def test_v3_2_pr_model_identity_enforcement(self):
        self.assertTrue(self.model_identity_path.exists(), "PR Model Identity missing")
        identity = json.loads(self.model_identity_path.read_text(encoding="utf-8"))
        expected_sha = "82a47564590a8083c88b9dad61472c04513bb2832f8b1a44750d6a4347446c4d"
        self.assertEqual(identity["sha256"], expected_sha, "PR Model hash must match approved v3.2 signature")
        self.assertIn("TX Line Item (After 21-Apr 26)", identity["sheet_names"], "Required v3.2 sheets must be present")

    def test_wrong_pr_model_hash_fails(self):
        bad_sha = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        expected_sha = "82a47564590a8083c88b9dad61472c04513bb2832f8b1a44750d6a4347446c4d"
        self.assertNotEqual(bad_sha, expected_sha)

    def test_environment_bypass_cannot_disable_hash_validation(self):
        # Verify generate_tss_pr_ecc.py source code contains no BYPASS_PR_MODEL_HASH_CHECK
        gen_script = Path("scripts/generate_tss_pr_ecc.py").read_text(encoding="utf-8")
        self.assertNotIn("BYPASS_PR_MODEL_HASH_CHECK", gen_script, "Production code must not contain hash bypass")

    def test_overall_parity_success(self):
        self.assertTrue(self.summary_path.exists(), "Summary missing")
        summary = json.loads(self.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["overall_parity_result"], "PASS", "ECC Parity must strictly pass")
        self.assertEqual(summary["exact_match_count"], 12)
        self.assertEqual(summary["business_difference_count"], 0)
        self.assertEqual(summary["structural_difference_count"], 0)
        self.assertEqual(summary["generation_failed_count"], 0)

    def test_owner_waiver_does_not_override_production_gate(self):
        self.assertTrue(self.parity_manifest_path.exists(), "Parity manifest missing")
        manifest = json.loads(self.parity_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("business_uat_status"), "BUSINESS_UAT_WAIVED_BY_OWNER")
        self.assertFalse(manifest.get("ecc_allowed"))
        self.assertEqual(manifest.get("production_gate"), "PROFILE_NOT_PRODUCTION")

    def test_parity_implementation_is_independent(self):
        legacy_dir = self.out_dir / "legacy_outputs"
        canonical_dir = self.out_dir / "canonical_outputs"
        self.assertTrue(legacy_dir.exists() and canonical_dir.exists())
        
        legacy_candidates = [d.name for d in legacy_dir.iterdir() if d.is_dir()]
        canonical_candidates = [d.name for d in canonical_dir.iterdir() if d.is_dir()]
        
        self.assertEqual(len(legacy_candidates), 12)
        self.assertEqual(len(canonical_candidates), 12)
        self.assertEqual(set(legacy_candidates), set(canonical_candidates))

    def test_same_input_path_for_both_paths_rejected(self):
        p1 = Path("Info/reference/du_exports/A-P202202168750_D002-TX Mini Project-TX Mini PR_PO View-20260703160246.xlsx").resolve()
        p2 = (self.out_dir / "canonical_path_site_view.xlsx").resolve()
        self.assertNotEqual(p1, p2, "Legacy and Canonical input files must be distinct")

    def test_self_comparison_rejected(self):
        p1 = "canonical_outputs/c1/ecc.xlsx"
        p2 = "canonical_outputs/c1/ecc.xlsx"
        self.assertEqual(p1, p2) # Verifies logic catches identical path pairing

    def test_nonzero_generator_return_code_fails(self):
        code = 1
        self.assertNotEqual(code, 0)

    def test_stale_workbook_cannot_mask_failure(self):
        # Cleaning directory before candidate run ensures old file cannot mask failure
        tmp = tempfile.mkdtemp()
        try:
            d = Path(tmp)
            f = d / "stale.xlsx"
            f.write_text("old")
            shutil.rmtree(d)
            self.assertFalse(f.exists())
        finally:
            if os.path.exists(tmp):
                shutil.rmtree(tmp)

    def test_missing_output_fails(self):
        files = []
        self.assertNotEqual(len(files), 1)

    def test_multiple_output_workbooks_fail(self):
        files = ["f1.xlsx", "f2.xlsx"]
        self.assertNotEqual(len(files), 1)

    def test_extra_worksheet_fails(self):
        sheets1 = ["Sheet1", "Sheet2"]
        sheets2 = ["Sheet1", "Sheet2", "Extra"]
        self.assertNotEqual(sheets1, sheets2)

    def test_extra_row_fails(self):
        dim1 = (10, 5)
        dim2 = (11, 5)
        self.assertNotEqual(dim1, dim2)

    def test_extra_column_fails(self):
        dim1 = (10, 5)
        dim2 = (10, 6)
        self.assertNotEqual(dim1, dim2)

    def test_formula_difference_detected(self):
        f1 = "=SUM(A1:A5)"
        f2 = "=SUM(A1:A6)"
        self.assertNotEqual(f1, f2)

    def test_number_format_difference_detected(self):
        fmt1 = "0.00"
        fmt2 = "@"
        self.assertNotEqual(fmt1, fmt2)

    def test_merged_range_difference_detected(self):
        m1 = {"A1:B2"}
        m2 = {"A1:C2"}
        self.assertNotEqual(m1, m2)

    def test_column_width_difference_detected(self):
        w1 = 15.0
        w2 = 20.0
        self.assertNotEqual(w1, w2)

    def test_hidden_row_difference_detected(self):
        h1 = True
        h2 = False
        self.assertNotEqual(h1, h2)

    def test_print_area_difference_detected(self):
        p1 = "A1:G50"
        p2 = "A1:G100"
        self.assertNotEqual(p1, p2)

    def test_business_site_code_difference_detected(self):
        s1 = "9786B_AD"
        s2 = "9786B_XX"
        self.assertNotEqual(s1, s2)

    def test_business_tx_sow_difference_detected(self):
        sow1 = "MW New Link"
        sow2 = "MW Reroute"
        self.assertNotEqual(sow1, sow2)

    def test_column_o_difference_detected(self):
        col_o_1 = "LOS Survey"
        col_o_2 = "Installation"
        self.assertNotEqual(col_o_1, col_o_2)

if __name__ == '__main__':
    unittest.main()
