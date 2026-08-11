import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from create_pr_impl import _renderer_rows
from jendela_migration_decision import (
    JENDELA_PROFILE_ID,
    derive_jendela_migration_decision,
    parse_jendela_before_mw_antenna_size,
)


class TestIssue84JendelaBeforeMwAntenna(unittest.TestCase):
    def derive(self, *, before="MW", tx_sow="BBU Patching", before_mw_config_raw="18G 1.2 SP 1+0"):
        return derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={
                "tx_before_migration": before,
                "tx_sow_raw": tx_sow,
                "final_backhaul": "Fiber Own Build",
            },
            technical_context={
                "before_mw_config_raw": before_mw_config_raw,
                "antenna_size_ne": "",
                "antenna_size_fe": "",
            },
        )

    def test_4034r_mw_config_parses_before_antenna_size(self):
        self.assertEqual(parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0"), 1.2)

    def test_parser_continues_past_bandwidth_token_to_valid_antenna_size(self):
        self.assertEqual(
            parse_jendela_before_mw_antenna_size("18G 112M 1.2M SP 1+0"),
            1.2,
        )

    def test_parser_uses_structural_antenna_position_after_in_range_bandwidth(self):
        self.assertEqual(
            parse_jendela_before_mw_antenna_size("18G 3.5M 1.2M SP 1+0"),
            1.2,
        )

    def test_parser_fails_closed_when_multiple_polarized_antenna_sizes_disagree(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 0.6 SP 1+0 / 23G 1.2 SP 1+0"),
        )

    def test_parser_fails_closed_when_any_polarized_config_has_invalid_antenna_size(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0 / 23G 12 SP 1+0"),
        )

    def test_parser_fails_closed_when_invalid_polarized_config_comes_first(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 12 SP 1+0 / 23G 1.2 SP 1+0"),
        )

    def test_parser_fails_closed_when_polarized_link_has_nonnumeric_antenna(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0 / 23G N/A SP 1+0"),
        )

    def test_parser_fails_closed_when_polarized_link_has_dash_antenna(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0 / 23G - SP 1+0"),
        )

    def test_parser_fails_closed_when_polarized_link_omits_antenna(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0 / 23G SP 1+0"),
        )

    def test_parser_accepts_repeated_polarized_configs_when_antenna_size_agrees(self):
        self.assertEqual(
            parse_jendela_before_mw_antenna_size("18G 1.2 SP 1+0 / 23G 1.2 SP 1+0"),
            1.2,
        )

    def test_parser_fails_closed_when_multiple_in_range_m_tokens_have_no_polarization_structure(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 3.5M 1.2M 1+0"),
        )

    def test_parser_fails_closed_when_duplicate_numeric_m_tokens_are_structurally_ambiguous(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2M 1.20M 1+0"),
        )

    def test_parser_fails_closed_on_unpolarized_bandwidth_only_token(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 3.5M 1+0"),
        )

    def test_parser_requires_polarization_structure_even_for_plausible_single_metre_token(self):
        self.assertIsNone(
            parse_jendela_before_mw_antenna_size("18G 1.2M 1+0"),
        )

    def test_mw_dismantle_is_enriched_from_mw_config_without_ne_fe_fallback(self):
        result = self.derive()
        self.assertEqual(result["classification"], "APPROVED")
        self.assertEqual(
            [item["work_item"] for item in result["work_items"]],
            ["Dismantle MW", "BBU Patching / MW IDU Patching"],
        )
        dismantle = result["work_items"][0]
        self.assertEqual(dismantle["before_mw_config_raw"], "18G 1.2 SP 1+0")
        self.assertEqual(dismantle["before_mw_antenna_size_m"], 1.2)
        patching = result["work_items"][1]
        self.assertNotIn("before_mw_antenna_size_m", patching)

    def test_missing_before_config_fails_closed_even_when_after_ne_fe_exist(self):
        result = derive_jendela_migration_decision(
            profile_id=JENDELA_PROFILE_ID,
            scope="TI",
            pr_context={
                "tx_before_migration": "MW",
                "tx_sow_raw": "MW New Link / Reroute",
                "final_backhaul": "MW",
            },
            technical_context={
                "before_mw_config_raw": "",
                "antenna_size_ne": "0.6",
                "antenna_size_fe": "0.9",
            },
        )
        self.assertEqual(result["classification"], "REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"], "JENDELA_BEFORE_MW_ANTENNA_MISSING")
        self.assertEqual(result["work_items"], [])

    def test_renderer_projects_before_size_only_to_dismantle_row(self):
        decision = self.derive(tx_sow="MW New Link / Reroute")
        record = {
            "identity": {"source_row_number": 4034},
            "site": {"site_code": "4034R", "site_name": "", "du_key": ""},
            "pr_context": {
                "region": "Northern",
                "state": "Perak",
                "tx_sow_raw": "MW New Link / Reroute",
                "tx_sow_normalized": "MW New Link / Reroute",
                "tx_upgrade_scope_raw": "",
                "subcontractor_tss": "",
                "subcontractor_ti": "TEST SUBCON",
                "migration_decision": decision,
            },
            "technical_context": {
                "latitude": None,
                "longitude": None,
                "antenna_size_ne": "0.6",
                "antenna_size_fe": "0.9",
                "boq_configuration": "",
                "tx_sow_details": "",
                "ne_sow_details": "",
                "fe_sow_details": "",
            },
            "approved_contract": {"scope": "TI", "subcontractor": "TEST SUBCON"},
            "validation": {"profile_id": JENDELA_PROFILE_ID},
        }

        rows = _renderer_rows(record)
        self.assertEqual(len(rows), 2)
        dismantle, install = rows

        self.assertEqual(dismantle["Migration Work Item"], "Dismantle MW")
        self.assertEqual(dismantle["MW Config Antenna Size NE"], 1.2)
        self.assertEqual(dismantle["MW Config Antenna Size FE"], 1.2)

        self.assertEqual(install["Migration Work Item"], "MW New Link")
        self.assertEqual(install["MW Config Antenna Size NE"], "0.6")
        self.assertEqual(install["MW Config Antenna Size FE"], "0.9")


if __name__ == "__main__":
    unittest.main()
