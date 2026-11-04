"""Business guidance regressions: scoped PostMOCN, Starlink, and NLOS rules."""
from pathlib import Path
import ast
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from antenna_evidence_resolver import resolve_installation_antenna_evidence, resolve_nlos_standard
from pr_helpers import normalize_postmocn_site_id, is_starlink_only_work_item, load_pr_model_items
import create_pr
from test_issue_82_mw_eos_antenna import TestMwSwapGeneratorFallback, SITE_COLUMNS


def row(**changes):
    result = {
        'customer site code': 'GUIDANCE_TEST', 'customer site name': 'Guidance regression',
        'du code': 'DU_GUIDANCE', 'region': 'Sabah', 'Province/State': 'Sabah',
        'Latitude (North Plus South Minus)': 4.414137,
        'Longitude (East Plus West Minus)': 118.522111,
        'TX Upgrade Scope': 'TSS+AA+TI', 'Tx SOW': 'MW SWAP',
        'MW Config Antenna Size NE': '', 'MW Config Antenna Size FE': '',
        'SubCon - TI Team': 'Seri Pancar', 'Subcon PR - TI': '',
        'BOQ Configuration': '', 'TX SOW Details': '', 'NE SOW Details': '', 'FE SOW Details': '',
    }
    result.update(changes)
    return result


class PostMocnTests(unittest.TestCase):
    def test_approved_spelling_aliases_keep_instance(self):
        for source in ('S1_POSTMOCN1', 'S1_Post MOCN1', 'S1_POST-MOCN_1', 'S1-Post_MOCN1'):
            with self.subTest(source=source):
                self.assertEqual(normalize_postmocn_site_id(source), 'S1_POSTMOCN1')
        self.assertEqual(normalize_postmocn_site_id('S1_postmocn'), 'S1_POSTMOCN')
        self.assertNotEqual(normalize_postmocn_site_id('S1_POSTMOCN1'), normalize_postmocn_site_id('S1_POSTMOCN2'))

    def test_unknown_lookalikes_and_other_suffixes_unchanged(self):
        for source in ('S1_POSTMOCNX', 'S1_POSTMOCN_ABC', 'POSTMOCN', 'S1_AD', 'S1_POSTMOCN1_EXTRA'):
            self.assertEqual(normalize_postmocn_site_id(source), source)

    def test_idempotent(self):
        value = normalize_postmocn_site_id('S1_Post MOCN_2')
        self.assertEqual(normalize_postmocn_site_id(value), value)

    def test_renderer_preserves_source_and_sow(self):
        record = {'identity': {'source_row_number': 5}, 'site': {'site_code': 'S1_Post MOCN_2'},
                  'pr_context': {'tx_sow_normalized': 'MW SWAP'}, 'technical_context': {}}
        rendered = create_pr._renderer_row(record)
        self.assertEqual(record['site']['site_code'], 'S1_Post MOCN_2')
        self.assertEqual(rendered['customer site code'], 'S1_POSTMOCN2')
        self.assertEqual(rendered['Tx SOW'], 'MW SWAP')

    def test_colliding_source_ids_fail_closed(self):
        records = [{'site': {'site_code': code}, 'identity': {'project_key': 'P'}}
                   for code in ('S1_POSTMOCN1', 'S1_Post MOCN_1')]
        with self.assertRaises(create_pr.CreatePrError) as caught:
            create_pr._partition_records(records, 'TI')
        self.assertEqual(caught.exception.code, 'RENDERED_SITE_ID_COLLISION')


class NlosTests(unittest.TestCase):
    def test_each_governed_source_resolves_standard(self):
        for field in ('BOQ Configuration', 'TX SOW Details'):
            result = resolve_installation_antenna_evidence(row(**{field: 'NLOS'}))
            self.assertEqual(result['status'], 'RESOLVED_COMMON')
            self.assertEqual(result['selected_size'], 0.3)
            self.assertEqual(result['evidence'][0]['source'], field)
            self.assertEqual(result['reason_code'], 'NLOS_STANDARD_0_3M')

    def test_label_colon_is_not_uncertainty(self):
        result = resolve_installation_antenna_evidence(row(**{'TX SOW Details': 'NLOS: install new link'}))
        self.assertEqual(result['selected_size'], 0.3)

    def test_explicit_same_size_is_compatible(self):
        result = resolve_installation_antenna_evidence(row(**{
            'TX SOW Details': 'NLOS; install antenna 0.3m with no dismantle', 'MW Config Antenna Size NE': '0.3m'}))
        self.assertEqual(result['selected_size'], 0.3)

    def test_conflicting_or_invalid_evidence_is_not_overwritten(self):
        for changes in (
            {'MW Config Antenna Size NE': '0.6m'},
            {'MW Config Antenna Size FE': 'unsupported'},
            {'TX SOW Details': 'NLOS; install antenna 1.2m'},
            {'NE SOW Details': 'Dismantle antenna 0.6m'},
            {'BOQ Configuration': 'NLOS / LOS'},
        ):
            result = resolve_installation_antenna_evidence(row(**{'BOQ Configuration': 'NLOS', **changes}))
            self.assertEqual(result['status'], 'CONFLICT', changes)
            self.assertIsNone(result['selected_size'])
            self.assertEqual(result['reason_code'], 'NLOS_ANTENNA_EVIDENCE_CONFLICT')

    def test_negated_uncertain_and_unrelated_labels_do_not_default(self):
        for text in ('not NLOS', 'NLOS?', 'possible NLOS', 'NLOS not required', 'if NLOS', 'previous NLOS', 'not an NLOS', 'non-NLOS', 'not-NLOS'):
            result = resolve_installation_antenna_evidence(row(**{'TX SOW Details': text}))
            self.assertEqual(result['status'], 'CONFLICT', text)
        for text in ('', 'XNLOS', 'NLOS2', 'LOS', 'IF cable 0.3m'):
            result = resolve_installation_antenna_evidence(row(**{'TX SOW Details': text}))
            self.assertIsNone(result['selected_size'], text)
        self.assertIsNone(resolve_nlos_standard(row(**{'customer site code': 'NLOS_SITE'})))

    def test_unapproved_canonical_evidence_cannot_activate_rule(self):
        for status in ('UNVERIFIED', 'MISSING', ''):
            source = row(**{'TX SOW Details': 'NLOS',
                            'Antenna Evidence Governance': 'CANONICAL_MAPPING_STATUS',
                            'TX SOW Details Mapping Status': status})
            self.assertEqual(resolve_installation_antenna_evidence(source)['status'], 'MISSING')
        source['TX SOW Details Mapping Status'] = 'APPROVED'
        self.assertEqual(resolve_installation_antenna_evidence(source)['selected_size'], 0.3)

    def test_tx_rollout_uses_only_existing_approved_detail_fingerprints(self):
        import json
        profile = json.loads((ROOT / 'config/du_profiles/tx_rollout_2023_pr_v1.yaml').read_text(encoding='utf-8'))
        fields = profile['field_mapping']
        self.assertEqual(fields['antenna_size_ne']['source_candidates'], [])
        self.assertEqual(fields['boq_configuration']['source_candidates'], [])
        for field in ('tx_sow_details', 'ne_sow_details', 'fe_sow_details'):
            self.assertEqual(fields[field]['source_candidates'][0]['mapping_status'], 'APPROVED')
        record = {'site': {'site_code': 'S1'}, 'pr_context': {'tx_sow_normalized': 'MW NEW LINK / REROUTE'},
                  'technical_context': {'tx_sow_details': 'NLOS'},
                  'source_evidence': {'fields': {'tx_sow_details': {'mapping_status': 'APPROVED'}}},
                  'validation': {'profile_id': 'tx_rollout_2023_pr_v1'}}
        self.assertEqual(resolve_nlos_standard(create_pr._renderer_row(record))['selected_size'], 0.3)

    def test_boq_approval_is_forwarded_by_renderer(self):
        record = {'site': {'site_code': 'S1'}, 'pr_context': {},
                  'technical_context': {'boq_configuration': 'NLOS'},
                  'source_evidence': {'fields': {'boq_configuration': {'mapping_status': 'APPROVED'}}}}
        rendered = create_pr._renderer_row(record)
        self.assertEqual(rendered['BOQ Configuration Mapping Status'], 'APPROVED')
        self.assertIn('BOQ Configuration Mapping Status', create_pr.CANONICAL_RENDERER_COLUMNS)
        self.assertEqual(resolve_nlos_standard(rendered)['selected_size'], 0.3)

    def test_nlos_is_installation_not_automatic_old_dismantle_evidence(self):
        from mw_link_scope import installation_evidence, dismantle_evidence
        source = row(**{'TX SOW Details': 'NLOS'})
        self.assertEqual(installation_evidence(source)['size'], 0.3)
        self.assertIsNone(dismantle_evidence(source)['size'])
        self.assertEqual(dismantle_evidence(source)['reason'], 'MW_REROUTE_DECOM_ANTENNA_SIZE_MISSING')
        source['MW Config Antenna Size NE'] = '1.2m'
        self.assertEqual(installation_evidence(source)['reason'], 'NLOS_ANTENNA_EVIDENCE_CONFLICT')


class StarlinkTests(unittest.TestCase):
    def test_starlink_work_is_not_applicable_even_with_unrelated_mw_evidence(self):
        result = resolve_installation_antenna_evidence(row(**{
            'Tx SOW': 'Starlink Dismanle', 'Migration Work Item': 'Dismantle Starlink',
            'TX SOW Details': 'NLOS', 'MW Config Antenna Size NE': '1.2m'}))
        self.assertEqual(result['status'], 'NOT_APPLICABLE')
        self.assertIsNone(result['selected_size'])

    def test_mixed_scope_does_not_exempt_mw_work(self):
        for sow in ('MW SWAP', 'MW New Link / Reroute', 'Starlink-MW', 'New Starlink'):
            source = row(**{'Tx SOW': sow, 'Migration Work Item': 'MW New Link'})
            self.assertFalse(is_starlink_only_work_item(source))
            self.assertEqual(resolve_installation_antenna_evidence(source)['status'], 'MISSING')


class GeneratorGuidanceTests(TestMwSwapGeneratorFallback):
    def _write_site_workbook(self, path, rows):
        import pandas as pd
        columns = list(dict.fromkeys([*SITE_COLUMNS, *(key for item in rows for key in item)]))
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            pd.DataFrame(rows, columns=columns).to_excel(writer, sheet_name='data', index=False, startrow=3)

    def test_mixed_starlink_mw_plan_requires_mw_size_and_is_atomic(self):
        common = {'DU Profile ID': 'jendela_tx_migration_pr_v1', 'Migration Decision ID': 'mixed-plan'}
        source = [row(**{**common, 'Tx SOW': 'Starlink Dismanle',
                         'Migration Work Item': 'Dismantle Starlink',
                         'Required PBOM Codes': '350000597850|350000597852'}),
                  row(**{**common, 'Tx SOW': 'MW New Link / Reroute',
                         'Migration Work Item': 'MW New Link'})]
        result, sites, reviews, diagnostics = self._run_generator(source)
        self.assertNotIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertTrue(any(r['Reason_Code'] == 'MISSING_TI_ANTENNA_SIZE' for r in reviews), diagnostics)

    def test_canonical_unapproved_nlos_is_not_used_by_generator(self):
        source = row(**{'TX SOW Details': 'NLOS',
                        'Antenna Evidence Governance': 'CANONICAL_MAPPING_STATUS',
                        'TX SOW Details Mapping Status': 'UNVERIFIED'})
        result, sites, reviews, diagnostics = self._run_generator([source])
        self.assertNotIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertTrue(any(r['Reason_Code'] == 'MISSING_TI_ANTENNA_SIZE' for r in reviews), diagnostics)

    def test_nlos_swap_generates_from_real_approved_model(self):
        result, sites, reviews, diagnostics = self._run_generator([row(**{'TX SOW Details': 'NLOS'})])
        self.assertEqual(result.returncode, 0, diagnostics)
        self.assertIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertFalse(reviews, diagnostics)
        self.assertIn('selected_size=0.3', result.stdout)

    def test_nlos_conflict_is_precise_review_not_ecc(self):
        result, sites, reviews, diagnostics = self._run_generator([row(**{
            'TX SOW Details': 'NLOS', 'MW Config Antenna Size NE': '1.2m'})])
        self.assertNotIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertTrue(any(r['Reason_Code'] == 'NLOS_ANTENNA_EVIDENCE_CONFLICT' for r in reviews), diagnostics)

    def test_starlink_only_generates_without_antenna(self):
        result, sites, reviews, diagnostics = self._run_generator([row(**{'Tx SOW': 'Starlink Dismanle'})])
        self.assertEqual(result.returncode, 0, diagnostics)
        self.assertIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertFalse(reviews, diagnostics)
        _, models = load_pr_model_items(ROOT / 'Info/input/pr_model.xlsx')
        required = {m['PBOM_Code'] for m in models if m['SOW'] == 'Starlink Dismanle' and m['Is_Mandatory']}
        selected = {str(values[9]) for values in diagnostics['generated_rows']}
        self.assertEqual(selected, required, diagnostics)

    def test_nlos_reroute_resolves_size_but_does_not_guess_antenna_count(self):
        result, sites, reviews, diagnostics = self._run_generator([row(**{
            'Tx SOW': 'MW New Link / Reroute', 'TX SOW Details': 'NLOS'})])
        self.assertEqual(result.returncode, 0, diagnostics)
        self.assertNotIn('GUIDANCE_TEST', sites, diagnostics)
        self.assertTrue(any(r['Reason_Code'] == 'MW_LINK_SCOPE_UNRESOLVED' for r in reviews), diagnostics)
        self.assertIn('[MW_LINK_SCOPE]', result.stdout)
        self.assertFalse(any('ANTENNA_SIZE_MISSING' in r['Reason_Code'] for r in reviews), diagnostics)


if __name__ == '__main__':
    unittest.main()