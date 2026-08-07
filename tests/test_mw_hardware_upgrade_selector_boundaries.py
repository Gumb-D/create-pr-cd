#!/usr/bin/env python3
"""Boundary regression tests for Issue #69 hardware subtype evidence parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from mw_hardware_upgrade_selector import resolve_mw_hardware_upgrade_subtype  # noqa: E402


class TestMwHardwareUpgradeSelectorBoundaries(unittest.TestCase):
    def test_idu_board_installation_is_classified_as_idu_work(self):
        evidence = {
            "customer site code": "HW_MD2",
            "TX Upgrade Scope": "TSS+AA+TI",
            "BOQ Configuration": "Install new MD2 card at NE and FE. Re-use existing ODU.",
            "TX SOW Details": "Install new MD2 card at NE and FE. Re-use existing ODU.",
            "NE SOW Details": "Install new MD2 card. Re-use existing ODU.",
            "FE SOW Details": "Install new MD2 card. Re-use existing ODU.",
        }

        result = resolve_mw_hardware_upgrade_subtype(evidence)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["subtype"], "IDU_WITHOUT_SITE_SURVEY")
        self.assertNotIn("pbom_code", result)

    def test_field_boundaries_prevent_reuse_text_from_becoming_new_idu_work(self):
        evidence = {
            "customer site code": "HW_FIELD_BOUNDARY",
            "TX Upgrade Scope": "TSS+AA+TI",
            "BOQ Configuration": "Reuse existing IDU RTN910A",
            "TX SOW Details": "MW Hardware Upgrade. New XMC-3E ODU",
            "NE SOW Details": "Reuse existing IDU RTN910A",
            "FE SOW Details": "Install new XMC-3E ODU",
        }

        result = resolve_mw_hardware_upgrade_subtype(evidence)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["subtype"], "ODU_WITH_SITE_SURVEY")
        self.assertNotIn("pbom_code", result)
        self.assertFalse(result["signals"]["new_idu"])


if __name__ == "__main__":
    unittest.main()
