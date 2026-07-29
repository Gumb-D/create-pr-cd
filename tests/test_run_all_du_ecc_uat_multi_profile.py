import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import run_all_du_ecc_uat as batch


CONTRACT_PATH = ROOT / "Info" / "input" / "contract_info_reference.md"
POLICY_PATH = ROOT / "config" / "subcontractor_pr_policy.json"


def write_ecc(path: Path, site_code: str, scope: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "details"
    worksheet.append(
        [
            "SN.", "Purchasing Area*", "Region*", "Site ID*", "Site Name*",
            "Delivery Unit Code*", "Logical Site Name", "Contract Number *",
            "Subcontractor*", "PBOM Code*", "SOW*", "Unit*", "Quantity*",
            "Remarks", "", "Contract Number",
        ]
    )
    worksheet.append(
        [
            1, "Malaysia_Central Region", "Central", site_code, site_code,
            f"DU-{site_code}", site_code, "S1MY2024071004WBF1", "CCSMY",
            "PBOM-1", f"{scope} Model", "SITE", 1, "", "MW NEW LINK",
            "S1MY2024071004WBF1",
        ]
    )
    workbook.save(path)
    return path


def child_summary(profile_id: str, scope: str, scope_dir: Path, pack_type: str, path: Path) -> dict:
    summary_path = scope_dir / f"summary-{pack_type}-{scope}.json"
    summary = {
        "status": "SUCCESS",
        "entrypoint": "create_pr.py",
        "run_mode": "NON_PRODUCTION_UAT",
        "profile_status": "PR_INPUT_READY",
        "non_production_uat": True,
        "production_ecc_allowed": False,
        "requested_output": str(scope_dir),
        "output_root": str(scope_dir),
        "run_id": "child",
        "scope": scope,
        "profile_id": profile_id,
        "profile_version": "1.0.0",
        "mapping_version": "approved-v1",
        "project_key": "project",
        "du_model_name": f"DU {profile_id}",
        "du_model_id": profile_id,
        "view_id": f"view-{profile_id}",
        "header_hash": f"hash-{profile_id}",
        "source_record_count": 1,
        "selected_record_count": 1,
        "pre_contract_candidate_count": 1,
        "candidate_count": 1,
        "duplicate_count": 0,
        "ignored_count": 0,
        "review_required_count": 0,
        "contract_mapping_missing_count": 0,
        "sm_excluded_count": 0,
        "created_files": [str(path.resolve())],
        "review_report": None,
        "ignored_report": None,
        "contract_mapping_review_report": None,
        "summary_path": str(summary_path.resolve()),
        "pack_type": pack_type,
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return summary


class TestAllDuEccUatMultiProfile(unittest.TestCase):
    def test_two_profiles_run_tss_and_ti_independently_with_reconciled_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_a = root / "profile_a.xlsx"
            source_b = root / "profile_b.xlsx"
            source_a.write_bytes(b"source-a")
            source_b.write_bytes(b"source-b")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "profiles": [
                            {"profile_id": "profile_a", "source_export": str(source_a)},
                            {"profile_id": "profile_b", "source_export": str(source_b)},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            profiles = {
                "profile_a": {"profile_id": "profile_a", "status": "PR_INPUT_READY"},
                "profile_b": {"profile_id": "profile_b", "status": "PR_INPUT_READY"},
            }
            source_to_profile = {
                source_a.resolve(): "profile_a",
                source_b.resolve(): "profile_b",
            }

            def fake_resolve(path, **_kwargs):
                profile_id = source_to_profile[Path(path).resolve()]
                return {"profile": profiles[profile_id], "header_hash": f"hash-{profile_id}", "inventory": []}

            calls = []

            def fake_scope_pack(
                source_export,
                scope_dir,
                scope,
                pack_type,
                site_codes,
                profile_id,
                batch_run_id,
                args,
            ):
                calls.append((profile_id, scope, pack_type, tuple(site_codes or ())))
                site_code = f"{profile_id}-{scope}"
                path = write_ecc(
                    scope_dir / f"{site_code}_{pack_type}_NON_PRODUCTION_UAT_{batch_run_id}.xlsx",
                    site_code,
                    scope,
                )
                return child_summary(profile_id, scope, scope_dir, pack_type, path), [path.resolve()]

            args = argparse.Namespace(
                manifest=manifest,
                output=root / "output",
                review_max_combinations=500,
                run_id="MULTI-RUN",
                pr_model=Path("pr_model.xlsx"),
                template=Path("template.xls"),
                mapping=CONTRACT_PATH,
                subcontractor_policy=POLICY_PATH,
            )
            with mock.patch.object(batch, "load_structured_profiles", return_value=profiles), mock.patch.object(
                batch, "resolve_du_profile", side_effect=fake_resolve
            ), mock.patch.object(batch, "run_scope_pack", side_effect=fake_scope_pack):
                summary = batch.run_batch(args)

            self.assertEqual(summary["status"], "SUCCESS")
            self.assertEqual(summary["eligible_profile_count"], 2)
            self.assertEqual(summary["blocked_profile_count"], 0)
            self.assertEqual(summary["successful_scope_runs"], 4)
            self.assertEqual(summary["failed_scope_runs"], 0)
            self.assertEqual(summary["candidate_count"], 4)
            self.assertEqual(summary["generated_ecc_file_count"], 8)
            self.assertEqual(summary["generated_ecc_row_count"], 8)
            self.assertTrue(summary["manifest_reconciliation_ok"])
            self.assertEqual(summary["unsafe_manifest_row_count"], 0)
            self.assertEqual(
                {(profile, scope, pack) for profile, scope, pack, _ in calls},
                {
                    ("profile_a", "TSS", "FULL_PACK"),
                    ("profile_a", "TSS", "REVIEW_PACK"),
                    ("profile_a", "TI", "FULL_PACK"),
                    ("profile_a", "TI", "REVIEW_PACK"),
                    ("profile_b", "TSS", "FULL_PACK"),
                    ("profile_b", "TSS", "REVIEW_PACK"),
                    ("profile_b", "TI", "FULL_PACK"),
                    ("profile_b", "TI", "REVIEW_PACK"),
                },
            )


if __name__ == "__main__":
    unittest.main()
