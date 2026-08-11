#!/usr/bin/env python3
"""Final Codex regression: punctuation must separate old/new antenna actions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence


class TestIssue82PunctuationIntentBoundaries(unittest.TestCase):
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

    def test_old_and_new_actions_split_by_common_punctuation(self):
        cases = (
            "Dismantle antenna 2.4m, install antenna 0.6m",
            "Dismantle antenna 2.4m & install antenna 0.6m",
            "Dismantle antenna 2.4m. Install antenna 0.6m",
        )
        for text in cases:
            with self.subTest(text=text):
                result = self._resolve(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
