#!/usr/bin/env python3
"""Issue #34 regression contract for deterministic all-DU Planning PR selection."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SELECTOR_PATH = SCRIPTS / "planning_pr_selector.py"


class PlanningSelectorPresenceTest(unittest.TestCase):
    def test_planning_selector_module_exists(self) -> None:
        self.assertTrue(
            SELECTOR_PATH.exists(),
            msg="Issue #34 requires scripts/planning_pr_selector.py",
        )


@unittest.skipUnless(SELECTOR_PATH.exists(), "selector not implemented yet")
class PlanningSelectorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("planning_pr_selector", SELECTOR_PATH)
        if spec is None or spec.loader is None:
            raise AssertionError("Unable to load planning_pr_selector.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cls.module = module
        cls.select = staticmethod(module.select_planning_item)

    def test_selector_accepts_only_du_model_and_planning_subcontractor(self) -> None:
        parameter_names = list(inspect.signature(self.select).parameters)
        self.assertEqual(parameter_names, ["du_model_name", "subcontractor_planning"])
        self.assertNotIn("tx_planning_remarks", parameter_names)
        self.assertNotIn("tx_sow", parameter_names)

    def test_five_full_planning_du_models_use_350001143904(self) -> None:
        du_models = (
            "2023 TX Rollout",
            "2023 Celcomdigi BAU",
            "2024 Celcomdigi BAU",
            "Celcomdigi USP",
            "Jendela TX Migration",
        )
        for du_model in du_models:
            for subcon in ("GCI", "GTSB"):
                with self.subTest(du_model=du_model, subcon=subcon):
                    result = self.select(du_model, subcon)
                    self.assertEqual(result.status, "RESOLVED")
                    self.assertEqual(result.pbom_code, "350001143904")
                    self.assertEqual(result.quantity, 1)
                    self.assertEqual(result.unit, "Hop")
                    self.assertEqual(result.contract_subcontractor, subcon)

    def test_three_single_hop_du_models_use_350001143905(self) -> None:
        du_models = ("TX Mini Project", "MW EOS Swap", "ZTE TX MINI")
        for du_model in du_models:
            for subcon in ("GCI", "GTSB"):
                with self.subTest(du_model=du_model, subcon=subcon):
                    result = self.select(du_model, subcon)
                    self.assertEqual(result.status, "RESOLVED")
                    self.assertEqual(result.pbom_code, "350001143905")
                    self.assertEqual(result.quantity, 1)
                    self.assertEqual(result.unit, "Hop")
                    self.assertEqual(result.contract_subcontractor, subcon)

    def test_aa_values_use_only_350001042321_for_every_supported_du(self) -> None:
        du_models = (
            "2023 TX Rollout",
            "TX Mini Project",
            "2023 Celcomdigi BAU",
            "2024 Celcomdigi BAU",
            "Celcomdigi USP",
            "Jendela TX Migration",
            "MW EOS Swap",
            "ZTE TX MINI",
        )
        for du_model in du_models:
            for source_subcon, contract_subcon in (("GCI_AA", "GCI"), ("GTSB_AA", "GTSB")):
                with self.subTest(du_model=du_model, subcon=source_subcon):
                    result = self.select(du_model, source_subcon)
                    self.assertEqual(result.status, "RESOLVED")
                    self.assertEqual(result.pbom_code, "350001042321")
                    self.assertNotIn(result.pbom_code, {"350001143904", "350001143905"})
                    self.assertEqual(result.quantity, 1)
                    self.assertEqual(result.unit, "Hop")
                    self.assertEqual(result.contract_subcontractor, contract_subcon)

    def test_whitespace_does_not_change_approved_exact_value(self) -> None:
        result = self.select("  MW EOS Swap  ", "  GCI_AA  ")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.pbom_code, "350001042321")
        self.assertEqual(result.contract_subcontractor, "GCI")

    def test_unknown_nonblank_planning_subcontractor_fails_closed(self) -> None:
        result = self.select("2023 TX Rollout", "UNKNOWN_VENDOR")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIsNone(result.pbom_code)
        self.assertIsNone(result.contract_subcontractor)
        self.assertEqual(result.reason_code, "PLANNING_SUBCONTRACTOR_NOT_APPROVED")

    def test_unknown_du_model_fails_closed(self) -> None:
        result = self.select("Unsupported DU", "GCI")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIsNone(result.pbom_code)
        self.assertEqual(result.reason_code, "PLANNING_DU_MODEL_NOT_APPROVED")

    def test_blank_planning_subcontractor_is_not_applicable(self) -> None:
        result = self.select("2023 TX Rollout", "  ")
        self.assertEqual(result.status, "NOT_APPLICABLE")
        self.assertIsNone(result.pbom_code)
        self.assertEqual(result.reason_code, "PLANNING_SUBCONTRACTOR_BLANK")


if __name__ == "__main__":
    unittest.main()
