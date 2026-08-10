import csv
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from create_pr import _build_site_reconciliation, _canonical_relocate_site_id
from renderer_reconciliation import collect_renderer_reconciliation


def record(site_code):
    return {"site": {"site_code": site_code}}


class TestIssue74RelocateIdentity(unittest.TestCase):
    def test_decom_relo_site_id_collapses_numbered_suffix(self):
        self.assertEqual(_canonical_relocate_site_id("B00288_RELOCATE1"), "B00288_Relocate")
        self.assertEqual(_canonical_relocate_site_id("S00144_Relocate_1"), "S00144_Relocate")
        self.assertEqual(_canonical_relocate_site_id("S00311_Relocate"), "S00311_Relocate")


class TestIssue74RendererReconciliation(unittest.TestCase):
    def test_reads_generated_and_review_required_sites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ecc = root / "Central-Magicell TX Rollout TI PR 20260810.xlsx"
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "details"
            worksheet.append(["SN.", "Site ID*"])
            worksheet.append([1, "A_Relocate"])
            workbook.save(ecc)

            review = root / "REVIEW_REQUIRED_TI_20260810.csv"
            with review.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Site_ID", "Reason_Code"])
                writer.writeheader()
                writer.writerow({"Site_ID": "B_Relocate", "Reason_Code": "NO_MATCHING_TI_PR_MODEL_ITEM"})

            candidates = [record("A_RELOCATE1"), record("B_RELOCATE2")]
            result = collect_renderer_reconciliation(
                root,
                candidates,
                "TI",
                lambda item: _canonical_relocate_site_id(item["site"]["site_code"]),
                created_paths=[ecc, review],
            )

            self.assertEqual(result["site_dispositions"][0]["disposition"], "GENERATED")
            self.assertEqual(result["site_dispositions"][1]["disposition"], "REVIEW_REQUIRED")
            self.assertEqual(result["site_dispositions"][1]["reason_code"], "NO_MATCHING_TI_PR_MODEL_ITEM")


class TestIssue74Reconciliation(unittest.TestCase):
    def test_every_selected_site_has_exactly_one_terminal_disposition(self):
        selected = [record("A_GENERATED"), record("B_REVIEW"), record("C_IGNORED"), record("D_DUP")]
        partitions = {
            "candidates": [selected[0], selected[1]],
            "review_required": [],
            "ignored": [selected[2]],
            "duplicates": [selected[3]],
        }
        renderer = {
            "site_dispositions": [
                {"site_code": "A_GENERATED", "disposition": "GENERATED"},
                {"site_code": "B_REVIEW", "disposition": "REVIEW_REQUIRED", "reason_code": "NO_MATCHING_TI_PR_MODEL_ITEM"},
            ]
        }

        result = _build_site_reconciliation(selected, partitions, renderer)

        self.assertEqual(result["requested_count"], 4)
        self.assertEqual(result["generated_count"], 1)
        self.assertEqual(result["review_required_count"], 1)
        self.assertEqual(result["approved_ignored_count"], 1)
        self.assertEqual(result["duplicate_blocked_count"], 1)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(result["unaccounted_count"], 0)
        self.assertEqual(len(result["site_dispositions"]), 4)

    def test_candidate_missing_from_renderer_is_failed_not_silent(self):
        selected = [record("MISSING_FROM_RENDERER")]
        partitions = {
            "candidates": list(selected),
            "review_required": [],
            "ignored": [],
            "duplicates": [],
        }

        result = _build_site_reconciliation(selected, partitions, {"site_dispositions": []})

        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["unaccounted_count"], 0)
        self.assertEqual(result["site_dispositions"][0]["disposition"], "FAILED")
        self.assertEqual(result["site_dispositions"][0]["reason_code"], "RENDERER_SITE_UNACCOUNTED")


if __name__ == "__main__":
    unittest.main()
