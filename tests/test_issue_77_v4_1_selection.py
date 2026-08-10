import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from jendela_migration_decision import JENDELA_PROFILE_ID, derive_jendela_migration_decision
from pr_helpers import is_mw_reroute_row, load_pr_model_items


CANDIDATE = ROOT / "Info" / "input" / "pr_model_v4.1.xlsx"


class TestIssue77V41Selection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.ti_models = load_pr_model_items(CANDIDATE)

    def _mandatory_pboms(self, sow):
        return {
            item["PBOM_Code"]
            for item in self.ti_models
            if item["SOW"] == sow and item["Is_Mandatory"]
        }

    def test_starlink_mandatory_pboms_match_v4_1(self):
        self.assertEqual(
            self._mandatory_pboms("Starlink Dismanle"),
            {"350000597850", "350000597852"},
        )

    def test_split_patching_models_have_same_mandatory_business_pbom(self):
        self.assertEqual(self._mandatory_pboms("BBU Patching"), {"350001095420"})
        self.assertEqual(self._mandatory_pboms("MW IDU Patching"), {"350001095420"})

    def test_v4_1_reroute_only_rows_are_separated_by_model_remarks(self):
        new_link_rows = [item for item in self.ti_models if item["SOW"] == "MW New Link / Reroute"]
        reroute_rows = [item for item in self.ti_models if item["SOW"] == "MW Reroute"]
        self.assertTrue(new_link_rows)
        self.assertTrue(reroute_rows)
        self.assertTrue(all(item.get("Remarks", "").casefold() != "reroute" for item in new_link_rows))
        self.assertTrue(all(item.get("Remarks", "").casefold() == "reroute" for item in reroute_rows))
        self.assertTrue(all(item.get("Source_SOW") == "MW New Link / Reroute" for item in reroute_rows))
        self.assertTrue(any("New - MW Link" in item["Description"] for item in new_link_rows))
        self.assertTrue(any("dismantl" in item["Description"].casefold() for item in reroute_rows))

    def test_jendela_new_link_work_item_does_not_enter_legacy_reroute_path(self):
        jendela_row = {
            "DU Profile ID": JENDELA_PROFILE_ID,
            "Migration Work Item": "MW New Link",
            "Tx SOW": "MW New Link / Reroute",
        }
        ordinary_row = {
            "DU Profile ID": "tx_mini_pr_v1",
            "Migration Work Item": "",
            "Tx SOW": "MW New Link / Reroute",
        }
        self.assertFalse(is_mw_reroute_row(jendela_row))
        self.assertTrue(is_mw_reroute_row(ordinary_row))

    def test_decision_uses_only_v4_1_sow_names_and_fixed_pboms(self):
        starlink = derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={"tx_before_migration": "Starlink", "tx_sow_raw": "-", "final_backhaul": "ignored"},
        )
        self.assertEqual(starlink["work_items"][0]["model_sow"], "Starlink Dismanle")
        self.assertEqual(
            starlink["work_items"][0]["required_pbom_codes"],
            ["350000597850", "350000597852"],
        )

        patching = derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={
                "tx_before_migration": "Fiber Own Build",
                "tx_sow_raw": "BBU Patching / MW IDU Patching",
                "final_backhaul": "ignored",
            },
        )
        self.assertEqual(patching["work_items"][0]["model_sow"], "BBU Patching")
        self.assertEqual(patching["work_items"][0]["required_pbom_codes"], ["350001095420"])

        new_link = derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={
                "tx_before_migration": "Fiber Own Build",
                "tx_sow_raw": "MW New Link / Reroute",
                "final_backhaul": "ignored",
            },
        )
        self.assertEqual(new_link["work_items"][0]["model_sow"], "MW New Link / Reroute")


if __name__ == "__main__":
    unittest.main()
