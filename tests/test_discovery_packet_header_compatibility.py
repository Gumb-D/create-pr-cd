import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_discovery_packet_consistency import _packet_compatible_profiles
from du_profile_loader import ProfileValidationError, load_du_profile


class TestDiscoveryPacketHeaderCompatibility(unittest.TestCase):
    def _registry(self):
        return json.loads(
            (ROOT / "config" / "registries" / "mw_du_model_discovery_registry.yaml").read_text(
                encoding="utf-8"
            )
        )

    def test_historical_tx_rollout_hash_remains_valid_when_still_approved(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")
        registry = self._registry()
        compatible = _packet_compatible_profiles([profile], registry)

        self.assertEqual(len(compatible), 1)
        self.assertEqual(
            compatible[0]["export_structure"]["observed_header_hash"],
            profile["export_structure"]["observed_header_hash"],
        )
        self.assertEqual(compatible[0]["profile_version"], profile["profile_version"])

        historical = next(
            item for item in registry["entries"] if item.get("profile_id") == "tx_rollout_2023_pr_v1"
        )
        historical_hash = "8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320"
        self.assertEqual(historical["observed_header_hash"], historical_hash)
        self.assertIn(historical_hash, profile["export_structure"]["approved_header_hashes"])
        self.assertEqual(profile["profile_version"], "0.1.1")

    def test_unapproved_historical_hash_fails_closed(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_rollout_2023_pr_v1.yaml")
        registry = copy.deepcopy(self._registry())
        entry = next(
            item for item in registry["entries"] if item.get("profile_id") == "tx_rollout_2023_pr_v1"
        )
        entry["observed_header_hash"] = "unapproved-hash"
        with self.assertRaises(ProfileValidationError) as context:
            _packet_compatible_profiles([profile], registry)
        self.assertIn("not registered as observed or approved", str(context.exception))

    def test_unchanged_draft_hash_does_not_require_approval(self):
        profile = load_du_profile(
            ROOT / "config" / "du_profiles" / "celcomdigi_cd_consolidation_2023_pr_v1.yaml"
        )
        self.assertEqual(profile["export_structure"]["approved_header_hashes"], [])
        compatible = _packet_compatible_profiles([profile], self._registry())
        self.assertEqual(
            compatible[0]["export_structure"]["observed_header_hash"],
            profile["export_structure"]["observed_header_hash"],
        )
        self.assertEqual(compatible[0]["profile_version"], profile["profile_version"])
        self.assertEqual(
            set(compatible[0]["export_structure"]["observed_header_hashes"]),
            {
                "b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16",
                "d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1",
            },
        )


if __name__ == "__main__":
    unittest.main()
