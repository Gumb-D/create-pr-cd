import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from backoffice_pr_rules import (
    BACKOFFICE_PBOM_LE_800,
    BACKOFFICE_PBOM_GT_800,
    TX_DEFAULT_WARNING,
    resolve_backoffice_trigger,
    select_backoffice_pbom,
)


class TestBackofficeRules(unittest.TestCase):
    def test_fixed_du_triggers(self):
        expected = {
            '2023 Celcomdigi BAU': ('BAU_2023_CUTOVER', 'microwave_tx_cutover_date'),
            '2024 Celcomdigi BAU': ('BAU_2024_CUTOVER', 'microwave_tx_cutover_date'),
            'Celcomdigi USP': ('USP_CUTOVER', 'microwave_tx_cutover_date'),
            'TX Mini Project': ('TX_MINI_INTEGRATION', 'tx_integrated_actual_end'),
            'Jendela TX Migration': ('JENDELA_CUTOVER', 'cut_over_actual_end'),
            'MW EOS Swap': ('MW_EOS_INTEGRATION', 'site_integrated_actual_end'),
            'ZTE TX MINI': ('ZTE_TX_MINI_INTEGRATION', 'site_integrated_actual_end'),
        }
        for du, pair in expected.items():
            with self.subTest(du=du):
                d = resolve_backoffice_trigger(du, '')
                self.assertEqual('RESOLVED', d.status)
                self.assertEqual(pair, (d.event_code, d.trigger_field))
                self.assertEqual((), d.warning_codes)

    def test_tx_rollout_decom_sows_use_l1(self):
        for sow in ('Decom - Relo','Decom','Decom - Decom + Relo','Decom - Reroute','Decom - Remain','Decom - Decom + Reroute'):
            with self.subTest(sow=sow):
                d = resolve_backoffice_trigger('2023 TX Rollout', sow)
                self.assertEqual(('RESOLVED','TX_ROLLOUT_DECOM','l1_approved_actual_end'), (d.status,d.event_code,d.trigger_field))

    def test_tx_rollout_integration_sows_use_tx_integrated(self):
        for sow in ('MW Re-engineering','MW New Link / Reroute','MW Hardware Upgrade','MW Remote Upgrade','MW Parallel Link','MW Swap','BBU Patching','MW IDU Relocation','MW IDU Patching','IPRAN Port Upgrade'):
            with self.subTest(sow=sow):
                d = resolve_backoffice_trigger('2023 TX Rollout', sow)
                self.assertEqual(('RESOLVED','TX_ROLLOUT_INTEGRATION','tx_integrated_actual_end'), (d.status,d.event_code,d.trigger_field))
                self.assertEqual((), d.warning_codes)

    def test_unknown_tx_rollout_sow_defaults_to_integrated_with_warning(self):
        d = resolve_backoffice_trigger('2023 TX Rollout', 'Future New SOW')
        self.assertEqual(('RESOLVED','TX_ROLLOUT_INTEGRATION','tx_integrated_actual_end'), (d.status,d.event_code,d.trigger_field))
        self.assertEqual((TX_DEFAULT_WARNING,), d.warning_codes)

    def test_cd_consolidation_mocn_and_decom_groups(self):
        for sow in ('Swap','Modernization','Remote MOCN','GF MOCN'):
            with self.subTest(sow=sow):
                d = resolve_backoffice_trigger('CD Consolidation 2023', sow)
                self.assertEqual(('RESOLVED','CD_CONSOLIDATION_MOCN','mocn_actual_end'), (d.status,d.event_code,d.trigger_field))
        for sow in ('MOCN Decomm(Dismantle Passive)','MOCN Decomm','Decomm','Maintain USP MOCN(Dismantle Passive)','Decomm, MOCN By Other Vendor'):
            with self.subTest(sow=sow):
                d = resolve_backoffice_trigger('CD Consolidation 2023', sow)
                self.assertEqual(('RESOLVED','CD_CONSOLIDATION_DECOM','decom_actual_end'), (d.status,d.event_code,d.trigger_field))

    def test_unknown_cd_consolidation_sow_requires_review(self):
        d = resolve_backoffice_trigger('CD Consolidation 2023', 'Future New SOW')
        self.assertEqual('REVIEW_REQUIRED', d.status)
        self.assertEqual('BACKOFFICE_CD_SOW_NOT_APPROVED', d.reason_code)

    def test_unsupported_du_requires_review(self):
        d = resolve_backoffice_trigger('Unknown DU', '')
        self.assertEqual('REVIEW_REQUIRED', d.status)
        self.assertEqual('BACKOFFICE_DU_MODEL_NOT_APPROVED', d.reason_code)

    def test_monthly_pbom_boundary_is_inclusive_at_800(self):
        self.assertEqual(BACKOFFICE_PBOM_LE_800, select_backoffice_pbom(799))
        self.assertEqual(BACKOFFICE_PBOM_LE_800, select_backoffice_pbom(800))
        self.assertEqual(BACKOFFICE_PBOM_GT_800, select_backoffice_pbom(801))
        with self.assertRaises(ValueError):
            select_backoffice_pbom(-1)


if __name__ == '__main__':
    unittest.main()
