import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_missing_field_bridge_review import build_bridge_entry, build_bridge_registry, bridge_markdown


class TestMissingFieldBridgeReview(unittest.TestCase):
    def test_missing_jendela_migration_field_uses_discovery_presence_without_crashing(self):
        unresolved_entry = {
            "profile_id": "jendela_tx_migration_pr_v1",
            "profile_version": "0.4.0",
            "mapping_version": "approved-2026-08-11-jendela-tx-migration-v4",
            "observed_header_hash": "jendela-hash",
            "du_model_name": "Jendela TX Migration",
            "source_file_name": "jendela.xlsx",
            "summary": {"missing_required_fields": ["tx_before_migration", "final_backhaul"]},
        }
        grouping = {
            "entries": [
                {
                    "source_file_name": "jendela.xlsx",
                    "closest_neighbors": [],
                }
            ]
        }
        discovery = {
            "entries": [
                {
                    "du_model_name": "Jendela TX Migration",
                    "source_file_name": "jendela.xlsx",
                    "observed_header_hash": "jendela-hash",
                    "profile_id": "jendela_tx_migration_pr_v1",
                    "skill_field_presence": {
                        "tx_before_migration": True,
                        "final_backhaul": True,
                    },
                }
            ]
        }

        bridge_entry = build_bridge_entry(unresolved_entry, grouping, discovery)

        self.assertEqual(
            sorted(bridge_entry["field_bridges"]),
            ["final_backhaul", "tx_before_migration"],
        )

    def test_tx_mini_bridge_is_empty_after_approved_pr_status_mappings(self):
        # Since the 2026-07-07 approvals, TX Mini maps existing_*_pr_status from
        # its own export, so it no longer needs cross-model donor fields.
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        tx_entry = next(
            entry for entry in unresolved["entries"] if entry.get("profile_id") == "tx_mini_pr_v1"
        )
        bridge_entry = build_bridge_entry(tx_entry, grouping, discovery)

        self.assertEqual(bridge_entry["profile_id"], "tx_mini_pr_v1")
        self.assertEqual(bridge_entry["profile_version"], "0.2.0")
        self.assertEqual(bridge_entry["mapping_version"], "approved-2026-07-07-tx-mini-v1")
        self.assertEqual(
            bridge_entry["observed_header_hash"],
            "167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221",
        )
        self.assertEqual(bridge_entry["field_bridges"], {})

    def test_mw_eos_bridge_is_empty_after_approved_pr_status_mappings(self):
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        mw_entry = next(
            entry for entry in unresolved["entries"] if entry["profile_id"] == "mw_eos_swap_pr_v1"
        )
        bridge_entry = build_bridge_entry(mw_entry, grouping, discovery)

        self.assertEqual(bridge_entry["profile_id"], "mw_eos_swap_pr_v1")
        self.assertEqual(bridge_entry["profile_version"], "0.1.1")
        self.assertEqual(bridge_entry["mapping_version"], "approved-2026-07-10-mw-eos-swap-v2")
        self.assertEqual(bridge_entry["field_bridges"], {})

    def test_jendela_bridge_is_empty_after_approved_pr_status_mappings(self):
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        unresolved_entry = next(
            entry for entry in unresolved["entries"] if entry["profile_id"] == "jendela_tx_migration_pr_v1"
        )
        bridge_entry = build_bridge_entry(unresolved_entry, grouping, discovery)

        self.assertEqual(bridge_entry["profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(bridge_entry["profile_version"], "0.5.0")
        self.assertEqual(bridge_entry["mapping_version"], "approved-2026-08-11-jendela-tx-migration-v4")
        self.assertEqual(bridge_entry["field_bridges"], {})

    def test_zte_bridge_is_empty_after_local_pr_shortlist_candidates_are_detected(self):
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        zte_entry = next(entry for entry in unresolved["entries"] if entry["profile_id"] == "zte_tx_mini_pr_v1")
        bridge_entry = build_bridge_entry(zte_entry, grouping, discovery)

        self.assertEqual(bridge_entry["profile_id"], "zte_tx_mini_pr_v1")
        self.assertEqual(bridge_entry["profile_version"], "0.2.0")
        self.assertEqual(bridge_entry["mapping_version"], "approved-2026-07-15-zte-tx-mini-v1")
        self.assertEqual(bridge_entry["field_bridges"], {})

    def test_2023_celcomdigi_bau_bridge_stays_empty_after_pr_input_ready_approval(self):
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        unresolved_entry = next(
            entry for entry in unresolved["entries"] if entry["profile_id"] == "celcomdigi_bau_2023_pr_v1"
        )
        bridge_entry = build_bridge_entry(unresolved_entry, grouping, discovery)

        self.assertEqual(bridge_entry["profile_id"], "celcomdigi_bau_2023_pr_v1")
        self.assertEqual(bridge_entry["profile_version"], "0.2.0")
        self.assertEqual(bridge_entry["mapping_version"], "approved-2026-07-14-2023-celcomdigi-bau-tx-prpo-v1")
        self.assertEqual(bridge_entry["field_bridges"], {})

    def test_bridge_registry_carries_all_nine_profile_families(self):
        unresolved = json.loads(
            (ROOT / "config" / "registries" / "mw_du_unresolved_skill_field_review.yaml").read_text(encoding="utf-8")
        )
        grouping = json.loads(
            (ROOT / "config" / "registries" / "mw_du_structure_grouping_review.yaml").read_text(encoding="utf-8")
        )
        discovery = json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(encoding="utf-8")
        )

        registry = build_bridge_registry(unresolved, grouping, discovery)

        profile_ids = [entry["profile_id"] for entry in registry["entries"]]
        self.assertEqual(len(profile_ids), 9)
        self.assertEqual(
            set(profile_ids),
            {
                "celcomdigi_bau_2023_pr_v1",
                "celcomdigi_bau_2024_pr_v1",
                "celcomdigi_cd_consolidation_2023_pr_v1",
                "celcomdigi_usp_pr_v1",
                "jendela_tx_migration_pr_v1",
                "mw_eos_swap_pr_v1",
                "tx_mini_pr_v1",
                "tx_rollout_2023_pr_v1",
                "zte_tx_mini_pr_v1",
            },
        )

    def test_markdown_mentions_bridge_caution(self):
        registry = {
            "entries": [
                {
                    "profile_id": "tx_mini_pr_v1",
                    "profile_version": "0.1.0",
                    "mapping_version": "discovery-2026-07-06-tx-mini-v1",
                    "observed_header_hash": "hash-tx-mini",
                    "du_model_name": "TX Mini Project",
                    "field_bridges": {
                        "existing_tss_pr_status": {
                            "bridge_status": "CROSS_MODEL_REVIEW_REQUIRED",
                            "review_reason": "Another export carries the missing field, but cross-model reuse is not approved.",
                            "best_source_export": {
                                "du_model_name": "2023 TX Rollout",
                                "source_file_name": "rollout.xlsx",
                                "source_similarity_to_target": 0.858,
                            },
                        }
                    },
                }
            ]
        }

        markdown = bridge_markdown(registry)

        self.assertIn("CROSS_MODEL_REVIEW_REQUIRED", markdown)
        self.assertIn("2023 TX Rollout", markdown)
        self.assertIn("0.858", markdown)
        self.assertIn("hash-tx-mini", markdown)


if __name__ == "__main__":
    unittest.main()
