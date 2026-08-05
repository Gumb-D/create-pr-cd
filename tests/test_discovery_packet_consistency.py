import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_discovery_packet_consistency import validate_discovery_packet_consistency, validate_live_discovery_packets
from du_profile_loader import ProfileValidationError, load_du_profile


class TestDiscoveryPacketConsistency(unittest.TestCase):
    def _profiles(self):
        return [
            load_du_profile(path)
            for path in sorted((ROOT / "config" / "du_profiles").glob("*.yaml"))
        ]

    def _registry(self, name):
        return json.loads((ROOT / "config" / "registries" / name).read_text(encoding="utf-8"))

    def test_live_discovery_packets_are_consistent(self):
        validate_live_discovery_packets()

    def test_readiness_mapping_version_mismatch_fails_closed(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(readiness)
        broken["entries"][0]["mapping_version"] = "wrong-version"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                broken,
                transition,
                bridge,
                deprecation,
                traceability,
                rollback,
                coverage,
            )

        self.assertIn("mapping-version mismatch", str(error.exception))

    def test_bridge_fields_must_match_unresolved_missing_fields(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(bridge)
        # Use a profile that still needs cross-model donor fields; TX Mini's
        # bridge is empty since its PR-status mappings were approved.
        bridged_entry = next(
            entry for entry in broken["entries"] if "existing_ti_pr_status" in entry.get("field_bridges", {})
        )
        del bridged_entry["field_bridges"]["existing_ti_pr_status"]

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                broken,
                deprecation,
                traceability,
                rollback,
                coverage,
            )

        self.assertIn("Bridge review field mismatch", str(error.exception))

    def test_deprecation_review_status_must_match_profile_status(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(deprecation)
        broken["entries"][0]["current_status"] = "DEPRECATED"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                broken,
                traceability,
                rollback,
                coverage,
            )

        self.assertIn("Deprecation review status mismatch", str(error.exception))

    def test_bridge_traceability_fields_must_match_profile(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(bridge)
        broken["entries"][0]["profile_version"] = "9.9.9"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                broken,
                deprecation,
                traceability,
                rollback,
                coverage,
            )

        self.assertIn("Bridge review profile-version mismatch", str(error.exception))

    def test_rollback_review_header_hash_must_match_profile(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(rollback)
        broken["entries"][0]["observed_header_hash"] = "wrong-header-hash"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                deprecation,
                traceability,
                broken,
                coverage,
            )

        self.assertIn("Rollback review header-hash mismatch", str(error.exception))

    def test_traceability_audit_status_must_match_profile(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(traceability)
        broken["entries"][0]["traceability_status"] = "TRACEABILITY_REVIEW_REQUIRED"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                deprecation,
                broken,
                rollback,
                coverage,
            )

        self.assertIn("Traceability audit status mismatch", str(error.exception))

    def test_traceability_audit_must_cover_expected_artifacts(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(traceability)
        broken["entries"][0]["artifacts"] = [
            artifact
            for artifact in broken["entries"][0]["artifacts"]
            if artifact["artifact_id"] != "coverage"
        ]

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                deprecation,
                broken,
                rollback,
                coverage,
            )

        self.assertIn("Traceability audit artifact coverage mismatch", str(error.exception))

    def test_coverage_review_tracked_profile_must_match_discovery_registry(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(coverage)
        tracked_entry = next(
            entry for entry in broken["entries"] if entry.get("profile_id") == "tx_mini_pr_v1"
        )
        tracked_entry["profile_id"] = None

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                deprecation,
                traceability,
                rollback,
                broken,
            )

        self.assertIn("Coverage review tracked-profile mismatch", str(error.exception))

    def test_coverage_review_donor_status_must_match_discovery_registry(self):
        profiles = [
            profile for profile in self._profiles()
            if profile["profile_id"] != "celcomdigi_cd_consolidation_2023_pr_v1"
        ]
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        discovery_broken = copy.deepcopy(discovery)
        broken = copy.deepcopy(self._registry("mw_du_export_coverage_review.yaml"))

        source_names = []
        for entry in discovery_broken["entries"]:
            if entry.get("profile_id") != "celcomdigi_cd_consolidation_2023_pr_v1":
                continue
            source_names.append(entry["source_file_name"])
            entry["profile_id"] = None
            entry["profile_status"] = None
            entry["profile_version"] = None
            entry["mapping_version"] = None
        for entry in broken["entries"]:
            if entry.get("source_file_name") not in source_names:
                continue
            entry["profile_id"] = None
            entry["profile_status"] = None
            entry["profile_version"] = None
            entry["mapping_version"] = None
            entry["coverage_status"] = "BACKLOG_DISCOVERY_ONLY"
        next(entry for entry in broken["entries"] if entry.get("source_file_name") == source_names[0])["coverage_status"] = "DONOR_REVIEW_CANDIDATE"

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles, discovery_broken, unresolved, readiness, transition,
                bridge, deprecation, traceability, rollback, broken,
            )

        self.assertIn("Coverage review donor/backlog mismatch", str(error.exception))

    def test_coverage_review_summary_counts_must_match_entries(self):
        profiles = self._profiles()
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        coverage = self._registry("mw_du_export_coverage_review.yaml")
        broken = copy.deepcopy(coverage)
        broken["summary"]["donor_review_candidates"] = 99

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles,
                discovery,
                unresolved,
                readiness,
                transition,
                bridge,
                deprecation,
                traceability,
                rollback,
                broken,
            )

        self.assertIn("Coverage review summary mismatch", str(error.exception))

    def test_coverage_review_missing_skill_fields_must_match_discovery_registry(self):
        profiles = [
            profile for profile in self._profiles()
            if profile["profile_id"] != "celcomdigi_cd_consolidation_2023_pr_v1"
        ]
        discovery = self._registry("mw_du_model_discovery_registry.yaml")
        unresolved = self._registry("mw_du_unresolved_skill_field_review.yaml")
        readiness = self._registry("mw_du_profile_readiness_review.yaml")
        transition = self._registry("mw_du_profile_transition_review.yaml")
        bridge = self._registry("mw_du_missing_field_bridge_review.yaml")
        deprecation = self._registry("mw_du_profile_deprecation_review.yaml")
        traceability = self._registry("mw_du_profile_traceability_audit.yaml")
        rollback = self._registry("mw_du_profile_rollback_readiness.yaml")
        discovery_broken = copy.deepcopy(discovery)
        broken = copy.deepcopy(self._registry("mw_du_export_coverage_review.yaml"))

        source_names = []
        for entry in discovery_broken["entries"]:
            if entry.get("profile_id") != "celcomdigi_cd_consolidation_2023_pr_v1":
                continue
            source_names.append(entry["source_file_name"])
            entry["profile_id"] = None
            entry["profile_status"] = None
            entry["profile_version"] = None
            entry["mapping_version"] = None
        for entry in broken["entries"]:
            if entry.get("source_file_name") not in source_names:
                continue
            entry["profile_id"] = None
            entry["profile_status"] = None
            entry["profile_version"] = None
            entry["mapping_version"] = None
            entry["coverage_status"] = "BACKLOG_DISCOVERY_ONLY"
        next(entry for entry in broken["entries"] if entry.get("source_file_name") == source_names[0])["missing_skill_fields"] = []

        with self.assertRaises(ProfileValidationError) as error:
            validate_discovery_packet_consistency(
                profiles, discovery_broken, unresolved, readiness, transition,
                bridge, deprecation, traceability, rollback, broken,
            )

        self.assertIn("Coverage review missing-skill-fields mismatch", str(error.exception))


if __name__ == "__main__":
    unittest.main()
