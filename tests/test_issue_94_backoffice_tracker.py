import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from backoffice_tracker import canonical_event_from_tracker_sow, duplicate_key, billing_month_from_filename, build_tracker_index, frozen_pbom_for_month, read_tracker_rows, BackofficeTrackerError

class TestBackofficeTracker(unittest.TestCase):
    def test_historical_sow_maps_to_canonical_event(self):
        cases={
            'CD consolidation 2023-MOCN':'CD_CONSOLIDATION_MOCN',
            'CD consolidation 2023-Decom':'CD_CONSOLIDATION_DECOM',
            '2023 TX Rollout':'TX_ROLLOUT_INTEGRATION',
            '2023 TX Rollout-Decom':'TX_ROLLOUT_DECOM',
            'TX Mini Project':'TX_MINI_INTEGRATION',
            '2023 Celcomdigi BAU':'BAU_2023_CUTOVER',
            '2024 Celcomdigi BAU':'BAU_2024_CUTOVER',
            'Celcomdigi USP':'USP_CUTOVER',
            'Jendela TX Migration':'JENDELA_CUTOVER',
            'MW EOS Swap':'MW_EOS_INTEGRATION',
            'ZTE TX MINI':'ZTE_TX_MINI_INTEGRATION',
        }
        for sow,event in cases.items(): self.assertEqual(event,canonical_event_from_tracker_sow(sow))
        self.assertIsNone(canonical_event_from_tracker_sow('Unknown Future SOW'))

    def test_duplicate_identity_is_du_plus_event_only(self):
        self.assertEqual(('DU0001','TX_ROLLOUT_DECOM'),duplicate_key(' du0001 ','TX_ROLLOUT_DECOM'))

    def test_filename_issue_date_maps_to_previous_closed_month(self):
        self.assertEqual('2024-07',billing_month_from_filename('TX Outsource-Allstar PR CD 20240815 Batch 1'))
        self.assertEqual('2026-04',billing_month_from_filename('TX Outsource-Allstar PR CD 20260505 Batch 1'))
        self.assertIsNone(billing_month_from_filename('No Date'))

    def test_index_blocks_duplicate_and_freezes_month_pbom_from_earliest_issue(self):
        rows=[
            {'Delivery Unit Code':'DU1','SOW':'2023 TX Rollout','PBOM Code':'350000592793','File Name':'TX Outsource-Allstar PR CD 20240815 Batch 1'},
            {'Delivery Unit Code':'DU2','SOW':'TX Mini Project','PBOM Code':'350000592793','File Name':'TX Outsource-Allstar PR CD 20240820 Supplementary 1'},
            {'Delivery Unit Code':'DU3','SOW':'MW EOS Swap','PBOM Code':'350000592794','File Name':'TX Outsource-Allstar PR CD 20240904 Batch 1'},
        ]
        idx=build_tracker_index(rows)
        self.assertIn(('DU1','TX_ROLLOUT_INTEGRATION'),idx.duplicate_keys)
        self.assertEqual('350000592793',frozen_pbom_for_month(idx,'2024-07'))
        self.assertEqual('350000592794',frozen_pbom_for_month(idx,'2024-08'))

    def test_xls_reader_uses_outsource_sheet_and_xlrd(self):
        fake=[{'Delivery Unit Code':'DU1','SOW':'TX Mini Project','PBOM Code':'350000592793','File Name':'TX Outsource-Allstar PR CD 20240815 Batch 1'}]
        with patch('backoffice_tracker.pd.read_excel', return_value=__import__('pandas').DataFrame(fake)) as read:
            rows=read_tracker_rows(Path('tracker.xls'))
        self.assertEqual(fake,rows)
        read.assert_called_once_with(Path('tracker.xls'),sheet_name='TX Outsource Details',engine='xlrd',dtype=object)

    def test_reader_fails_closed_when_required_columns_missing(self):
        with patch('backoffice_tracker.pd.read_excel', return_value=__import__('pandas').DataFrame([{'SOW':'TX Mini Project'}])):
            with self.assertRaises(BackofficeTrackerError) as cm: read_tracker_rows(Path('tracker.xls'))
        self.assertEqual('BACKOFFICE_TRACKER_REQUIRED_COLUMNS_MISSING',cm.exception.code)

    def test_ambiguous_duplicate_identity_fails_closed(self):
        rows=[
            {'Delivery Unit Code':'DU1','SOW':'2023 TX Rollout','PBOM Code':'350000592793','File Name':'TX Outsource-Allstar PR CD 20240815 Batch 1'},
            {'Delivery Unit Code':'DU1','SOW':'2023 TX Rollout','PBOM Code':'350000592794','File Name':'TX Outsource-Allstar PR CD 20240904 Batch 1'},
        ]
        with self.assertRaises(BackofficeTrackerError): build_tracker_index(rows)

if __name__=='__main__': unittest.main()
