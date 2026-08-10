#!/usr/bin/env python3
"""Negative regression tests for Issue #82 antenna evidence parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82CommonDetailFalsePositiveGuard(unittest.TestCase):
    def test_common_detail_cable_length_is_not_antenna_evidence(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": "MW swap; install IF cable 3.0m",
            }
        )
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["selected_size"])
        self.assertEqual(result["evidence"], [])

    def test_common_detail_requires_antenna_context_for_metre_value(self):
        result = resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": "MW swap; install antenna 1.2m",
            }
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["selected_size"], 1.2)
        self.assertEqual(result["group_source"], "TX SOW Details")


if __name__ == "__main__":
    unittest.main()
