import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_du_export_coverage_review import (
    BACKLOG_DISCOVERY_ONLY,
    DONOR_REVIEW_CANDIDATE,
    TRACKED_DRAFT_PROFILE,
    build_coverage_registry,
    coverage_markdown,
    write_coverage_outputs,
)


class TestDuExportCoverageReview(unittest.TestCase):
    def test_registry_summarizes_tracked_donor_and_backlog_exports(self):
        discovery_registry = {
            "entries": [
                {
                    "du_model_name": "TX Mini Project",
                    "source_file_name": "tx-mini.xlsx",
                    "profile_id": "tx_mini_pr_v1",
                    "profile_status": "DRAFT",
                    "profile_version": "0.1.0",
                    "mapping_version": "discovery-v1",
                    "observed_header_hash": "hash-a",
                    "skill_field_presence": {
                        "existing_tss_pr": False,
                        "existing_ti_pr": False,
                        "site_id": True,
                    },
                },
                {
                    "du_model_name": "2023 TX Rollout",
                    "source_file_name": "tx-rollout.xlsx",
                    "profile_id": None,
                    "profile_status": None,
                    "profile_version": None,
                    "mapping_version": None,
                    "observed_header_hash": "hash-b",
                    "skill_field_presence": {
                        "existing_tss_pr": True,
                        "existing_ti_pr": True,
                        "site_id": True,
                    },
                },
                {
                    "du_model_name": "2024 Celcomdigi BAU",
                    "source_file_name": "bau-2024.xlsx",
                    "profile_id": None,
                    "profile_status": None,
                    "profile_version": None,
                    "mapping_version": None,
                    "observed_header_hash": "hash-c",
                    "skill_field_presence": {
                        "existing_tss_pr": False,
                        "existing_ti_pr": False,
                        "site_id": True,
                        "subcon_planning": False,
                    },
                },
            ]
        }

        registry = build_coverage_registry(discovery_registry)
        self.assertEqual(registry["summary"]["total_exports"], 3)
        self.assertEqual(registry["summary"]["tracked_profile_exports"], 1)
        self.assertEqual(registry["summary"]["donor_review_candidates"], 1)
        self.assertEqual(registry["summary"]["backlog_discovery_only_exports"], 1)

        statuses = {entry["source_file_name"]: entry["coverage_status"] for entry in registry["entries"]}
        self.assertEqual(statuses["tx-mini.xlsx"], TRACKED_DRAFT_PROFILE)
        self.assertEqual(statuses["tx-rollout.xlsx"], DONOR_REVIEW_CANDIDATE)
        self.assertEqual(statuses["bau-2024.xlsx"], BACKLOG_DISCOVERY_ONLY)

    def test_markdown_mentions_coverage_status_and_next_action(self):
        registry = {
            "summary": {
                "total_exports": 1,
                "tracked_profile_exports": 1,
                "donor_review_candidates": 0,
                "backlog_discovery_only_exports": 0,
            },
            "entries": [
                {
                    "du_model_name": "TX Mini Project",
                    "source_file_name": "tx-mini.xlsx",
                    "coverage_status": TRACKED_DRAFT_PROFILE,
                    "profile_id": "tx_mini_pr_v1",
                    "profile_status": "DRAFT",
                    "profile_version": "0.1.0",
                    "mapping_version": "discovery-v1",
                    "observed_header_hash": "hash-a",
                    "missing_skill_fields": ["existing_tss_pr", "existing_ti_pr"],
                    "next_action": "Continue tracked profile review through the existing DRAFT discovery packet.",
                }
            ],
        }
        markdown = coverage_markdown(registry)
        self.assertIn("TRACKED_DRAFT_PROFILE", markdown)
        self.assertIn("tx_mini_pr_v1", markdown)
        self.assertIn("Continue tracked profile review", markdown)

    def test_write_outputs_creates_registry_and_markdown(self):
        discovery_registry = {
            "entries": [
                {
                    "du_model_name": "2023 TX Rollout",
                    "source_file_name": "tx-rollout.xlsx",
                    "profile_id": None,
                    "profile_status": None,
                    "profile_version": None,
                    "mapping_version": None,
                    "observed_header_hash": "hash-b",
                    "skill_field_presence": {
                        "existing_tss_pr": True,
                        "existing_ti_pr": True,
                    },
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            discovery_path = tmp_path / "discovery.json"
            registry_path = tmp_path / "coverage.json"
            markdown_path = tmp_path / "coverage.md"
            discovery_path.write_text(json.dumps(discovery_registry), encoding="utf-8")

            write_coverage_outputs(discovery_path, registry_path, markdown_path)

            written = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(written["entries"][0]["coverage_status"], DONOR_REVIEW_CANDIDATE)
            self.assertIn("DONOR_REVIEW_CANDIDATE", markdown_path.read_text(encoding="utf-8"))

    def test_generated_coverage_keeps_2023_celcomdigi_bau_tracked_without_pr_gaps(self):
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_export_coverage_review.yaml").read_text(encoding="utf-8")
        )
        entry = next(
            item
            for item in registry["entries"]
            if item["source_file_name"]
            == "A-P202202168750_D002-2023 Celcomdigi BAU-2023 Celcomdigi BAU_(TX_PRPO)-20260714150843.xlsx"
        )
        self.assertEqual(entry["coverage_status"], TRACKED_DRAFT_PROFILE)
        self.assertNotIn("existing_tss_pr", entry["missing_skill_fields"])
        self.assertNotIn("existing_ti_pr", entry["missing_skill_fields"])


if __name__ == "__main__":
    unittest.main()
