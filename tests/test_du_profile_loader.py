import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from du_profile_loader import ProfileValidationError, load_du_profile


class TestDuProfileLoader(unittest.TestCase):
    def test_draft_tx_mini_profile_loads_without_claiming_production_readiness(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["export_structure"]["header_rows"], [0, 1, 2, 3])
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])

    def test_production_profile_requires_approved_header_hash_and_approved_mapping(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        profile["status"] = "PRODUCTION"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "unsafe.yaml"
            path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaises(ProfileValidationError):
                load_du_profile(path)


if __name__ == "__main__":
    unittest.main()
