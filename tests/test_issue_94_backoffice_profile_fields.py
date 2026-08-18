import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical_site_validator import SCOPE_REQUIRED_FIELDS, FIELD_PATHS
from canonical_input_pipeline import _required_fields_for_scope

PROFILES=ROOT/'config'/'du_profiles'
EXPECTED={
'celcomdigi_bau_2023_pr_v1':('microwave_tx_cutover_date','docata|ZDCSZ00885808','Microwave','TX Cutover Date'),
'celcomdigi_bau_2024_pr_v1':('microwave_tx_cutover_date','docata|ZDCSZ00885808','Microwave','TX Cutover Date'),
'celcomdigi_usp_pr_v1':('microwave_tx_cutover_date','docata|ZDCSZ00885808','Microwave','TX Cutover Date'),
'tx_mini_pr_v1':('tx_integrated_actual_end','WP11400|AC0000111569|actual_end_date','TX Integrated','actual end time'),
'jendela_tx_migration_pr_v1':('cut_over_actual_end','WP11401|AC0000156514|actual_end_date','Cut Over','actual end time'),
'mw_eos_swap_pr_v1':('site_integrated_actual_end','WP11400|AC0000145873|actual_end_date','Site Integrated','actual end time'),
'zte_tx_mini_pr_v1':('site_integrated_actual_end','WP11400|AC0000197593|actual_end_date','Site Integrated','actual end time'),
}


def load(pid):
    return json.loads((PROFILES/f'{pid}.yaml').read_text(encoding='utf-8'))


class TestBackofficeProfileFields(unittest.TestCase):
    def test_backoffice_base_scope_is_canonical(self):
        self.assertEqual(('site_code','site_name','du_key','region'), SCOPE_REQUIRED_FIELDS['BACKOFFICE'])
        for name in ('du_key','backoffice_sow_raw','microwave_tx_cutover_date','tx_integrated_actual_end','cut_over_actual_end','site_integrated_actual_end','l1_approved_actual_end','mocn_actual_end','decom_actual_end'):
            self.assertIn(name,FIELD_PATHS)

    def test_backoffice_renderer_identity_fields_are_scope_required_and_approved(self):
        self.assertEqual(('site_code','site_name','du_key','region'), SCOPE_REQUIRED_FIELDS['BACKOFFICE'])
        for path in sorted(PROFILES.glob('*.yaml')):
            p=json.loads(path.read_text(encoding='utf-8'))
            if p.get('scope_status',{}).get('BACKOFFICE')!='PRODUCTION':
                continue
            with self.subTest(profile=path.stem):
                required=_required_fields_for_scope(p,'BACKOFFICE')
                self.assertIn('site_name',required)
                self.assertIn('region',required)
                scoped=p.get('scope_mapping_status',{}).get('BACKOFFICE',{})
                site_name_status=scoped.get('site_name') or p['field_mapping']['site_name']['source_candidates'][0]['mapping_status']
                region_status=scoped.get('region') or p['field_mapping']['region']['source_candidates'][0]['mapping_status']
                self.assertEqual('APPROVED',site_name_status)
                self.assertEqual('APPROVED',region_status)
    def test_fixed_trigger_profiles_have_approved_real_fingerprints(self):
        for pid,(field,code,task,header) in EXPECTED.items():
            with self.subTest(profile=pid):
                p=load(pid)
                self.assertEqual('PRODUCTION',p['scope_status']['BACKOFFICE'])
                self.assertEqual(['du_key',field],p['scope_required_fields']['BACKOFFICE'])
                m=p['field_mapping'][field]
                self.assertEqual('APPROVED',m['source_candidates'][0]['mapping_status'])
                fp=m['source_candidates'][0]['fingerprint']
                self.assertEqual((code,task,header),(fp['field_code'],fp['task_name'],fp['display_header']))
                d=p['field_mapping']['du_key']['source_candidates'][0]
                self.assertEqual('du|du_code',d['fingerprint']['field_code'])
                self.assertEqual('APPROVED', p['scope_mapping_status']['BACKOFFICE']['du_key'])
                self.assertNotIn('delivery_unit_code', p['field_mapping'])

    def test_tx_rollout_maps_both_governed_milestones(self):
        p=load('tx_rollout_2023_pr_v1')
        self.assertEqual(['du_key','tx_sow_raw','tx_integrated_actual_end','l1_approved_actual_end'],p['scope_required_fields']['BACKOFFICE'])
        expected={
            'tx_integrated_actual_end':('WP11400|AC0000079301|actual_end_date','Software Commissioning','TX Integrated','actual end time'),
            'l1_approved_actual_end':('WPC000011222|AC0000079322|actual_end_date','Q&EHS','L1 Approved','actual end time'),
        }
        for field,want in expected.items():
            fp=p['field_mapping'][field]['source_candidates'][0]['fingerprint']
            self.assertEqual(want,(fp['field_code'],fp['wbs_stage'],fp['task_name'],fp['display_header']))

    def test_cd_consolidation_maps_mocn_and_decom(self):
        p=load('celcomdigi_cd_consolidation_2023_pr_v1')
        self.assertEqual('PRODUCTION',p['scope_status']['BACKOFFICE'])
        self.assertEqual(['du_key','backoffice_sow_raw','mocn_actual_end','decom_actual_end'],p['scope_required_fields']['BACKOFFICE'])
        site=next(c for c in p['field_mapping']['site_code']['source_candidates'] if c['fingerprint']['field_code']=='site|fix00012|8359047522524182050|8359047522524230651')
        self.assertEqual('UNVERIFIED',site['mapping_status'])
        tx=next(c for c in p['field_mapping']['backoffice_sow_raw']['source_candidates'] if c['fingerprint']['wbs_stage']=='Installation' and c['fingerprint']['task_name']=='Wireless RAN')
        self.assertEqual('UNVERIFIED',tx['mapping_status'])
        self.assertEqual(('docata|ZDCSZ631062','Installation','Wireless RAN','SOW'),(tx['fingerprint']['field_code'],tx['fingerprint']['wbs_stage'],tx['fingerprint']['task_name'],tx['fingerprint']['display_header']))
        expected={
            'mocn_actual_end':('WPC000011434|AC0000084313|actual_end_date','MOCN Consolidation','CD consolidation (CD MOCN)','actual end time'),
            'decom_actual_end':('WPC000011433|AC0000084312|actual_end_date','Site DECOMM','Decomm','actual end time'),
        }
        scoped=p['scope_mapping_status']['BACKOFFICE']
        for field in ('site_code','site_name','du_key','region','backoffice_sow_raw','mocn_actual_end','decom_actual_end'):
            self.assertEqual('APPROVED',scoped[field])
        for field,want in expected.items():
            mapping=p['field_mapping'][field]['source_candidates'][0]
            self.assertEqual('UNVERIFIED',mapping['mapping_status'])
            fp=mapping['fingerprint']
            self.assertEqual(want,(fp['field_code'],fp['wbs_stage'],fp['task_name'],fp['display_header']))

    def test_pipeline_uses_scope_specific_required_fields(self):
        p=load('tx_rollout_2023_pr_v1')
        self.assertEqual({'site_code','site_name','du_key','region','tx_sow_raw','tx_integrated_actual_end','l1_approved_actual_end'},_required_fields_for_scope(p,'BACKOFFICE'))

if __name__=='__main__': unittest.main()
