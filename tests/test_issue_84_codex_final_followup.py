import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_profile_rollback_readiness import build_rollback_registry, rollback_markdown
from du_profile_loader import load_du_profile
from jendela_migration_decision import parse_jendela_before_mw_antenna_size


class TestIssue84CodexFinalFollowup(unittest.TestCase):
    def _profile_and_source(self):
        profile = load_du_profile(
            ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"
        )
        source = json.loads(
            (
                ROOT
                / "config"
                / "registries"
                / "mw_du_profile_rollback_baselines_source.yaml"
            ).read_text(encoding="utf-8")
        )
        return profile, source

    def test_parser_includes_larger_supported_standalone_candidate_outside_link(self):
        for raw in (
            "2.4 / 18G 1.2 1+0",
            "18G 1.2 1+0 / 2.4",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(parse_jendela_before_mw_antenna_size(raw), 2.4)

    def test_parser_accepts_underscore_delimited_mw_config(self):
        cases = {
            "18G_1.2M_SP_1+0": 1.2,
            "18GHz_0.6_DP_1+0": 0.6,
            "18G_0.6_SP_1+0_/_23G_1.2_SP_1+0": 1.2,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_jendela_before_mw_antenna_size(raw), expected)

    def test_parser_accepts_documented_mac_omt_mw_config(self):
        cases = {
            "18G_1.2M(MAC)+OMT x1": 1.2,
            "18GHz_0.6M(MAC)+OMT x1": 0.6,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_jendela_before_mw_antenna_size(raw), expected)

    def test_duplicate_unknown_rollback_profile_id_blocks_registry_globally(self):
        profile, source = self._profile_and_source()
        stale_entry = {
            "profile_id": "stale_profile_typo",
            "current_profile_version": "9.9.9",
            "rollback_profile_id": "stale_profile_typo",
            "rollback_profile_version": "9.9.8",
            "rollback_header_hashes": ["stale-hash"],
        }
        source["entries"].extend([dict(stale_entry), dict(stale_entry)])

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("DUPLICATE_ROLLBACK_BASELINE_ENTRIES", entry["blockers"])
        self.assertIn("stale_profile_typo", registry["duplicate_rollback_profile_ids"])

    def test_null_rollback_header_hashes_fail_closed_without_crashing(self):
        profile, source = self._profile_and_source()
        for entry in source["entries"]:
            if entry.get("profile_id") == "jendela_tx_migration_pr_v1":
                entry["rollback_header_hashes"] = None
                break

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_HEADER_HASHES_INVALID", entry["blockers"])
        self.assertEqual(entry["rollback_target_header_hashes"], [])

    def test_malformed_rollback_header_hash_member_fails_closed_and_renders(self):
        profile, source = self._profile_and_source()
        source["entries"][0]["rollback_header_hashes"] = [None]

        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]

        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_HEADER_HASHES_INVALID", entry["blockers"])
        self.assertEqual(entry["rollback_target_header_hashes"], [])
        self.assertIn("ROLLBACK_BLOCKED", rollback_markdown(registry))

    def test_null_rollback_source_collections_fail_closed_without_crashing(self):
        profile, source = self._profile_and_source()
        for collection_name in ("entries", "required_profile_ids"):
            malformed = json.loads(json.dumps(source))
            malformed[collection_name] = None
            with self.subTest(collection_name=collection_name):
                registry = build_rollback_registry([profile], {"entries": []}, malformed)
                entry = registry["entries"][0]
                self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
                self.assertIn(
                    "ROLLBACK_BASELINE_SOURCE_COLLECTION_INVALID",
                    entry["blockers"],
                )
                self.assertIn(
                    collection_name,
                    registry["invalid_rollback_source_collections"],
                )

    def test_malformed_rollback_source_entry_blocks_registry_globally(self):
        profile, source = self._profile_and_source()
        for malformed_entry in (None, {}, {"current_profile_version": "0.5.0"}):
            malformed = json.loads(json.dumps(source))
            malformed["entries"].append(malformed_entry)
            with self.subTest(malformed_entry=malformed_entry):
                registry = build_rollback_registry([profile], {"entries": []}, malformed)
                entry = registry["entries"][0]
                self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
                self.assertIn("ROLLBACK_BASELINE_SOURCE_ENTRY_INVALID", entry["blockers"])
                self.assertTrue(registry["invalid_rollback_source_entry_indexes"])

    def test_governed_jendela_rollback_has_resolvable_immutable_artifact(self):
        profile, source = self._profile_and_source()
        source_entry = source["entries"][0]
        artifact_path = ROOT / source_entry["rollback_profile_artifact_path"]
        self.assertTrue(artifact_path.is_file())

        artifact_bytes = artifact_path.read_bytes()
        git_blob_sha = hashlib.sha1(
            f"blob {len(artifact_bytes)}\0".encode("ascii") + artifact_bytes
        ).hexdigest()
        self.assertEqual(git_blob_sha, source_entry["rollback_profile_blob_sha"])
        self.assertEqual(
            source_entry["rollback_source_commit_sha"],
            "6f0253edad2a4bb3abfef838e918379110bbd046",
        )

        archived = json.loads(artifact_bytes.decode("utf-8"))
        self.assertEqual(archived["profile_id"], "jendela_tx_migration_pr_v1")
        self.assertEqual(archived["profile_version"], "0.4.0")
        self.assertEqual(
            archived["mapping_version"],
            "approved-2026-08-04-jendela-tx-migration-v3",
        )
        self.assertEqual(
            archived["export_structure"]["observed_header_hash"],
            source_entry["rollback_header_hashes"][0],
        )

        registry = build_rollback_registry([profile], {"entries": []}, source)
        self.assertEqual(
            registry["entries"][0]["rollback_readiness_status"],
            "ROLLBACK_BASELINE_RECORDED",
        )

    def test_governed_jendela_rollback_blocks_artifact_identity_drift(self):
        profile, source = self._profile_and_source()
        source["entries"][0]["rollback_profile_blob_sha"] = "0" * 40
        registry = build_rollback_registry([profile], {"entries": []}, source)
        entry = registry["entries"][0]
        self.assertEqual(entry["rollback_readiness_status"], "ROLLBACK_BLOCKED")
        self.assertIn("ROLLBACK_PROFILE_ARTIFACT_BLOB_MISMATCH", entry["blockers"])


if __name__ == "__main__":
    unittest.main()
