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

    def test_bare_decimal_sentence_boundary_excludes_dismantle_size(self):
        result = self._resolve_common(
            "Dismantle antenna 2.4. Install antenna 0.6."
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_upgrade_direction_excludes_source_size(self):
        result = self._resolve_common(
            "Upgrade antenna 2.4m to new antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_replacement_marker_is_installation_intent(self):
        result = self._resolve_common(
            "Replace existing antenna 2.4m with replacement antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_directional_target_without_adjective_excludes_source_size(self):
        result = self._resolve_common("Upgrade antenna 2.4m to antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_slash_delimited_actions_exclude_dismantle_size(self):
        result = self._resolve_common(
            "Dismantle antenna 2.4m / install antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_non_metre_units_are_not_bare_antenna_diameters(self):
        for text in (
            "Install antenna bracket 2.4mm",
            "Install antenna at clearance 2.4cm",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["selected_size"])

    def test_slash_build_action_uses_only_built_antenna_size(self):
        result = self._resolve_common(
            "Dismantle antenna 2.4m / build antenna 0.6m"
        )
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_dash_delimited_actions_exclude_dismantle_size(self):
        for separator in ("-", "–", "—"):
            text = f"Dismantle antenna 2.4m {separator} install antenna 0.6m"
            with self.subTest(separator=separator):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_directional_height_is_not_antenna_diameter(self):
        result = self._resolve_common(
            "Upgrade antenna 2.4m to antenna mounted at 3.0m height"
        )
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["common_size"])
        self.assertIsNone(result["selected_size"])

    def test_punctuation_prefixed_non_metre_unit_is_rejected(self):
        result = self._resolve_common("Install antenna bracket 2.4-inch")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["common_size"])
        self.assertIsNone(result["selected_size"])


if __name__ == "__main__":
    unittest.main()
