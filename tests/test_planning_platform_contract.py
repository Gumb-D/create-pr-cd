"""Planning exercised through the real public manifest adapter; offline synthetic exports."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from openpyxl import load_workbook
from tests.test_issue_34_planning_end_to_end import _write_raw_export, _load_profile, _ecc_rows, PROFILE_EXPECTED_PBOM

ROOT = Path(__file__).resolve().parents[1]

class PlanningPlatformContractTests(unittest.TestCase):
    def execute(self, root, source, scope='PLANNING', sites=None):
        params={'scope':scope,'allSites':sites is None,'nonProductionUat':False}
        if sites is not None:params['siteCodes']=sites
        envelope={'schemaVersion':'1.0','jobId':'PLANNING-CONTRACT','skill':{'skillId':'create-pr-cd','version':json.loads((ROOT/'skill.json').read_text())['version']},
                  'parameters':params,'files':[{'name':'site_data','path':source.name,'size':source.stat().st_size,
                  'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}],
                  'paths':{'workspace':'.','output':'output','result':'result.json','cancellation':'temp/cancel.requested'}}
        manifest=root/'input.json';manifest.write_text(json.dumps(envelope),encoding='utf-8')
        run=subprocess.run([sys.executable,str(ROOT/'src/main.py'),'--input-manifest',str(manifest)],cwd=ROOT,capture_output=True,text=True,timeout=120)
        result=json.loads((root/'result.json').read_text(encoding='utf-8'))
        return run,result

    def test_manifest_option_and_other_scope_rejected(self):
        m=json.loads((ROOT/'skill.json').read_text())
        self.assertEqual(m['inputs']['parametersSchema']['properties']['scope']['enum'],['TSS','TI','PLANNING'])
        self.assertIn({'value':'PLANNING','label':'Planning'},m['ui']['parameters']['scope']['options'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';_write_raw_export(src,_load_profile('tx_mini_pr_v1'),[('P1','GCI')])
            run,result=self.execute(root,src,scope='BACKOFFICE')
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(result['error']['code'],'PARAMETERS_INVALID')

    def test_all_profiles_all_sites_actual_ecc_archive_and_reconciliation(self):
        for profile_id, pbom in PROFILE_EXPECTED_PBOM.items():
            with self.subTest(profile=profile_id), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);src=root/'sites.xlsx';_write_raw_export(src,_load_profile(profile_id),[('P1','GCI'),('P2','GTSB_AA')])
                before=hashlib.sha256(src.read_bytes()).hexdigest()
                run,result=self.execute(root,src)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertEqual(result['status'],'succeeded')
                self.assertEqual(result['skillVersion'],json.loads((ROOT/'skill.json').read_text())['version'])
                self.assertEqual(result['reconciliation']['unaccountedCount'],0)
                self.assertEqual(result['reconciliation']['generatedCount'],2)
                rows=_ecc_rows(root/'output');self.assertEqual({str(row[9]) for row in rows},{pbom,'350001042321'})
                self.assertEqual({str(row[3]) for row in rows},{'P1','P2'})
                self.assertTrue(all(row[12]==1 for row in rows))
                archive=root/'output/CREATE_PR_DELIVERY_PLANNING.zip';self.assertTrue(archive.exists())
                with zipfile.ZipFile(archive) as z:self.assertTrue(any(n.endswith('.xlsx') for n in z.namelist()))
                for item in result['outputs']:
                    p=root/item['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),item['sha256'])
                self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),before)

    def test_single_site_selection_does_not_include_unselected_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';_write_raw_export(src,_load_profile('tx_mini_pr_v1'),[('P1','GCI'),('P2','GTSB_AA')])
            run,result=self.execute(root,src,sites=['P2'])
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual({str(x[3]) for x in _ecc_rows(root/'output')},{'P2'})
            self.assertEqual(result['reconciliation']['unaccountedCount'],0)

    def test_existing_pr_blank_vendor_and_unknown_vendor_are_not_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';profile=_load_profile('tx_mini_pr_v1')
            _write_raw_export(src,profile,[('DUPLICATE','GCI'),('BLANK',''),('UNKNOWN','UNKNOWN_VENDOR')])
            wb=load_workbook(src);ws=wb['data'];display=profile['field_mapping']['existing_planning_pr_status']['source_candidates'][0]['fingerprint']['display_header']
            column=next(c.column for c in ws[4] if c.value==display);ws.cell(5,column,'PSQ_EXISTING');wb.save(src);wb.close()
            run,result=self.execute(root,src)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual(result['status'],'succeeded_with_warning')
            self.assertEqual(_ecc_rows(root/'output'),[])
            rec=result['reconciliation'];self.assertEqual(rec['duplicateBlockedCount'],1);self.assertEqual(rec['approvedIgnoredCount'],1);self.assertEqual(rec['reviewRequiredCount'],1);self.assertEqual(rec['unaccountedCount'],0)

    def test_missing_planning_source_mapping_does_not_generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';profile=_load_profile('tx_mini_pr_v1');_write_raw_export(src,profile,[('P1','GCI')])
            wb=load_workbook(src);ws=wb['data'];display=profile['field_mapping']['subcontractor_planning']['source_candidates'][0]['fingerprint']['display_header']
            col=next(c.column for c in ws[4] if c.value==display);ws.delete_cols(col);wb.save(src);wb.close()
            run,result=self.execute(root,src)
            self.assertEqual(_ecc_rows(root/'output'),[])
            self.assertNotEqual(result['status'],'succeeded')

    def test_unsupported_du_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';_write_raw_export(src,_load_profile('tx_mini_pr_v1'),[('P1','GCI')])
            wb=load_workbook(src);ws=wb['data'];
            # Model identity is carried by the authoritative field-code fingerprint,
            # not an arbitrary business cell in column B.
            col=next(c.column for c in ws[1] if isinstance(c.value,str) and c.value.startswith('site|fix00012|'))
            ws.cell(1,col,'site|fix00012|UNSUPPORTED_MODEL_ID|UNSUPPORTED_VIEW_ID');wb.save(src);wb.close()
            run,result=self.execute(root,src)
            self.assertNotEqual(result['status'],'succeeded')
            self.assertEqual(_ecc_rows(root/'output'),[])

    def test_cancellation_prevents_domain_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'sites.xlsx';_write_raw_export(src,_load_profile('tx_mini_pr_v1'),[('P1','GCI')])
            (root/'temp').mkdir();(root/'temp/cancel.requested').write_text('cancel')
            run,result=self.execute(root,src)
            self.assertEqual(result['status'],'cancelled');self.assertNotEqual(run.returncode,0)

if __name__=='__main__':unittest.main()
