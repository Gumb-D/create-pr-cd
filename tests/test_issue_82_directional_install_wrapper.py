#!/usr/bin/env python3
"""Regression coverage for directional targets introduced by install verbs."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82DirectionalInstallWrapper(unittest.TestCase):
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

    def test_to_install_antenna_uses_target_size(self):
        result = self._resolve("Upgrade antenna 2.4m to install antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_to_install_new_antenna_uses_target_size(self):
        result = self._resolve("Upgrade antenna 2.4m to install new antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
