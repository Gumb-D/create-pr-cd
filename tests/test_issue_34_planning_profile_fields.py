#!/usr/bin/env python3
"""Issue #34 profile-level Planning field mapping contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "config" / "du_profiles"

EXPECTED = {
    "tx_rollout_2023_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01027586", "Network Planning", "Microwave", "Subcon - Planning"),
        "status": ("docata|ZDCSZ01027605", "Network Planning", "Microwave", "Subcon PR - Planning"),
    },
    "tx_mini_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01027586", "Network Planning", "Microwave", "Subcon - Planning"),
        "status": ("docata|ZDCSZ01027605", "Network Planning", "Microwave", "Subcon PR - Planning"),
    },
    "celcomdigi_bau_2023_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01036640", "Installation", "Wireless RAN", "Subcon Planning"),
        "status": ("docata|ZDCSZ01036639", "Installation", "Wireless RAN", "Subcon PR - Planning"),
    },
    "celcomdigi_bau_2024_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01036640", "Installation", "Wireless RAN", "Subcon Planning"),
        "status": ("docata|ZDCSZ01036639", "Installation", "Wireless RAN", "Subcon PR - Planning"),
    },
    "celcomdigi_usp_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01036640", "Installation", "Wireless RAN", "Subcon Planning"),
        "status": ("docata|ZDCSZ01036639", "Installation", "Wireless RAN", "Subcon PR - Planning"),
    },
    "jendela_tx_migration_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01036640", "Installation", "Wireless RAN", "Subcon Planning"),
        "status": ("docata|ZDCSZ01036639", "Installation", "Wireless RAN", "Subcon PR - Planning"),
    },
    "mw_eos_swap_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01087327", "Network Planning", "Microwave", "Subcon - Planning"),
        "status": ("docata|ZDCSZ01087326", "Network Planning", "Microwave", "Subcon - PR Planning"),
    },
    "zte_tx_mini_pr_v1.yaml": {
        "planning": ("docata|ZDCSZ01087327", "Network Planning", "Microwave", "Subcon - Planning"),
        "status": ("docata|ZDCSZ01087326", "Network Planning", "Microwave", "Subcon - PR Planning"),
    },
}


def _fingerprint_tuple(field_config: dict) -> tuple[str, str, str, str]:
    candidates = field_config.get("source_candidates", [])
    if len(candidates) != 1:
        raise AssertionError(f"Expected exactly one Planning source candidate, got {len(candidates)}")
    candidate = candidates[0]
    if candidate.get("mapping_status") != "APPROVED":
        raise AssertionError(f"Planning mapping must be APPROVED, got {candidate.get('mapping_status')}")
    fp = candidate["fingerprint"]
    return (fp["field_code"], fp["wbs_stage"], fp["task_name"], fp["display_header"])


class PlanningProfileFieldTest(unittest.TestCase):
    def test_all_supported_profiles_have_exact_approved_planning_fields(self) -> None:
        for filename, expected in EXPECTED.items():
            with self.subTest(profile=filename):
                profile = json.loads((PROFILE_DIR / filename).read_text(encoding="utf-8"))
                fields = profile["field_mapping"]
                self.assertEqual(
                    _fingerprint_tuple(fields["subcontractor_planning"]),
                    expected["planning"],
                )
                self.assertEqual(
                    _fingerprint_tuple(fields["existing_planning_pr_status"]),
                    expected["status"],
                )
                self.assertEqual(fields["subcontractor_planning"].get("transforms"), ["trim"])
                self.assertEqual(
                    fields["existing_planning_pr_status"].get("transforms"),
                    ["normalize_pr_reference_status"],
                )

    def test_tx_planning_remarks_is_not_a_canonical_planning_field(self) -> None:
        for filename in EXPECTED:
            with self.subTest(profile=filename):
                profile = json.loads((PROFILE_DIR / filename).read_text(encoding="utf-8"))
                fields = profile["field_mapping"]
                self.assertNotIn("tx_planning_remarks", fields)
                self.assertNotIn("planning_remarks", fields)


if __name__ == "__main__":
    unittest.main()
