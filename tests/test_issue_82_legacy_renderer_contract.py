#!/usr/bin/env python3
"""Compatibility guard for synthetic/legacy renderer records used by governed tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from antenna_evidence_resolver import resolve_installation_antenna_evidence
from create_pr import _renderer_row


class TestIssue82LegacyRendererContract(unittest.TestCase):
    def test_record_without_canonical_source_evidence_keeps_legacy_direct_antenna_contract(self):
        record = {
            "identity": {"source_row_number": 7},
            "site": {"site_code": "LEGACY", "site_name": "Legacy", "du_key": "DU-LEGACY"},
            "pr_context": {
                "region": "Southern",
                "state": "Johor",
                "tx_sow_normalized": "MW SWAP",
                "subcontractor_ti": "GTSB",
            },
            "technical_context": {
                "antenna_size_ne": "0.6m",
                "antenna_size_fe": "0.6m",
            },
            "validation": {"profile_id": "jendela_tx_migration_pr_v1"},
            "approved_contract": {"scope": "TI", "subcontractor": "GTSB"},
        }

        row = _renderer_row(record)
        self.assertEqual(row["Antenna Evidence Governance"], "")
        result = resolve_installation_antenna_evidence(row)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["selected_size"], 0.6)


if __name__ == "__main__":
    unittest.main()
