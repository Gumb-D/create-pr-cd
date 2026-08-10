#!/usr/bin/env python3
"""Codex regressions for replacement direction and sentence-ending bare sizes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82ReplacementPhrase(unittest.TestCase):
    def _resolve_common(self, text: str):
        return resolve_installation_antenna_evidence(
            {
                "MW Config Antenna Size NE": "",
                "MW Config Antenna Size FE": "",
                "NE SOW Details": "",
                "FE SOW Details": "",
                "TX SOW Details": text,
            }
        )

    def test_replace_existing_with_new_binds_only_new_size(self):
        result = self._resolve_common(
            "Replace existing antenna 2.4m with new antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_sentence_period_after_bare_decimal_is_allowed(self):
        result = self._resolve_common("Install antenna size 0.6.")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_ip_multi_dot_remains_rejected(self):
        result = self._resolve_common("Install antenna; new IP 1.2.3.4.")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["selected_size"])


if __name__ == "__main__":
    unittest.main()
