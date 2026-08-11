#!/usr/bin/env python3
"""Regression coverage for standalone and directional antenna replacement actions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82StandaloneReplacement(unittest.TestCase):
    def _resolve(self, text: str):
        return resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": text,
            }
        )

    def test_replace_antenna_is_installation_intent(self):
        result = self._resolve("Replace antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_swap_antenna_is_installation_intent(self):
        result = self._resolve("Swap antenna 1.2m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 1.2)
        self.assertEqual(result["selected_size"], 1.2)

    def test_swap_for_antenna_uses_target_size(self):
        result = self._resolve("Swap antenna 2.4m for antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
