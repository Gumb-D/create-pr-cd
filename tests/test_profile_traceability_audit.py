import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_traceability_audit import build_traceability_registry, traceability_markdown
from du_profile_loader import load_du_profile


class TestProfileTraceabilityAudit(unittest.TestCase):
    def _profiles(self):
        return [
            load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml"),
            load_du_profile(ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml"),
            load_du_profile(ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml"),
        ]

    def _registry(self, name):
        return json.loads((ROOT / "config" / "registries" / name).read_text(encoding="utf-8"))

    def test_traceability_registry_marks_profile_artifacts_traceable(self):
        registry = build_traceability_registry(
            self._profiles(),
            {
                "discovery": self._registry("mw_du_model_discovery_registry.yaml"),
                "unresolved": self._registry("mw_du_unresolved_skill_field_review.yaml"),
                "bridge": self._registry("mw_du_missing_field_bridge_review.yaml"),
                "readiness": self._registry("mw_du_profile_readiness_review.yaml"),
                "action_queue": self._registry("mw_du_profile_action_queue.yaml"),
                "review_matrix": self._registry("mw_du_profile_review_matrix.yaml"),
                "coverage": self._registry("mw_du_export_coverage_review.yaml"),
                "transition": self._registry("mw_du_profile_transition_review.yaml"),
                "deprecation": self._registry("mw_du_profile_deprecation_review.yaml"),
                "rollback": self._registry("mw_du_profile_rollback_readiness.yaml"),
            },
        )

        tx_entry = next(entry for entry in registry["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        self.assertEqual(tx_entry["traceability_status"], "TRACEABLE")
        discovery = next(item for item in tx_entry["artifacts"] if item["artifact_id"] == "discovery")
        coverage = next(item for item in tx_entry["artifacts"] if item["artifact_id"] == "coverage")
        rollback = next(item for item in tx_entry["artifacts"] if item["artifact_id"] == "rollback")
        self.assertTrue(discovery["profile_version_matches"])
        self.assertTrue(discovery["observed_header_hash_matches"])
        self.assertTrue(coverage["profile_version_matches"])
        self.assertTrue(rollback["profile_version_matches"])

    def test_traceability_registry_flags_mismatch(self):
        profiles = self._profiles()
        registries = {
            "discovery": self._registry("mw_du_model_discovery_registry.yaml"),
            "unresolved": self._registry("mw_du_unresolved_skill_field_review.yaml"),
            "bridge": self._registry("mw_du_missing_field_bridge_review.yaml"),
            "readiness": self._registry("mw_du_profile_readiness_review.yaml"),
            "action_queue": self._registry("mw_du_profile_action_queue.yaml"),
            "review_matrix": self._registry("mw_du_profile_review_matrix.yaml"),
            "coverage": self._registry("mw_du_export_coverage_review.yaml"),
            "transition": self._registry("mw_du_profile_transition_review.yaml"),
            "deprecation": self._registry("mw_du_profile_deprecation_review.yaml"),
            "rollback": self._registry("mw_du_profile_rollback_readiness.yaml"),
        }
        registries["bridge"] = json.loads(json.dumps(registries["bridge"]))
        next(
            entry for entry in registries["bridge"]["entries"] if entry["profile_id"] == "tx_mini_pr_v1"
        )["observed_header_hash"] = "wrong-hash"

        registry = build_traceability_registry(profiles, registries)

        tx_entry = next(entry for entry in registry["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        self.assertEqual(tx_entry["traceability_status"], "TRACEABILITY_REVIEW_REQUIRED")
        bridge = next(item for item in tx_entry["artifacts"] if item["artifact_id"] == "bridge")
        self.assertFalse(bridge["observed_header_hash_matches"])

    def test_markdown_mentions_traceability_status(self):
        registry = build_traceability_registry(
            self._profiles(),
            {
                "discovery": self._registry("mw_du_model_discovery_registry.yaml"),
                "unresolved": self._registry("mw_du_unresolved_skill_field_review.yaml"),
                "bridge": self._registry("mw_du_missing_field_bridge_review.yaml"),
                "readiness": self._registry("mw_du_profile_readiness_review.yaml"),
                "action_queue": self._registry("mw_du_profile_action_queue.yaml"),
                "review_matrix": self._registry("mw_du_profile_review_matrix.yaml"),
                "coverage": self._registry("mw_du_export_coverage_review.yaml"),
                "transition": self._registry("mw_du_profile_transition_review.yaml"),
                "deprecation": self._registry("mw_du_profile_deprecation_review.yaml"),
                "rollback": self._registry("mw_du_profile_rollback_readiness.yaml"),
            },
        )

        markdown = traceability_markdown(registry)
        self.assertIn("# MW DU Profile Traceability Audit", markdown)
        self.assertIn("TRACEABLE", markdown)
        self.assertIn("tx_mini_pr_v1", markdown)


if __name__ == "__main__":
    unittest.main()
