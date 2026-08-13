import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from backoffice_tracker import TrackerIndex
from backoffice_pr_runtime import build_backoffice_entitlements, load_service_registry

PBOM_LOW='350000592793'
PBOM_HIGH='350000592794'

def rec(du_model='TX Mini Project', du='DU1', site='S1', sow='', **ctx):
    base={
        'identity':{'du_model_name':du_model,'source_row_number':2},
        'site':{'site_code':site,'du_key':du},
        'pr_context':{'delivery_unit_code':du,'tx_sow_raw':sow},
        'validation':{'pr_input_classification':'PR_INPUT_READY','profile_id':'x'},
    }
    base['pr_context'].update(ctx)
    return base

def empty_tracker(month_pbom=None, keys=()):
    return TrackerIndex(frozenset(keys),{},month_pbom or {})

REG={
 'services':[{
   'effective_from':'2024-04-25','effective_to':None,
   'subcontractor':'Allstar','contract_number':'S1MY2024042501WBF1'
 }]
}

class TestBackofficeRuntime(unittest.TestCase):
    def test_blank_trigger_is_not_yet_eligible(self):
        r=rec(tx_integrated_actual_end='')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(0,len(out['candidates']))
        self.assertEqual('NOT_YET_ELIGIBLE',out['ignored'][0]['pr_generation_decision']['reason_code'])

    def test_wrong_month_trigger_is_not_in_requested_closed_month(self):
        r=rec(tx_integrated_actual_end='2026-06-30')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual('BACKOFFICE_OUTSIDE_BILLING_MONTH',out['ignored'][0]['pr_generation_decision']['reason_code'])

    def test_duplicate_is_blocked_by_delivery_unit_plus_event(self):
        r=rec(tx_integrated_actual_end='2026-07-15')
        key=('DU1','TX_MINI_INTEGRATION')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(keys=(key,)),REG)
        self.assertEqual('DUPLICATE_BLOCKED',out['duplicates'][0]['pr_generation_decision']['classification'])

    def test_main_month_800_uses_low_pbom(self):
        rows=[rec(du=f'DU{i}',site=f'S{i}',tx_integrated_actual_end='2026-07-15') for i in range(800)]
        out=build_backoffice_entitlements(rows,'2026-07',empty_tracker(),REG)
        self.assertEqual(PBOM_LOW,out['summary']['pbom_code'])
        self.assertEqual(800,out['summary']['eligible_hops'])
        self.assertEqual('MAIN',out['summary']['issue_type'])
        self.assertTrue(all(x['backoffice_selection']['pbom_code']==PBOM_LOW for x in out['candidates']))

    def test_main_month_801_uses_high_pbom(self):
        rows=[rec(du=f'DU{i}',site=f'S{i}',tx_integrated_actual_end='2026-07-15') for i in range(801)]
        out=build_backoffice_entitlements(rows,'2026-07',empty_tracker(),REG)
        self.assertEqual(PBOM_HIGH,out['summary']['pbom_code'])

    def test_supplementary_reuses_frozen_main_pbom(self):
        rows=[rec(du=f'N{i}',site=f'N{i}',tx_integrated_actual_end='2026-07-15') for i in range(30)]
        out=build_backoffice_entitlements(rows,'2026-07',empty_tracker({'2026-07':PBOM_LOW}),REG)
        self.assertEqual('SUPPLEMENTARY',out['summary']['issue_type'])
        self.assertEqual(PBOM_LOW,out['summary']['pbom_code'])

    def test_tx_l1_missing_falls_back_to_integrated_with_warning(self):
        r=rec('2023 TX Rollout',sow='Decom',l1_approved_actual_end='',tx_integrated_actual_end='2026-07-20')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        sel=out['candidates'][0]['backoffice_selection']
        self.assertEqual('TX_ROLLOUT_INTEGRATION',sel['event_code'])
        self.assertIn('BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED',sel['warnings'])

    def test_invalid_trigger_date_requires_review(self):
        r=rec(tx_integrated_actual_end='not-a-date')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual('BACKOFFICE_TRIGGER_DATE_INVALID',out['review_required'][0]['pr_generation_decision']['reason_code'])

    def test_missing_delivery_unit_requires_review(self):
        r=rec(du='',tx_integrated_actual_end='2026-07-15')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual('BACKOFFICE_DELIVERY_UNIT_CODE_MISSING',out['review_required'][0]['pr_generation_decision']['reason_code'])

    def test_effective_dated_provider_and_contract_are_attached(self):
        r=rec(tx_integrated_actual_end='2026-07-15')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        sel=out['candidates'][0]['backoffice_selection']
        self.assertEqual('Allstar',sel['subcontractor'])
        self.assertEqual('S1MY2024042501WBF1',sel['contract_number'])
        self.assertEqual('Hop',sel['unit'])
        self.assertEqual(1,sel['quantity'])

    def test_no_effective_contract_requires_review(self):
        r=rec(tx_integrated_actual_end='2023-01-15')
        out=build_backoffice_entitlements([r],'2023-01',empty_tracker(),REG)
        self.assertEqual('BACKOFFICE_SERVICE_CONTRACT_NOT_EFFECTIVE',out['review_required'][0]['pr_generation_decision']['reason_code'])

    def test_registry_file_loads_current_backoffice_service(self):
        reg=load_service_registry(Path('config/backoffice_service_registry.yaml'))
        self.assertTrue(any(x['subcontractor']=='Allstar' and x['contract_number']=='S1MY2024042501WBF1' for x in reg['services']))

if __name__=='__main__': unittest.main()
