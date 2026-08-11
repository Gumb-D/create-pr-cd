#!/usr/bin/env python3
"""Permanent regression coverage for directional targets introduced by install verbs."""
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

    def _assert_target_size(self, text: str, expected: float = 0.6):
        result = self._resolve(text)
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], expected)
        self.assertEqual(result["selected_size"], expected)

    def test_to_install_antenna_uses_target_size(self):
        self._assert_target_size("Upgrade antenna 2.4m to install antenna 0.6m")

    def test_to_install_new_antenna_uses_target_size(self):
        self._assert_target_size("Upgrade antenna 2.4m to install new antenna 0.6m")

    def test_to_install_a_new_antenna_uses_target_size(self):
        self._assert_target_size("Upgrade antenna 2.4m to install a new antenna 0.6m")

    def test_to_install_an_antenna_uses_target_size(self):
        self._assert_target_size("Upgrade antenna 2.4m to install an antenna 0.6m")

    def test_to_install_the_replacement_antenna_uses_target_size(self):
        self._assert_target_size("Upgrade antenna 2.4m to install the replacement antenna 0.6m")


if __name__ == "__main__":
    unittest.main()
