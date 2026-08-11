import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from create_pr_impl import CreatePrError, _parse_site_codes, _select_records


def record(site_code):
    return {"site": {"site_code": site_code}}


class TestIssue93RequestedSiteSelection(unittest.TestCase):
    def test_valid_case_variants_are_normalized_and_deduplicated(self):
        requested = _parse_site_codes("a0001,A0001,b0002")

        self.assertEqual(requested, ["A0001", "B0002"])
        selected = _select_records(
            [record("A0001"), record("B0002")],
            requested,
            False,
        )
        self.assertEqual(
            [item["site"]["site_code"] for item in selected],
            ["A0001", "B0002"],
        )

    def test_explicit_missing_site_fails_closed_with_missing_list(self):
        requested = _parse_site_codes("a0001,QA15_UNMATCHED")

        with self.assertRaises(CreatePrError) as caught:
            _select_records([record("A0001")], requested, False)

        self.assertEqual(caught.exception.code, "SITE_CODES_NOT_FOUND")
        self.assertEqual(
            caught.exception.details["missing_site_codes"],
            ["QA15_UNMATCHED"],
        )


if __name__ == "__main__":
    unittest.main()
