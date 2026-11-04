"""Production scope split regression: real model plus classified source evidence."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from mw_link_scope import classify_link_scope, dismantle_evidence, approved_row
from test_ti_business_guidance import row
from test_issue_82_mw_eos_antenna import TestMwSwapGeneratorFallback, SITE_COLUMNS

class ScopeTests(unittest.TestCase):
    def test_combined_label_alone_or_only_new_sizes_is_ambiguous(self):
        for changes in ({}, {'MW Config Antenna Size NE':'0.3m', 'MW Config Antenna Size FE':'0.3m'}, {'TX SOW Details':'MW NEW LINK/REROUTE 0.3M/0.3M'}, {'TX SOW Details':'NLOS'}):
            self.assertEqual(classify_link_scope(row(**{'Tx SOW':'MW New Link / Reroute', **changes}))['status'], 'REVIEW_REQUIRED')

    def test_explicit_scopes_and_conflicts(self):
        for sow in ('MW New Link', 'MW New Link Only'):
            self.assertEqual(classify_link_scope(row(**{'Tx SOW':sow}))['status'], 'NEW_LINK_ONLY')
        self.assertEqual(classify_link_scope(row(**{'Tx SOW':'MW Reroute'}))['status'], 'REROUTE')
        for detail in ('New link only; dismantle old MW antenna 0.6m', 'Possible dismantle old MW antenna', 'Do not dismantle old MW antenna', 'Reroute?', 'No dismantling, remove old antenna 0.6m', 'New link only, dismantle old antenna 0.6m', 'Not new link only'):
            self.assertEqual(classify_link_scope(row(**{'Tx SOW':'MW New Link / Reroute','TX SOW Details':detail}))['status'], 'REVIEW_REQUIRED', detail)
        self.assertEqual(classify_link_scope(row(**{'Tx SOW':'MW New Link / Reroute','TX SOW Details':'New link only; no dismantling'}))['status'], 'NEW_LINK_ONLY')

    def test_unapproved_scope_cannot_select_production_path(self):
        source=row(**{'Tx SOW':'MW New Link / Reroute','Antenna Evidence Governance':'CANONICAL_MAPPING_STATUS','TX Upgrade Scope':'New link only','TX Upgrade Scope Mapping Status':'UNVERIFIED'})
        self.assertEqual(classify_link_scope(source)['status'],'REVIEW_REQUIRED')
        source['TX Upgrade Scope Mapping Status']='APPROVED'
        self.assertEqual(classify_link_scope(source)['status'],'NEW_LINK_ONLY')

    def test_old_size_and_count_are_separate(self):
        source=row(**{'Tx SOW':'MW Reroute','TX SOW Details':'Dismantle existing antenna 0.6m, 2 antennas; install new antenna 1.2m'})
        result=dismantle_evidence(source)
        self.assertEqual((result['size'],result['count'],result['reason']),(0.6,2,None))
        source['TX SOW Details']='Dismantle existing antenna 0.6m'
        self.assertEqual(dismantle_evidence(source)['reason'],'MW_REROUTE_DECOM_ANTENNA_COUNT_UNRESOLVED')

    def test_new_config_nlos_retained_and_cable_are_not_old_diameter(self):
        for detail in ('NLOS', 'Install new antenna 0.3m', 'Retain existing antenna 0.3m', 'Dismantle IF cable 0.3m', 'Dismantle antenna with cable 0.3m'):
            result=dismantle_evidence(row(**{'TX SOW Details':detail,'MW Config Antenna Size NE':'0.3m','MW Config Antenna Size FE':'0.3m'}))
            self.assertIsNotNone(result['reason'],detail)
            self.assertIsNone(result.get('count'))

    def test_one_endpoint_is_not_complete_installation_evidence(self):
        from mw_link_scope import installation_evidence
        source=row(**{'MW Config Antenna Size NE':'0.6m'})
        self.assertIsNone(installation_evidence(source)['size'])

    def test_negated_new_scope_cannot_activate(self):
        source=row(**{'Tx SOW':'MW New Link / Reroute','TX SOW Details':'Do not build new link only'})
        self.assertEqual(classify_link_scope(source)['status'],'REVIEW_REQUIRED')

    def test_unapproved_old_evidence_is_ignored(self):
        source=row(**{'TX SOW Details':'Dismantle existing antenna 0.6m, 2 antennas','Antenna Evidence Governance':'CANONICAL_MAPPING_STATUS','TX SOW Details Mapping Status':'UNVERIFIED'})
        self.assertEqual(dismantle_evidence(source)['reason'],'MW_REROUTE_DECOM_ANTENNA_SIZE_MISSING')
        source['TX SOW Details Mapping Status']='APPROVED'
        self.assertIsNone(dismantle_evidence(source)['reason'])

    def test_conflicting_old_sizes_or_counts_are_reviewed(self):
        for detail in ('Dismantle existing antenna 0.6m, 2 antennas; dismantle existing antenna 1.2m, 2 antennas', 'Dismantle existing antenna 0.6m, 2 antennas; dismantle existing antenna 0.6m, 4 antennas'):
            self.assertIsNotNone(dismantle_evidence(row(**{'TX SOW Details':detail}))['reason'])

class ProductionGeneratorTests(TestMwSwapGeneratorFallback):
    def _write_site_workbook(self,path,rows):
        import pandas as pd
        columns=list(dict.fromkeys([*SITE_COLUMNS, *(k for item in rows for k in item)]))
        with pd.ExcelWriter(path,engine='openpyxl') as writer:
            pd.DataFrame(rows,columns=columns).to_excel(writer,sheet_name='data',index=False,startrow=3)

    def run_case(self,detail='',sow='MW New Link / Reroute',**changes):
        return self._run_generator([row(**{'Tx SOW':sow,'TX SOW Details':detail,**changes})])

    def test_clear_new_link_generates_install_and_inbound_not_dismantling(self):
        result,sites,reviews,diag=self.run_case('New link only; install new antenna 0.6m')
        self.assertEqual(result.returncode,0,diag)
        self.assertIn('GUIDANCE_TEST',sites,diag)
        self.assertFalse(reviews,diag)
        pboms={str(x[9]) for x in diag['generated_rows']}
        self.assertEqual(pboms,{'350001095409','350000212476'},diag)

    def test_explicit_new_link_and_nlos_succeeds_without_old_size(self):
        result,sites,reviews,diag=self.run_case('NLOS',sow='MW New Link')
        self.assertIn('GUIDANCE_TEST',sites,diag)
        self.assertFalse(reviews,diag)

    def test_actual_reroute_with_old_count_generates_both_directions(self):
        result,sites,reviews,diag=self.run_case('Install new antenna 1.2m; dismantle existing antenna 0.6m, 2 antennas')
        self.assertIn('GUIDANCE_TEST',sites,diag)
        self.assertFalse(reviews,diag)
        self.assertEqual({str(x[9]) for x in diag['generated_rows']}, {'350001095410','350000212476','350000236679','350000589315'},diag)

    def test_four_old_antennas_selects_four_not_two(self):
        result,sites,reviews,diag=self.run_case('Install new antenna 0.3m; dismantle existing antenna 0.6m, 4 antennas')
        self.assertIn('GUIDANCE_TEST',sites,diag)
        pboms={str(x[9]) for x in diag['generated_rows']}
        self.assertIn('350000236680',pboms,diag)
        self.assertNotIn('350000236679',pboms,diag)
        self.assertFalse(reviews,diag)

    def test_ambiguous_label_no_partial_ecc(self):
        result,sites,reviews,diag=self.run_case('NLOS')
        self.assertNotIn('GUIDANCE_TEST',sites,diag)
        self.assertTrue(any(r['Reason_Code']=='MW_LINK_SCOPE_UNRESOLVED' for r in reviews),diag)

    def test_missing_old_evidence_no_partial_ecc(self):
        result,sites,reviews,diag=self.run_case('Install new antenna 0.3m',sow='MW Reroute')
        self.assertNotIn('GUIDANCE_TEST',sites,diag)
        self.assertTrue(any(r['Reason_Code']=='MW_REROUTE_DECOM_ANTENNA_SIZE_MISSING' for r in reviews),diag)

    def test_missing_count_no_partial_ecc(self):
        result,sites,reviews,diag=self.run_case('Install new antenna 0.3m; dismantle existing antenna 0.6m')
        self.assertNotIn('GUIDANCE_TEST',sites,diag)
        self.assertTrue(any(r['Reason_Code']=='MW_REROUTE_DECOM_ANTENNA_COUNT_UNRESOLVED' for r in reviews),diag)

    def test_unapproved_install_evidence_cannot_generate(self):
        result,sites,reviews,diag=self.run_case('New link only; install new antenna 0.3m',sow='MW New Link',**{'Antenna Evidence Governance':'CANONICAL_MAPPING_STATUS','TX SOW Details Mapping Status':'UNVERIFIED'})
        self.assertNotIn('GUIDANCE_TEST',sites,diag)
        self.assertTrue(reviews,diag)

    def test_transport_review_also_blocks_entire_site(self):
        result,sites,reviews,diag=self.run_case('New link only; install new antenna 0.3m',**{'Province/State':'','region':'Central'})
        self.assertNotIn('GUIDANCE_TEST',sites,diag)
        self.assertTrue(reviews,diag)

    def test_duplicate_pr_reference_still_blocks(self):
        result,sites,reviews,diag=self.run_case('New link only; install new antenna 0.3m',**{'Subcon PR - TI':'PSQ_EXISTING'})
        self.assertNotIn('GUIDANCE_TEST',sites,diag)

    def test_canonical_scope_provenance_is_forwarded(self):
        import create_pr
        record={'site':{'site_code':'TEST'},'pr_context':{'tx_upgrade_scope_raw':'New link only'},'technical_context':{},'source_evidence':{'fields':{'tx_upgrade_scope_raw':{'mapping_status':'APPROVED'}}}}
        rendered=create_pr._renderer_row(record)
        self.assertEqual(rendered['TX Upgrade Scope Mapping Status'],'APPROVED')
        self.assertIn('TX Upgrade Scope Mapping Status',create_pr.CANONICAL_RENDERER_COLUMNS)

if __name__=='__main__':unittest.main()
