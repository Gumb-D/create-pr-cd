#!/usr/bin/env python3
"""Permanent regression coverage for direct antenna fields containing CIDR-like values."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82DirectCidr(unittest.TestCase):
    def test_direct_cidr_values_fail_closed(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "10.0.0.6/2",
                "MW Config Antenna Size FE": "192.168.1.2/2",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["ne_size"])
        self.assertIsNone(result["fe_size"])
        self.assertIsNone(result["selected_size"])

    def test_valid_direct_size_survives_near_cidr_noise(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "0.6m / 10.0.0.6/2",
                "MW Config Antenna Size FE": "0.6m",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": "",
            }
        )
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["ne_size"], 0.6)
        self.assertEqual(result["fe_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
