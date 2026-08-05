import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_profile_status_consistency import validate_profile_status_consistency, validate_profiles_against_transition_registry
from du_profile_loader import ProfileValidationError, load_du_profile


class TestProfileStatusConsistency(unittest.TestCase):
    def test_current_draft_profiles_pass_consistency_check(self):
        validate_profiles_against_transition_registry(
            [
                ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml",
                ROOT / "config" / "du_profiles" / "mw_eos_swap_pr_v1.yaml",
                ROOT / "config" / "du_profiles" / "zte_tx_mini_pr_v1.yaml",
            ],
            ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml",
        )

    def test_tx_mini_production_status_is_permitted_by_transition_review(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        registry = json.loads(
            (ROOT / "config" / "registries" / "mw_du_profile_transition_review.yaml").read_text(encoding="utf-8")
        )
        transition_entry = next(entry for entry in registry["entries"] if entry["profile_id"] == "tx_mini_pr_v1")
        validate_profile_status_consistency(profile, transition_entry)
        production = next(
            target for target in transition_entry["transition_targets"]
            if target["target_status"] == "PRODUCTION"
        )
        self.assertTrue(production["eligible"])
        self.assertEqual(production["denied_reasons"], [])

    def test_missing_transition_entry_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            registry_path.write_text(json.dumps({"entries": []}), encoding="utf-8")
            with self.assertRaises(ProfileValidationError):
                validate_profiles_against_transition_registry(
                    [ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml"],
                    registry_path,
                )

    def test_deprecated_profile_requires_recorded_deprecation_review(self):
        profile = load_du_profile(ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml")
        profile["status"] = "DEPRECATED"
        profile["deprecation"] = {
            "reason": "Superseded by successor profile.",
            "successor_profile_id": "tx_mini_pr_v2",
            "successor_profile_version": "0.2.0",
            "rollback_profile_id": "tx_mini_pr_v1",
            "rollback_profile_version": "0.1.0",
            "superseded_header_hashes": [profile["export_structure"]["observed_header_hash"]],
        }
        transition_entry = {
            "transition_targets": [
                {"target_status": "PRODUCTION", "eligible": True, "denied_reasons": []},
            ]
        }
        deprecation_entry = {
            "profile_id": "tx_mini_pr_v1",
            "deprecation_status": "DEPRECATION_DENIED",
            "blockers": ["NO_SUCCESSOR_PROFILE"],
        }

        with self.assertRaises(ProfileValidationError) as error:
            validate_profile_status_consistency(profile, transition_entry, deprecation_entry)

        self.assertIn("DEPRECATED", str(error.exception))
        self.assertIn("deprecation review", str(error.exception).lower())


if __name__ == "__main__":
    unittest.main()
