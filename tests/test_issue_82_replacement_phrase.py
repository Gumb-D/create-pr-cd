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
        result = self._resolve_common("Replace existing antenna 2.4m with new antenna 0.6m")
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
        result = self._resolve_common("Dismantle antenna 2.4. Install antenna 0.6.")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_upgrade_direction_excludes_source_size(self):
        result = self._resolve_common("Upgrade antenna 2.4m to new antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_replacement_marker_is_installation_intent(self):
        result = self._resolve_common("Replace existing antenna 2.4m with replacement antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_directional_target_without_adjective_excludes_source_size(self):
        result = self._resolve_common("Upgrade antenna 2.4m to antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_slash_delimited_actions_exclude_dismantle_size(self):
        result = self._resolve_common("Dismantle antenna 2.4m / install antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_non_metre_units_are_not_bare_antenna_diameters(self):
        for text in ("Install antenna bracket 2.4mm", "Install antenna at clearance 2.4cm"):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["selected_size"])

    def test_slash_build_action_uses_only_built_antenna_size(self):
        result = self._resolve_common("Dismantle antenna 2.4m / build antenna 0.6m")
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
        result = self._resolve_common("Upgrade antenna 2.4m to antenna mounted at 3.0m height")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["common_size"])
        self.assertIsNone(result["selected_size"])

    def test_punctuation_prefixed_non_metre_unit_is_rejected(self):
        result = self._resolve_common("Install antenna bracket 2.4-inch")
        self.assertEqual(result["status"], "MISSING")
        self.assertIsNone(result["common_size"])
        self.assertIsNone(result["selected_size"])

    def test_reverse_directional_target_uses_new_size(self):
        for transition in ("to", "with", "by"):
            text = f"Upgrade antenna 2.4m {transition} 0.6m antenna"
            with self.subTest(transition=transition):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_colon_delimited_action_excludes_dismantle_size(self):
        result = self._resolve_common("Dismantle antenna 2.4m: install antenna 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)
        self.assertEqual(result["selected_size"], 0.6)

    def test_colon_inside_size_phrase_stays_valid(self):
        result = self._resolve_common("Install antenna size: 0.6m")
        self.assertEqual(result["status"], "RESOLVED_COMMON")
        self.assertEqual(result["common_size"], 0.6)

    def test_punctuated_quote_units_are_rejected(self):
        for punctuation in ("-", "/", "("):
            text = f'Install antenna diameter 2.4{punctuation}"'
            with self.subTest(punctuation=punctuation):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["selected_size"])

    def test_invalid_reverse_directional_target_fails_closed(self):
        for text in (
            "Upgrade antenna 2.4m to 0.6-inch antenna",
            "Upgrade antenna 2.4m to 0.6mm antenna",
            'Upgrade antenna 2.4m to 0.6" antenna',
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_ascii_and_unicode_foot_units_fail_closed(self):
        for marker in ("'", "′", "’", "‘"):
            for text in (
                f"Install antenna diameter 0.6{marker}",
                f"Upgrade antenna 2.4m to 0.6{marker} antenna",
            ):
                with self.subTest(marker=marker, text=text):
                    result = self._resolve_common(text)
                    self.assertEqual(result["status"], "MISSING")
                    self.assertIsNone(result["common_size"])
                    self.assertIsNone(result["selected_size"])

    def test_question_and_exclamation_split_action_clauses(self):
        for marker in ("!", "?"):
            text = f"Dismantle antenna 2.4m{marker} Install antenna 0.6m"
            with self.subTest(marker=marker):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_invalid_reverse_target_with_descriptor_fails_closed(self):
        for text in (
            "Upgrade antenna 2.4m to 0.6-inch diameter antenna",
            "Upgrade antenna 2.4m to 0.6' diameter antenna",
            "Upgrade antenna 2.4m to 0.6mm diameter antenna",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_invalid_reverse_target_with_unit_punctuation_fails_closed(self):
        for text in (
            "Upgrade antenna 2.4m to 0.6 in. diameter antenna",
            "Upgrade antenna 2.4m to 0.6 [inch] diameter antenna",
            "Upgrade antenna 2.4m to 0.6 (inch) diameter antenna",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_bare_reverse_antenna_targets_remain_supported(self):
        for text, expected in (
            ("Upgrade antenna 2.4m to 0.6 antenna", 0.6),
            ("New 1.2 dish", 1.2),
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], expected)
                self.assertEqual(result["selected_size"], expected)

    def test_reverse_noun_cannot_cross_newline_clause_boundary(self):
        for text in (
            "New radio version 1.2\nantenna inspection only",
            "Upgrade software 1.2\ndish inspection only",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])

    def test_target_first_replacement_excludes_replaced_source_size(self):
        for text in (
            "Install antenna 0.6m replacing antenna 2.4m",
            "Install antenna 0.6m to replace antenna 2.4m",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_carriage_return_is_hard_action_line_boundary(self):
        for boundary in ("\r", "\r\n"):
            text = f"Dismantle antenna 2.4m{boundary}Install antenna 0.6m"
            with self.subTest(boundary=repr(boundary)):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "RESOLVED_COMMON")
                self.assertEqual(result["common_size"], 0.6)
                self.assertEqual(result["selected_size"], 0.6)

    def test_negated_installation_phrases_fail_closed(self):
        for text in (
            "Do not install antenna 2.4m",
            "No new antenna 1.2m required",
            "Not required to install antenna 0.6m",
            "Without installing antenna 0.6m",
        ):
            with self.subTest(text=text):
                result = self._resolve_common(text)
                self.assertEqual(result["status"], "MISSING")
                self.assertIsNone(result["common_size"])
                self.assertIsNone(result["selected_size"])


if __name__ == "__main__":
    unittest.main()
