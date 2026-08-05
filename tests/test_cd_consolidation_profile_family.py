#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE_ROOT = ROOT / "config" / "du_profiles"
REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"
CANONICAL_PROFILE_ID = "celcomdigi_cd_consolidation_2023_pr_v1"
CANONICAL_PROFILE_PATH = PROFILE_ROOT / f"{CANONICAL_PROFILE_ID}.yaml"
OLD_PROFILE_PATHS = {
    PROFILE_ROOT / "cd_consolidation_2023_decom_pr_v1.yaml",
    PROFILE_ROOT / "cd_consolidation_2023_rollout_pr_v1.yaml",
}
IDENTITY_KEY = "Malaysia_CelcomDigi_Project::8359047522524182050"


class TestCdConsolidationProfileFamily(unittest.TestCase):
    def test_registry_has_one_canonical_identity_route(self):
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        records = [
            row for row in registry["profiles"]
            if row["identity_key"] == IDENTITY_KEY
        ]

        self.assertEqual([row["profile_id"] for row in records], [CANONICAL_PROFILE_ID])
        self.assertEqual(records[0]["canonical_profile_id"], CANONICAL_PROFILE_ID)
        self.assertEqual(records[0]["name_status"], "STANDARD")
        self.assertEqual(
            records[0]["accepted_view_ids"],
            ["702960351133798763", "8359047522524230651"],
        )
        self.assertFalse(registry.get("identity_reviews"))

    def test_profile_preserves_both_layouts_and_remains_fail_closed(self):
        profile = json.loads(CANONICAL_PROFILE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(profile["profile_id"], CANONICAL_PROFILE_ID)
        self.assertEqual(profile["status"], "DRAFT")
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        self.assertEqual(
            profile["export_structure"]["observed_header_hashes"],
            [
                "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16",
                "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1",
            ],
        )

        variants = {row["variant_id"]: row for row in profile["layout_variants"]}
        self.assertEqual(set(variants), {"decom", "rollout"})
        self.assertEqual(variants["decom"]["view_id"], "702960351133798763")
        self.assertEqual(variants["rollout"]["view_id"], "8359047522524230651")
        self.assertEqual(
            variants["decom"]["observed_header_hash"],
            "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16",
        )
        self.assertEqual(
            variants["rollout"]["observed_header_hash"],
            "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1",
        )
        for variant in variants.values():
            for mapping in variant["field_mapping"].values():
                for candidate in mapping.get("source_candidates", []):
                    self.assertEqual(candidate["mapping_status"], "UNVERIFIED")

    def test_old_view_based_profile_files_are_removed(self):
        self.assertTrue(CANONICAL_PROFILE_PATH.exists())
        self.assertFalse(any(path.exists() for path in OLD_PROFILE_PATHS))


if __name__ == "__main__":
    unittest.main()
