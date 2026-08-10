import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from jendela_migration_decision import JENDELA_PROFILE_ID, derive_jendela_migration_decision


class TestIssue77JendelaRedesign(unittest.TestCase):
    def derive(self, *, before, tx_sow, final_backhaul="IGNORED"):
        return derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={
                "tx_before_migration": before,
                "tx_sow_raw": tx_sow,
                "final_backhaul": final_backhaul,
            },
        )

    def work_items(self, result):
        return [item["work_item"] for item in result["work_items"]]

    def test_final_backhaul_does_not_change_work_plan(self):
        expected = None
        for final_backhaul in ("", "Fiber Own Build", "Fiber LL", "Fiber OB/LL", "MW", "unexpected"):
            with self.subTest(final_backhaul=final_backhaul):
                result = self.derive(
                    before="Starlink",
                    tx_sow="BBU Patching / MW IDU Patching",
                    final_backhaul=final_backhaul,
                )
                self.assertEqual(result["classification"], "APPROVED")
                observed = self.work_items(result)
                if expected is None:
                    expected = observed
                self.assertEqual(observed, expected)
        self.assertEqual(expected, ["Dismantle Starlink", "BBU Patching / MW IDU Patching"])

    def test_tx_before_migration_controls_dismantle_only(self):
        cases = {
            "Starlink": ["Dismantle Starlink"],
            "MW": ["Dismantle MW"],
            "Microwave": ["Dismantle MW"],
        }
        for before, expected in cases.items():
            with self.subTest(before=before):
                result = self.derive(before=before, tx_sow="-")
                self.assertEqual(result["classification"], "APPROVED")
                self.assertEqual(self.work_items(result), expected)

        no_work = self.derive(before="Fiber Own Build", tx_sow="-")
        self.assertEqual(no_work["classification"], "APPROVED_NO_OUTPUT")
        self.assertEqual(self.work_items(no_work), [])

    def test_tx_sow_controls_additional_work_only(self):
        work_cases = {
            "BBU Patching / MW IDU Patching": ["BBU Patching / MW IDU Patching"],
            "BBU Patching": ["BBU Patching / MW IDU Patching"],
            "MW IDU Patching": ["BBU Patching / MW IDU Patching"],
            "MW New Link / Reroute": ["MW New Link"],
        }
        for tx_sow, expected in work_cases.items():
            with self.subTest(tx_sow=tx_sow):
                result = self.derive(before="Fiber Own Build", tx_sow=tx_sow)
                self.assertEqual(result["classification"], "APPROVED")
                self.assertEqual(self.work_items(result), expected)

        for tx_sow in ("MW by others", "-", "", None):
            with self.subTest(tx_sow=tx_sow):
                result = self.derive(before="Fiber Own Build", tx_sow=tx_sow)
                self.assertEqual(result["classification"], "APPROVED_NO_OUTPUT")
                self.assertEqual(result["reason_code"], "JENDELA_TI_NO_WORK_REQUIRED")
                self.assertEqual(self.work_items(result), [])

    def test_independent_decisions_are_combined_atomically(self):
        cases = [
            ("Starlink", "BBU Patching / MW IDU Patching", ["Dismantle Starlink", "BBU Patching / MW IDU Patching"]),
            ("MW", "MW New Link / Reroute", ["Dismantle MW", "MW New Link"]),
            ("Fiber Own Build", "MW New Link / Reroute", ["MW New Link"]),
            ("MW", "", ["Dismantle MW"]),
        ]
        for before, tx_sow, expected in cases:
            with self.subTest(before=before, tx_sow=tx_sow):
                result = self.derive(before=before, tx_sow=tx_sow)
                self.assertEqual(result["classification"], "APPROVED")
                self.assertEqual(self.work_items(result), expected)

        no_work = self.derive(before="Fiber Own Build", tx_sow="")
        self.assertEqual(no_work["classification"], "APPROVED_NO_OUTPUT")
        self.assertEqual(self.work_items(no_work), [])

    def test_missing_or_unknown_tx_before_migration_fails_closed(self):
        for before in (None, "", "Satellite", "Unknown"):
            with self.subTest(before=before):
                result = self.derive(before=before, tx_sow="-")
                self.assertEqual(result["classification"], "REVIEW_REQUIRED")
                self.assertEqual(result["work_items"], [])
                self.assertIn(result["reason_code"], {
                    "JENDELA_TX_BEFORE_MIGRATION_MISSING",
                    "JENDELA_TX_BEFORE_MIGRATION_NOT_APPROVED",
                })

    def test_unknown_actionable_tx_sow_fails_closed_without_partial_dismantle(self):
        result = self.derive(before="Starlink", tx_sow="Some New Work")
        self.assertEqual(result["classification"], "REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"], "JENDELA_TX_SOW_NOT_APPROVED")
        self.assertEqual(result["work_items"], [])

    def test_work_item_model_mapping_is_explicit_and_v4_1_backed(self):
        starlink = self.derive(before="Starlink", tx_sow="-")["work_items"][0]
        self.assertEqual(starlink["model_sow"], "Starlink Dismanle")
        self.assertEqual(starlink["required_pbom_codes"], ["350000597850", "350000597852"])

        patching = self.derive(before="Fiber Own Build", tx_sow="BBU Patching / MW IDU Patching")["work_items"][0]
        self.assertEqual(patching["model_sow"], "BBU Patching")
        self.assertEqual(patching["required_pbom_codes"], ["350001095420"])

        idu = self.derive(before="Fiber Own Build", tx_sow="MW IDU Patching")["work_items"][0]
        self.assertEqual(idu["model_sow"], "MW IDU Patching")
        self.assertEqual(idu["required_pbom_codes"], ["350001095420"])

        mw_new_link = self.derive(before="Fiber Own Build", tx_sow="MW New Link / Reroute")["work_items"][0]
        self.assertEqual(mw_new_link["model_sow"], "MW New Link / Reroute")

    def test_non_jendela_and_tss_are_unchanged(self):
        self.assertIsNone(
            derive_jendela_migration_decision(
                profile_id="tx_mini_pr_v1",
                scope="TI",
                pr_context={"tx_before_migration": "Starlink", "tx_sow_raw": "-"},
            )
        )
        self.assertIsNone(
            derive_jendela_migration_decision(
                profile_id=JENDELA_PROFILE_ID,
                scope="TSS",
                pr_context={"tx_before_migration": "Starlink", "tx_sow_raw": "-"},
            )
        )


if __name__ == "__main__":
    unittest.main()
