import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import date
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import create_pr
from backoffice_tracker import TrackerIndex, load_backoffice_tracker

LOW='350000592793'

def tracker(month_pbom=None):
    return TrackerIndex(frozenset(),{},month_pbom or {})

class TestBackofficeEntrypoint(unittest.TestCase):
    def test_parser_accepts_backoffice_tracker_and_billing_month(self):
        argv=['create_pr.py','--site-data','input','--output','out','--scope','BACKOFFICE','--all-sites','--backoffice-tracker','tracker.xls','--billing-month','2026-07']
        with patch.object(sys,'argv',argv): args=create_pr.parse_args()
        self.assertEqual('BACKOFFICE',args.scope)
        self.assertEqual(Path('tracker.xls'),args.backoffice_tracker)
        self.assertEqual('2026-07',args.billing_month)

    def test_main_requires_previous_closed_month(self):
        create_pr._validate_backoffice_cadence('2026-07',tracker(),date(2026,8,13))
        with self.assertRaises(create_pr.CreatePrError) as cm:
            create_pr._validate_backoffice_cadence('2026-06',tracker(),date(2026,8,13))
        self.assertEqual('BACKOFFICE_MAIN_BILLING_MONTH_NOT_PREVIOUS',cm.exception.code)

    def test_supplementary_allows_older_closed_frozen_month(self):
        create_pr._validate_backoffice_cadence('2026-05',tracker({'2026-05':LOW}),date(2026,8,13))

    def test_current_month_is_never_production_eligible(self):
        with self.assertRaises(create_pr.CreatePrError) as cm:
            create_pr._validate_backoffice_cadence('2026-08',tracker({'2026-08':LOW}),date(2026,8,13))
        self.assertEqual('BACKOFFICE_BILLING_MONTH_NOT_CLOSED',cm.exception.code)

    def test_main_requires_directory_to_prove_cross_du_aggregation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.xlsx'; p.write_bytes(b'x')
            with self.assertRaises(create_pr.CreatePrError) as cm:
                create_pr._backoffice_source_files(p,issue_type='MAIN')
            self.assertEqual('BACKOFFICE_MAIN_REQUIRES_SOURCE_DIRECTORY',cm.exception.code)

    def test_source_directory_collects_supported_exports_and_ignores_temp_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ['a.xlsx','b.xlsm','c.csv','~$lock.xlsx','tracker.xls','note.txt']:
                (root/name).write_bytes(b'x')
            files=create_pr._backoffice_source_files(root,issue_type='MAIN')
            self.assertEqual(['a.xlsx','b.xlsm','c.csv'],[p.name for p in files])

    def test_supplementary_can_use_single_export_because_tier_is_frozen(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.xlsx'; p.write_bytes(b'x')
            self.assertEqual([p],create_pr._backoffice_source_files(p,issue_type='SUPPLEMENTARY'))

    def test_tracker_loader_convenience_builds_snapshot(self):
        rows=[{'Delivery Unit Code':'DU1','SOW':'TX Mini Project','PBOM Code':LOW,'File Name':'TX Outsource-Allstar PR CD 20240815 Batch 1'}]
        with patch('backoffice_tracker.read_tracker_rows',return_value=rows):
            snap=load_backoffice_tracker(Path('tracker.xls'))
        self.assertIn(('DU1','TX_MINI_INTEGRATION'),snap.duplicate_keys)

    def test_multi_export_canonicalization_accepts_backoffice_production_scope_even_if_overall_profile_is_draft(self):
        sources=[Path('a.xlsx'),Path('b.xlsx')]
        resolution={
            'profile':{'status':'DRAFT','scope_status':{'BACKOFFICE':'PRODUCTION'}},
            'inventory':{'x':1},'header_hash':'h'
        }
        with patch.object(create_pr,'resolve_du_profile',return_value=resolution) as resolver, patch.object(create_pr,'build_canonical_records',side_effect=[([{'site':{'site_code':'A'}}],{'profile_id':'p1'}),([{'site':{'site_code':'B'}}],{'profile_id':'p2'})]) as builder:
            records, metadata=create_pr._canonicalize_backoffice_sources(sources)
        self.assertEqual(['A','B'],[r['site']['site_code'] for r in records])
        self.assertEqual(['p1','p2'],[m['profile_id'] for m in metadata])
        self.assertEqual(2,resolver.call_count)
        self.assertEqual(2,builder.call_count)

    def test_multi_export_canonicalization_blocks_nonproduction_backoffice_scope(self):
        resolution={'profile':{'status':'PRODUCTION','scope_status':{'BACKOFFICE':'DRAFT'}},'inventory':{},'header_hash':'h'}
        with patch.object(create_pr,'resolve_du_profile',return_value=resolution):
            with self.assertRaises(create_pr.CreatePrError) as cm:
                create_pr._canonicalize_backoffice_sources([Path('a.xlsx')])
        self.assertEqual('BACKOFFICE_PROFILE_SCOPE_NOT_PRODUCTION',cm.exception.code)

    def test_run_routes_backoffice_to_dedicated_orchestrator(self):
        parsed=Namespace(scope='BACKOFFICE',pr_model=Path('Info/input/pr_model.xlsx'))
        baseline={'path':Path('Info/input/pr_model.xlsx'),'baseline_id':'x','version':'4.1','actual_sha256':'abc'}
        expected={'status':'SUCCESS'}
        with patch.object(create_pr,'validate_pr_model_baseline',return_value=baseline), patch.object(create_pr,'_run_backoffice',return_value=expected) as runner:
            self.assertIs(expected,create_pr.run(parsed))
        runner.assert_called_once()

    def test_backoffice_does_not_reject_same_site_when_delivery_unit_event_identity_differs(self):
        records=[
            {'site':{'site_code':'SAME','du_key':'DU1'},'identity':{'project_key':'P'}},
            {'site':{'site_code':'SAME','du_key':'DU2'},'identity':{'project_key':'P'}},
        ]
        create_pr._validate_backoffice_source_identity(records)

    def test_backoffice_renderer_row_carries_runtime_selection(self):
        record={'site':{'site_code':'S1','site_name':'Site 1','du_key':'DU1'},'pr_context':{'region':'Central'},'backoffice_selection':{'event_code':'TX_MINI_INTEGRATION','trigger_date':'2026-07-15','billing_month':'2026-07','pbom_code':LOW,'unit':'Hop','quantity':1,'subcontractor':'Allstar','contract_number':'S1MY2024042501WBF1','issue_type':'MAIN','warnings':['W']}}
        row=create_pr._renderer_row(record)
        self.assertEqual('TX_MINI_INTEGRATION',row['Backoffice Event Code'])
        self.assertEqual(LOW,row['Backoffice PBOM Code'])
        self.assertEqual('W',row['Backoffice Warnings'])

if __name__=='__main__': unittest.main()
