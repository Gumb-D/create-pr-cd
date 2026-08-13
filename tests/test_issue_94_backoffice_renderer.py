import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from openpyxl import Workbook, load_workbook
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from backoffice_ecc_renderer import BackofficeRendererError, load_backoffice_model_item, render

LOW='350000592793'
HIGH='350000592794'

def make_model(path, duplicate=False):
    wb=Workbook(); ws=wb.active; ws.title='TX Line Item (After 21-Apr 26)'
    ws.append(['SOW','PBOM Code','Description','Unit','Quantity','Rules'])
    ws.append(['Operation Back Office',LOW,'Microwave Back office commisioning and troubleshooting service(Less Than 800 Hops for each month)','Hop',1,'2 choose 1 (Mandatory)'])
    ws.append(['Operation Back Office',HIGH,'Microwave Back office commisioning and troubleshooting service(More Than 800 Hops for each month)','Hop',1,'2 choose 1 (Mandatory)'])
    if duplicate: ws.append(['Operation Back Office',LOW,'duplicate','Hop',1,'2 choose 1 (Mandatory)'])
    wb.save(path); wb.close()

def make_input(path, pbom=LOW, issue='MAIN', contract='S1MY2024042501WBF1'):
    headers=['customer site code','customer site name','du code','region','Backoffice Event Code','Backoffice Trigger Date','Backoffice Billing Month','Backoffice PBOM Code','Backoffice Unit','Backoffice Quantity','Backoffice Subcontractor','Backoffice Contract Number','Backoffice Issue Type','Backoffice Warnings']
    wb=Workbook(); ws=wb.active; ws.title='data'; ws.append(['CANONICAL CREATE-PR-CD INPUT']); ws.append(['x']); ws.append(['x']); ws.append(headers)
    ws.append(['S1','Site 1','DU1','Central','TX_MINI_INTEGRATION','2026-07-15','2026-07',pbom,'Hop',1,'Allstar',contract,issue,''])
    wb.save(path); wb.close()

def make_mapping(path):
    path.write_text('''## Region to Purchasing Area\n| Region* | Purchasing Area* |\n|---|---|\n| Central | Central |\n''',encoding='utf-8')

class TestBackofficeRenderer(unittest.TestCase):
    def test_model_item_is_read_from_operation_back_office_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.xlsx'; make_model(p)
            item=load_backoffice_model_item(p,LOW)
            self.assertEqual(LOW,item['pbom_code'])
            self.assertEqual('Hop',item['unit'])
            self.assertIn('Less Than 800 Hops',item['description'])

    def test_duplicate_pbom_in_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.xlsx'; make_model(p,True)
            with self.assertRaises(BackofficeRendererError) as cm: load_backoffice_model_item(p,LOW)
            self.assertEqual('BACKOFFICE_PR_MODEL_PBOM_AMBIGUOUS',cm.exception.code)

    def test_main_ecc_has_governed_values(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); model=root/'m.xlsx'; inp=root/'i.xlsx'; mapping=root/'map.md'; out=root/'out'
            make_model(model); make_input(inp); make_mapping(mapping)
            paths=render(Namespace(site_data=inp,pr_model=model,mapping=mapping,output=out,scope='BACKOFFICE',du_model_name='TX Mini Project',all_sites=True,site_code=None))
            self.assertEqual(1,len(paths)); self.assertIn('Backoffice MAIN 2026-07',paths[0].name)
            wb=load_workbook(paths[0],read_only=True,data_only=True); ws=wb['details']; row=[ws.cell(2,c).value for c in range(1,17)]; wb.close()
            self.assertEqual('DU1',row[5]); self.assertEqual('S1MY2024042501WBF1',row[7]); self.assertEqual('Allstar',row[8]); self.assertEqual(LOW,str(row[9])); self.assertIn('Less Than 800 Hops',row[10]); self.assertEqual('Hop',row[11]); self.assertEqual(1,row[12])

    def test_filename_contains_pr_marker_for_terminal_reconciliation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); model=root/'m.xlsx'; inp=root/'i.xlsx'; mapping=root/'map.md'; out=root/'out'
            make_model(model); make_input(inp); make_mapping(mapping)
            paths=render(Namespace(site_data=inp,pr_model=model,mapping=mapping,output=out,scope='BACKOFFICE',du_model_name='TX Mini Project',all_sites=True,site_code=None))
            self.assertIn(' PR ',paths[0].name)

    def test_supplementary_name_is_auditable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); model=root/'m.xlsx'; inp=root/'i.xlsx'; mapping=root/'map.md'; out=root/'out'
            make_model(model); make_input(inp,issue='SUPPLEMENTARY'); make_mapping(mapping)
            paths=render(Namespace(site_data=inp,pr_model=model,mapping=mapping,output=out,scope='BACKOFFICE',du_model_name='TX Mini Project',all_sites=True,site_code=None))
            self.assertIn('Backoffice SUPPLEMENTARY 2026-07',paths[0].name)

    def test_pipeline_pbom_or_contract_mismatch_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); model=root/'m.xlsx'; inp=root/'i.xlsx'; mapping=root/'map.md'; out=root/'out'
            make_model(model); make_input(inp,contract='WRONG'); make_mapping(mapping)
            with self.assertRaises(BackofficeRendererError): render(Namespace(site_data=inp,pr_model=model,mapping=mapping,output=out,scope='BACKOFFICE',du_model_name='TX Mini Project',all_sites=True,site_code=None))
            self.assertFalse(out.exists() and any(out.iterdir()))

if __name__=='__main__': unittest.main()
