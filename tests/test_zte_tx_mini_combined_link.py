"""Approved combined category regressions; no private workbook is checked in."""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import test_scope_actual_end_eligibility as date_fixture
from test_tx_mini_negative_acceptance import _raw_values, _context, _inventory_from_profile
from du_export_adapter import build_canonical_site_record, resolve_profile_field_mappings
from sow_normalization import load_canonical_sow_registry

def _build_record(profile, overrides, scope):
    return build_canonical_site_record(_raw_values(profile, overrides), profile, _context(profile), scope=scope, resolved_mappings=resolve_profile_field_mappings(_inventory_from_profile(profile), profile), sow_registry=load_canonical_sow_registry(ROOT / "config/registries/canonical_sow_registry.yaml"))
from du_profile_loader import load_du_profile
from mw_link_scope import classify_link_scope, approved_row, installation_evidence
from canonical_generator_bridge import classify_uat_record
from create_pr import _partition_records

class CombinedLinkTests(unittest.TestCase):
    def source(self, **changes):
        row = {"DU Profile ID": "zte_tx_mini_pr_v1", "Tx SOW": "MW New Link / Reroute",
               "MW Config Antenna Size NE": "1.2m", "MW Config Antenna Size FE": "0.6m",
               "TX SOW Details": "Install new antenna", "BOQ Configuration": "conflicting NLOS"}
        row.update(changes)
        return row

    def test_one_category_needs_no_scope_split_or_boq(self):
        row = self.source()
        self.assertEqual(classify_link_scope(row)["status"], "COMBINED_LINK")
        self.assertFalse(classify_link_scope(row)["include_dismantle"])
        self.assertEqual(approved_row(row)["BOQ Configuration"], "")
        self.assertEqual(installation_evidence(row)["size"], 1.2)

    def test_dismantle_only_when_explicit(self):
        row = self.source(**{"TX SOW Details": "Dismantle existing antenna 0.6m, 2 antennas"})
        self.assertTrue(classify_link_scope(row)["include_dismantle"])
        row["TX SOW Details"] = "Possible dismantle existing antenna"
        self.assertEqual(classify_link_scope(row)["status"], "REVIEW_REQUIRED")

    def test_other_profiles_keep_split(self):
        self.assertEqual(classify_link_scope(self.source(**{"DU Profile ID": "mw_eos_swap_pr_v1"}))["status"], "REVIEW_REQUIRED")

    def record(self, **changes):
        record = date_fixture.TestScopeActualEndEligibility().make_record(actual_end=None)
        record["validation"]["profile_id"] = "zte_tx_mini_pr_v1"
        record["pr_context"].update(changes)
        return record

    def test_date_exempt_but_duplicates_still_block(self):
        record = self.record()
        self.assertEqual(classify_uat_record(record, "TI")[0], "UAT_CANDIDATE")
        record["pr_context"]["existing_ti_pr_status"] = "PR_EXISTS"
        self.assertEqual(classify_uat_record(record, "TI")[0], "DUPLICATE_BLOCKED")
        self.assertEqual(len(_partition_records([record], "TI")["duplicates"]), 1)

    def test_other_sow_date_gate_unchanged(self):
        record = self.record(tx_sow_normalized="MW SWAP")
        self.assertEqual(classify_uat_record(record, "TI")[0], "NO_PR_OR_IGNORED")

    def test_scoped_alias_preserves_raw_and_mappings(self):
        profile = load_du_profile(ROOT / "config/du_profiles/zte_tx_mini_pr_v1.yaml")
        record = _build_record(profile, overrides={"tx_sow_raw": "MW New Link"}, scope="TI")
        self.assertEqual(record["pr_context"]["tx_sow_raw"], "MW New Link")
        self.assertEqual(record["pr_context"]["tx_sow_normalized"], "MW NEW LINK / REROUTE")
        for field in ("tx_sow_details", "antenna_size_ne", "antenna_size_fe"):
            self.assertEqual(record["source_evidence"]["fields"][field]["mapping_status"], "APPROVED")
        tss = _build_record(profile, overrides={"tx_sow_raw": "MW New Link"}, scope="TSS")
        self.assertEqual(tss["pr_context"]["tx_sow_normalized"], "")

if __name__ == "__main__":
    unittest.main()
