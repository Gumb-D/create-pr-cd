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

    def test_swap_for_determined_forward_target_uses_target_size(self):
        for text in (
            "Swap antenna 2.4m for a new antenna 0.6m",
            "Swap antenna 2.4m for the replacement antenna 0.6m",
        ):
            with self.subTest(text=text):
                result = self._resolve(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_swap_for_determined_reverse_target_uses_target_size(self):
        result = self._resolve("Swap antenna 2.4m for an 0.6m antenna")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_swap_for_multiline_determined_target_fails_closed(self):
        result = self._resolve("Swap antenna 2.4m for\na new antenna 0.6m")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["common_size"])
        self.assertIsNone(result["selected_size"])

    def test_swap_for_multiline_reverse_target_fails_closed(self):
        for text in (
            "Swap antenna 2.4m for an\n0.6m antenna",
            "Swap antenna 2.4m for\nan 0.6m antenna",
        ):
            with self.subTest(text=text):
                result = self._resolve(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_multiline_invalid_unit_reverse_target_fails_closed(self):
        for text in (
            "Upgrade antenna 2.4m to\n0.6-inch antenna",
            "Swap antenna 2.4m for\n0.6 [inch] antenna",
        ):
            with self.subTest(text=text):
                result = self._resolve(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_size_first_source_multiline_target_fails_closed(self):
        for text in (
            "Upgrade 2.4m antenna to\n0.6m antenna",
            "Replace 2.4m dish with\n0.6m dish",
        ):
            with self.subTest(text=text):
                result = self._resolve(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_unrelated_multiline_antenna_port_does_not_discard_valid_size(self):
        result = self._resolve("Install antenna 0.6m. Route cable to\nantenna port")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_unrelated_multiline_antenna_distance_does_not_discard_valid_size(self):
        result = self._resolve("Install antenna 0.6m. Route cable to\nantenna 10m away")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_unrelated_upgrade_cable_route_does_not_discard_valid_size(self):
        result = self._resolve("Install antenna 0.6m. Upgrade cable route to\nantenna 10m away")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
