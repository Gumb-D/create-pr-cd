#!/usr/bin/env python3
"""Official create-pr Planning integration regression coverage for Issue #34."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import create_pr  # noqa: E402


class PlanningOfficialEntrypointTest(unittest.TestCase):
    def test_official_parser_accepts_planning_scope(self):
        argv = [
            "create_pr.py",
            "--site-data",
            "input.xlsx",
            "--output",
            "output",
            "--scope",
            "Planning",
            "--all-sites",
        ]
        with patch.object(sys, "argv", argv):
            parsed = create_pr.parse_args()
        self.assertEqual(parsed.scope, "PLANNING")

    def test_scope_renderer_routes_only_planning_to_dedicated_renderer(self):
        self.assertEqual(
            create_pr._renderer_for_scope("Planning").name,
            "planning_ecc_renderer.py",
        )
        self.assertEqual(
            create_pr._renderer_for_scope("TSS").name,
            "generate_tss_pr_ecc.py",
        )
        self.assertEqual(
            create_pr._renderer_for_scope("TI").name,
            "generate_tss_pr_ecc.py",
        )

    def test_renderer_row_carries_planning_source_and_selection_evidence(self):
        record = {
            "identity": {"du_model_name": "2024 Celcomdigi BAU"},
            "site": {"site_code": "A0001", "site_name": "Planning Site", "du_key": "DU-A0001"},
            "pr_context": {
                "region": "Central",
                "state": "Selangor",
                "subcontractor_planning": "GCI_AA",
            },
            "technical_context": {},
            "source_evidence": {"fields": {}},
            "validation": {"profile_id": "celcomdigi_bau_2024_pr_v1"},
            "approved_contract": {
                "scope": "PLANNING",
                "subcontractor": "GCI",
                "contract_number": "S1MY2024071002WBF1",
            },
            "planning_selection": {
                "status": "RESOLVED",
                "pbom_code": "350001042321",
                "description": "Detailed end to end transmission planning and design (for AA modification & AA submisison sow only)",
                "quantity": 1,
                "unit": "Hop",
                "contract_subcontractor": "GCI",
                "reason_code": None,
            },
        }
        row = create_pr._renderer_row(record)
        self.assertEqual(row["Subcon - Planning"], "GCI_AA")
        self.assertEqual(row["Planning Contract Subcontractor"], "GCI")
        self.assertEqual(row["Planning PBOM Code"], "350001042321")
        self.assertEqual(row["Planning Unit"], "Hop")
        self.assertEqual(row["Planning Quantity"], 1)
        self.assertIn("Planning SOW", create_pr.CANONICAL_RENDERER_COLUMNS)
        self.assertIn("Subcon - Planning", create_pr.CANONICAL_RENDERER_COLUMNS)

    def test_run_selects_planning_renderer_before_delegating_to_impl(self):
        class Parsed:
            pr_model = ROOT / "Info" / "input" / "pr_model.xlsx"
            output = ROOT / "output"
            scope = "PLANNING"

        fake_summary = {
            "status": "SUCCESS",
            "run_mode": "PRODUCTION",
            "output_root": str(ROOT / "output"),
            "summary_path": str(ROOT / "output" / "summary.json"),
        }
        baseline = {
            "baseline_id": "test",
            "version": "test",
            "actual_sha256": "hash",
            "path": Parsed.pr_model,
        }
        with (
            patch.object(create_pr, "validate_pr_model_baseline", return_value=baseline),
            patch.object(create_pr, "snapshot_renderer_artifacts", return_value={}),
            patch.object(create_pr._impl, "run", return_value=dict(fake_summary)) as impl_run,
            patch.object(create_pr, "_write_ignored_report", return_value=None),
            patch.object(create_pr, "_reconcile_summary", return_value={
                "requested_count": 0,
                "generated_count": 0,
                "review_required_count": 0,
                "approved_ignored_count": 0,
                "duplicate_blocked_count": 0,
                "failed_count": 0,
                "unaccounted_count": 0,
                "site_dispositions": [],
            }),
            patch.object(Path, "write_text", return_value=1),
        ):
            create_pr.run(Parsed())
            impl_run.assert_called_once()
            self.assertEqual(create_pr._impl.RENDERER.name, "planning_ecc_renderer.py")


if __name__ == "__main__":
    unittest.main()
