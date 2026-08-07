#!/usr/bin/env python3
"""Regression coverage for Issue #69 MW Hardware Upgrade TI selection."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "generate_tss_pr_ecc.py"
PR_MODEL_PATH = ROOT / "Info" / "input" / "pr_model.xlsx"
TEMPLATE_PATH = ROOT / "Info" / "input" / "ecc_template.xls"
MAPPING_PATH = ROOT / "Info" / "input" / "contract_info_reference.md"
PROFILE_DIR = ROOT / "config" / "du_profiles"

SITE_COLUMNS = [
    "customer site code",
    "customer site name",
    "du code",
    "region",
    "Province/State",
    "Latitude (North Plus South Minus)",
    "Longitude (East Plus West Minus)",
    "TX Upgrade Scope",
    "Tx SOW",
    "MW Config Antenna Size NE",
    "MW Config Antenna Size FE",
    "SubCon - TI Team",
    "Subcon PR - TI",
]

SUBTYPE_PBOMS = {
    "IDU swap": "350001095419",
    "ODU swap without site survey": "350001095418",
    "ODU swap with site survey": "350001095417",
}


def _site(site_code: str, upgrade_scope: str) -> dict[str, object]:
    return {
        "customer site code": site_code,
        "customer site name": f"Issue 69 {site_code}",
        "du code": f"DU-{site_code}",
        "region": "Central",
        "Province/State": "Selangor",
        "Latitude (North Plus South Minus)": 3.0738,
        "Longitude (East Plus West Minus)": 101.5183,
        "TX Upgrade Scope": upgrade_scope,
        "Tx SOW": "  mw   hardware   upgrade  ",
        "MW Config Antenna Size NE": "",
        "MW Config Antenna Size FE": "",
        "SubCon - TI Team": "GTSB",
        "Subcon PR - TI": "",
    }


class MwHardwareUpgradeGeneratorHarness(unittest.TestCase):
    def _write_site_workbook(self, path: Path, rows: list[dict[str, object]]) -> None:
        dataframe = pd.DataFrame(rows, columns=SITE_COLUMNS)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            dataframe.to_excel(writer, sheet_name="data", index=False, startrow=3)

    def _run_generator(self, rows: list[dict[str, object]]):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            site_path = temporary_root / "issue-69-site-data.xlsx"
            output_dir = temporary_root / "output"
            output_dir.mkdir()
            self._write_site_workbook(site_path, rows)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--site-data",
                    str(site_path),
                    "--pr-model",
                    str(PR_MODEL_PATH),
                    "--template",
                    str(TEMPLATE_PATH),
                    "--mapping",
                    str(MAPPING_PATH),
                    "--output",
                    str(output_dir),
                    "--scope",
                    "TI",
                    "--all-sites",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            output_rows: list[dict[str, object]] = []
            for workbook_path in sorted(output_dir.glob("*.xlsx")):
                workbook = load_workbook(workbook_path, read_only=True, data_only=True)
                worksheet = workbook["details"]
                for values in worksheet.iter_rows(min_row=2, values_only=True):
                    if not values[0]:
                        continue
                    output_rows.append(
                        {
                            "Site_ID": values[3],
                            "PBOM_Code": str(values[9]),
                            "Description": values[10],
                            "Unit": values[11],
                            "Quantity": values[12],
                        }
                    )
                workbook.close()

            review_rows: list[dict[str, str]] = []
            review_files = sorted(output_dir.glob("REVIEW_REQUIRED_TI_*.csv"))
            if review_files:
                with review_files[0].open(newline="", encoding="utf-8-sig") as handle:
                    review_rows = list(csv.DictReader(handle))

            return result, output_rows, review_rows


class TestMwHardwareUpgradePositiveSelection(MwHardwareUpgradeGeneratorHarness):
    def test_each_approved_mandatory_subtype_selects_exact_pr_model_row(self):
        rows = [
            _site("HW_IDU", "IDU swap"),
            _site("HW_ODU_NO_TSS", "ODU swap without site survey"),
            _site("HW_ODU_TSS", "ODU swap with site survey"),
        ]

        result, output_rows, review_rows = self._run_generator(rows)

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        rows_by_site: dict[str, list[dict[str, object]]] = {}
        for row in output_rows:
            rows_by_site.setdefault(str(row["Site_ID"]), []).append(row)

        for source_row in rows:
            site_code = str(source_row["customer site code"])
            expected_pbom = SUBTYPE_PBOMS[str(source_row["TX Upgrade Scope"])]
            with self.subTest(site=site_code):
                self.assertIn(site_code, rows_by_site)
                subtype_rows = [
                    row for row in rows_by_site[site_code]
                    if row["PBOM_Code"] in set(SUBTYPE_PBOMS.values())
                ]
                self.assertEqual(len(subtype_rows), 1)
                self.assertEqual(subtype_rows[0]["PBOM_Code"], expected_pbom)
                self.assertEqual(subtype_rows[0]["Unit"], "Hop")
                self.assertEqual(float(subtype_rows[0]["Quantity"]), 1.0)

        self.assertEqual(review_rows, [])


class TestMwHardwareUpgradeFailClosed(MwHardwareUpgradeGeneratorHarness):
    def test_q02210_missing_subtype_uses_group_level_reason_not_false_no_model_match(self):
        result, output_rows, review_rows = self._run_generator([
            _site("Q02210_AD", ""),
        ])

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        self.assertFalse(any(row["Site_ID"] == "Q02210_AD" for row in output_rows))
        review_by_site = {row["Site_ID"]: row for row in review_rows}
        self.assertEqual(
            review_by_site["Q02210_AD"]["Reason_Code"],
            "MW_HARDWARE_UPGRADE_TYPE_UNRESOLVED",
        )
        self.assertNotEqual(
            review_by_site["Q02210_AD"]["Reason_Code"],
            "NO_MATCHING_TI_PR_MODEL_ITEM",
        )

    def test_ambiguous_idu_and_odu_evidence_blocks_whole_site(self):
        result, output_rows, review_rows = self._run_generator([
            _site("HW_AMBIGUOUS", "IDU and ODU swap"),
        ])

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        self.assertFalse(any(row["Site_ID"] == "HW_AMBIGUOUS" for row in output_rows))
        review_by_site = {row["Site_ID"]: row for row in review_rows}
        self.assertEqual(
            review_by_site["HW_AMBIGUOUS"]["Reason_Code"],
            "MW_HARDWARE_UPGRADE_TYPE_UNRESOLVED",
        )

    def test_odu_without_site_survey_evidence_is_not_guessed(self):
        result, output_rows, review_rows = self._run_generator([
            _site("HW_ODU_UNQUALIFIED", "ODU swap"),
        ])

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        self.assertFalse(any(row["Site_ID"] == "HW_ODU_UNQUALIFIED" for row in output_rows))
        review_by_site = {row["Site_ID"]: row for row in review_rows}
        self.assertEqual(
            review_by_site["HW_ODU_UNQUALIFIED"]["Reason_Code"],
            "MW_HARDWARE_UPGRADE_TYPE_UNRESOLVED",
        )


class TestMwHardwareUpgradeProfileEvidence(unittest.TestCase):
    def test_every_production_profile_with_approved_upgrade_scope_uses_shared_field(self):
        supported_profiles = []
        for profile_path in sorted(PROFILE_DIR.glob("*.yaml")):
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            if profile.get("status") != "PRODUCTION":
                continue
            mapping = profile.get("field_mapping", {}).get("tx_upgrade_scope_raw", {})
            approved_candidates = [
                candidate
                for candidate in mapping.get("source_candidates", [])
                if candidate.get("mapping_status") == "APPROVED"
            ]
            if approved_candidates:
                supported_profiles.append(profile["profile_id"])
                self.assertEqual(
                    approved_candidates[0]["fingerprint"]["display_header"],
                    "TX Upgrade Scope",
                )

        self.assertIn("tx_mini_pr_v1", supported_profiles)
        self.assertIn("mw_eos_swap_pr_v1", supported_profiles)
        self.assertIn("tx_rollout_2023_pr_v1", supported_profiles)


if __name__ == "__main__":
    unittest.main()
