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

    def test_same_run_duplicate_delivery_unit_event_requires_review(self):
        first=rec(du='DU1',site='S1',tx_integrated_actual_end='2026-07-15')
        repeated=rec(du='DU1',site='S2',tx_integrated_actual_end='2026-07-16')
        out=build_backoffice_entitlements([first,repeated],'2026-07',empty_tracker(),REG)
        self.assertEqual(1,len(out['candidates']))
        self.assertEqual(1,len(out['review_required']))
        self.assertEqual('BACKOFFICE_CURRENT_RUN_DUPLICATE_ENTITLEMENT',out['review_required'][0]['pr_generation_decision']['reason_code'])

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

    def test_cd_uses_dedicated_backoffice_sow_not_tx_sow(self):
        r=rec('CD consolidation 2023',sow='Decom',backoffice_sow_raw='Modernization',mocn_actual_end='2026-07-10',decom_actual_end='2026-06-10')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(1,len(out['candidates']))
        self.assertEqual('CD_CONSOLIDATION_MOCN',out['candidates'][0]['backoffice_selection']['event_code'])

    def test_cd_known_mocn_with_blank_selected_trigger_and_current_decom_evidence_requires_review(self):
        r=rec('CD consolidation 2023',backoffice_sow_raw='Modernization',mocn_actual_end='',decom_actual_end='2026-07-18')
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(0,len(out['candidates']))
        self.assertEqual(0,len(out['ignored']))
        self.assertEqual(1,len(out['review_required']))
        self.assertEqual('BACKOFFICE_CD_MILESTONE_CONFLICT',out['review_required'][0]['pr_generation_decision']['reason_code'])

    def test_supplementary_eligible_hops_includes_tracker_blocked_month_entitlements(self):
        duplicate_rows=[]
        duplicate_keys=[]
        for i in range(3):
            row=rec(du=f'OLD{i}',site=f'OLD{i}',tx_integrated_actual_end='2026-07-15')
            duplicate_rows.append(row)
            duplicate_keys.append((f'OLD{i}','TX_MINI_INTEGRATION'))
        new_rows=[rec(du='NEW1',site='NEW1',tx_integrated_actual_end='2026-07-16'),rec(du='NEW2',site='NEW2',tx_integrated_actual_end='2026-07-17')]
        out=build_backoffice_entitlements(duplicate_rows+new_rows,'2026-07',empty_tracker({'2026-07':PBOM_LOW},keys=duplicate_keys),REG)
        self.assertEqual('SUPPLEMENTARY',out['summary']['issue_type'])
        self.assertEqual(3,len(out['duplicates']))
        self.assertEqual(2,len(out['candidates']))
        self.assertEqual(5,out['summary']['eligible_hops'])
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

    def test_cd_unknown_sow_with_only_historical_milestones_is_ignored_not_reviewed(self):
        r=rec('CD consolidation 2023',sow='',mocn_actual_end='2024-05-10',decom_actual_end='2025-02-11')
        r['pr_context']['backoffice_sow_raw']=''
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(0,len(out['review_required']))
        self.assertEqual(1,len(out['ignored']))
        self.assertEqual('BACKOFFICE_OUTSIDE_BILLING_MONTH',out['ignored'][0]['pr_generation_decision']['reason_code'])

    def test_cd_unknown_sow_with_no_completed_milestone_is_not_yet_eligible(self):
        r=rec('CD consolidation 2023',sow='')
        r['pr_context']['backoffice_sow_raw']=''
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(0,len(out['review_required']))
        self.assertEqual(1,len(out['ignored']))
        self.assertEqual('NOT_YET_ELIGIBLE',out['ignored'][0]['pr_generation_decision']['reason_code'])

    def test_cd_unknown_sow_with_possible_current_month_milestone_requires_review(self):
        r=rec('CD consolidation 2023',sow='',mocn_actual_end='2026-07-10',decom_actual_end='2025-02-11')
        r['pr_context']['backoffice_sow_raw']=''
        out=build_backoffice_entitlements([r],'2026-07',empty_tracker(),REG)
        self.assertEqual(1,len(out['review_required']))
        self.assertEqual('BACKOFFICE_CD_SOW_NOT_APPROVED',out['review_required'][0]['pr_generation_decision']['reason_code'])

    def test_all_eleven_governed_event_paths_resolve_to_current_month_candidates(self):
        cases = [
            (rec('2023 Celcomdigi BAU',du='D1',site='S1',microwave_tx_cutover_date='2026-07-01'), 'BAU_2023_CUTOVER'),
            (rec('2024 Celcomdigi BAU',du='D2',site='S2',microwave_tx_cutover_date='2026-07-02'), 'BAU_2024_CUTOVER'),
            (rec('Celcomdigi USP',du='D3',site='S3',microwave_tx_cutover_date='2026-07-03'), 'USP_CUTOVER'),
            (rec('TX Mini Project',du='D4',site='S4',tx_integrated_actual_end='2026-07-04'), 'TX_MINI_INTEGRATION'),
            (rec('Jendela TX Migration',du='D5',site='S5',cut_over_actual_end='2026-07-05'), 'JENDELA_CUTOVER'),
            (rec('MW EOS Swap',du='D6',site='S6',site_integrated_actual_end='2026-07-06'), 'MW_EOS_INTEGRATION'),
            (rec('ZTE TX MINI',du='D7',site='S7',site_integrated_actual_end='2026-07-07'), 'ZTE_TX_MINI_INTEGRATION'),
            (rec('2023 TX Rollout',du='D8',site='S8',sow='MW Swap',tx_integrated_actual_end='2026-07-08'), 'TX_ROLLOUT_INTEGRATION'),
            (rec('2023 TX Rollout',du='D9',site='S9',sow='Decom',l1_approved_actual_end='2026-07-09'), 'TX_ROLLOUT_DECOM'),
            (rec('CD consolidation 2023',du='D10',site='S10',backoffice_sow_raw='Modernization',mocn_actual_end='2026-07-10'), 'CD_CONSOLIDATION_MOCN'),
            (rec('CD consolidation 2023',du='D11',site='S11',backoffice_sow_raw='Decomm',decom_actual_end='2026-07-11'), 'CD_CONSOLIDATION_DECOM'),
        ]
        out=build_backoffice_entitlements([row for row,_ in cases],'2026-07',empty_tracker(),REG)
        self.assertEqual(11,len(out['candidates']))
        self.assertEqual(
            [event for _,event in cases],
            [row['backoffice_selection']['event_code'] for row in out['candidates']],
        )

if __name__=='__main__': unittest.main()
