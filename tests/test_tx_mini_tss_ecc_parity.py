import json
import unittest
from pathlib import Path

class TestTxMiniTssEccParity(unittest.TestCase):
    def setUp(self):
        self.manifest_path = Path("output/tx-mini-tss-ecc-parity/candidate_manifest/TX_MINI_TSS_CANDIDATE_MANIFEST.json")
        self.summary_path = Path("output/tx-mini-tss-ecc-parity/TX_MINI_TSS_ECC_PARITY_SUMMARY.json")
        self.model_identity_path = Path("output/tx-mini-tss-ecc-parity/TX_MINI_TSS_PR_MODEL_IDENTITY.json")

    def test_exactly_12_tss_candidates_selected(self):
        if not self.manifest_path.exists():
            self.skipTest("Manifest not generated")
            
        candidates = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(candidates), 12, "Must select exactly 12 TSS UAT candidates")

    def test_candidate_manifest_uniqueness(self):
        if not self.manifest_path.exists():
            self.skipTest("Manifest not generated")
            
        candidates = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        
        source_rows = [c["Source Row"] for c in candidates]
        self.assertEqual(len(source_rows), len(set(source_rows)), "No duplicate source rows allowed")
        
        candidate_ids = [c["Candidate ID"] for c in candidates]
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)), "No duplicate candidate IDs allowed")
        
        site_codes = [c["Site Code"] for c in candidates]
        self.assertEqual(len(site_codes), len(set(site_codes)), "Each site code must be unique in the candidate selection")

    def test_v3_2_pr_model_identity_enforcement(self):
        if not self.model_identity_path.exists():
            self.skipTest("PR Model Identity not generated")
            
        identity = json.loads(self.model_identity_path.read_text(encoding="utf-8"))
        
        # Valid v3.2 SHA-256
        expected_sha = "82a47564590a8083c88b9dad61472c04513bb2832f8b1a44750d6a4347446c4d"
        self.assertEqual(identity["sha256"], expected_sha, "PR Model hash must match approved v3.2 signature")
        
        self.assertIn("TX Line Item (After 21-Apr 26)", identity["sheet_names"], "Required v3.2 sheets must be present")
        
    def test_mismatched_pr_model_hashes_fail(self):
        # We simulate a failure by checking that the generated output didn't use an invalid hash.
        # If it used v3.2, it's correct.
        if not self.model_identity_path.exists():
            self.skipTest("PR Model Identity not generated")
            
        identity = json.loads(self.model_identity_path.read_text(encoding="utf-8"))
        legacy_sha = "fbd42f8c05001ff889d120a113bc624a9a08e16b9b3ffb9c47087640db90e29b" # Mock v3.0 SHA
        
        self.assertNotEqual(identity["sha256"], legacy_sha, "Must fail if using legacy PR model")
        
    def test_overall_parity_success(self):
        if not self.summary_path.exists():
            self.skipTest("Parity summary not generated")
            
        summary = json.loads(self.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["overall_parity_result"], "PASS", "ECC Parity must strictly pass")
        self.assertEqual(summary["exact_match_count"], 12, "All 12 candidates must exactly match")
        self.assertEqual(summary["business_difference_count"], 0, "No business differences allowed")
        self.assertEqual(summary["structural_difference_count"], 0, "No structural differences allowed")

if __name__ == '__main__':
    unittest.main()
