import json
import unittest
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "config" / "du_profiles"
REGISTRY_PATH = ROOT / "config" / "registries" / "mw_du_profile_identity_registry.yaml"

ALLOWED_NAME_STATUSES = {
    "STANDARD",
    "LEGACY_ACCEPTED",
    "CONSOLIDATION_REVIEW_REQUIRED",
}


def load_json_mapping(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def load_profiles(profile_dir: Path = PROFILE_DIR) -> dict[str, dict]:
    profiles = {}
    for path in sorted(profile_dir.glob("*.yaml")):
        profile = load_json_mapping(path)
        profile_id = profile["profile_id"]
        if profile_id in profiles:
            raise AssertionError(f"duplicate profile_id: {profile_id}")
        profiles[profile_id] = profile
    return profiles


def identity_key(profile: dict) -> str:
    identity = profile["identity"]
    model_ids = identity["accepted_du_model_ids"]
    if len(model_ids) != 1:
        raise AssertionError(f"{profile['profile_id']} must register exactly one DU model ID")
    return f"{identity['project_key']}::{model_ids[0]}"


def _single(values: list[str], field_name: str, profile_id: str) -> str:
    if len(values) != 1:
        raise AssertionError(f"{profile_id} must register exactly one {field_name}")
    return values[0]


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_identity_governance(profiles: dict[str, dict], registry: dict) -> list[str]:
    errors: list[str] = []
    registry_records = registry.get("profiles", [])
    if not isinstance(registry_records, list):
        raise AssertionError("registry.profiles must be a list")

    records_by_id: dict[str, dict] = {}
    for record in registry_records:
        if not isinstance(record, dict):
            raise AssertionError("every registry profile record must be an object")
        profile_id = record.get("profile_id")
        if not isinstance(profile_id, str) or not profile_id:
            raise AssertionError("every registry profile record requires profile_id")
        if profile_id in records_by_id:
            raise AssertionError(f"duplicate registry profile_id: {profile_id}")
        records_by_id[profile_id] = record

    profile_ids = set(profiles)
    registry_ids = set(records_by_id)
    for profile_id in sorted(profile_ids - registry_ids):
        errors.append(f"UNREGISTERED_DU_PROFILE:{profile_id}")
    for profile_id in sorted(registry_ids - profile_ids):
        errors.append(f"STALE_PROFILE_REGISTRY_RECORD:{profile_id}")

    for profile_id in sorted(profile_ids & registry_ids):
        profile = profiles[profile_id]
        record = records_by_id[profile_id]
        identity = profile["identity"]
        du_model_name = _single(identity["accepted_du_models"], "DU model name", profile_id)
        du_model_id = _single(identity["accepted_du_model_ids"], "DU model ID", profile_id)
        expected_identity_key = identity_key(profile)

        identity_matches = (
            record.get("project_key") == identity.get("project_key")
            and record.get("du_model_name") == du_model_name
            and str(record.get("du_model_id")) == str(du_model_id)
            and record.get("identity_key") == expected_identity_key
            and record.get("accepted_view_ids") == identity.get("accepted_view_ids")
        )
        if not identity_matches:
            errors.append(f"PROFILE_IDENTITY_MISMATCH:{profile_id}")

        if record.get("profile_status") != profile.get("status"):
            errors.append(f"PROFILE_STATUS_MISMATCH:{profile_id}")

        name_status = record.get("name_status")
        if name_status not in ALLOWED_NAME_STATUSES:
            errors.append(f"NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:{profile_id}")
        elif name_status == "STANDARD":
            if record.get("canonical_profile_id") != profile_id:
                errors.append(f"NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:{profile_id}")
        elif name_status == "LEGACY_ACCEPTED":
            if not _nonblank(record.get("reason")):
                errors.append(f"LEGACY_PROFILE_WITHOUT_REASON:{profile_id}")
        elif name_status == "CONSOLIDATION_REVIEW_REQUIRED":
            if not _nonblank(record.get("reason")):
                errors.append(f"CONSOLIDATION_REVIEW_WITHOUT_REASON:{profile_id}")

    profiles_by_identity: dict[str, set[str]] = defaultdict(set)
    for profile_id, profile in profiles.items():
        profiles_by_identity[identity_key(profile)].add(profile_id)

    review_records = registry.get("identity_reviews", [])
    if not isinstance(review_records, list):
        raise AssertionError("registry.identity_reviews must be a list")
    reviews_by_identity = {}
    for review in review_records:
        if not isinstance(review, dict):
            raise AssertionError("every identity review must be an object")
        key = review.get("identity_key")
        if not isinstance(key, str) or not key:
            raise AssertionError("every identity review requires identity_key")
        if key in reviews_by_identity:
            raise AssertionError(f"duplicate identity review: {key}")
        reviews_by_identity[key] = review

    for key, duplicate_profile_ids in sorted(profiles_by_identity.items()):
        if len(duplicate_profile_ids) <= 1:
            continue
        review = reviews_by_identity.get(key)
        if review is None:
            errors.append(f"DUPLICATE_PROFILE_IDENTITY:{key}")
            continue
        permitted = review.get("permitted_profile_ids", [])
        if (
            review.get("status") != "CONSOLIDATION_REVIEW_REQUIRED"
            or set(permitted) != duplicate_profile_ids
            or not _nonblank(review.get("reason"))
        ):
            errors.append(f"DUPLICATE_IDENTITY_SET_MISMATCH:{key}")

    return sorted(set(errors))


class TestDuProfileIdentityGovernance(unittest.TestCase):
    def setUp(self):
        self.profiles = load_profiles()
        self.registry = load_json_mapping(REGISTRY_PATH)

    def test_current_repository_is_governed(self):
        self.assertEqual(validate_identity_governance(self.profiles, self.registry), [])

    def test_unregistered_profile_fails(self):
        registry = deepcopy(self.registry)
        registry["profiles"] = [
            record for record in registry["profiles"] if record["profile_id"] != "tx_mini_pr_v1"
        ]
        self.assertIn(
            "UNREGISTERED_DU_PROFILE:tx_mini_pr_v1",
            validate_identity_governance(self.profiles, registry),
        )

    def test_unapproved_duplicate_identity_fails(self):
        profiles = deepcopy(self.profiles)
        duplicate = deepcopy(profiles["jendela_tx_migration_pr_v1"])
        duplicate["profile_id"] = "jendela_tx_migration_duplicate_pr_v1"
        profiles[duplicate["profile_id"]] = duplicate

        registry = deepcopy(self.registry)
        source_record = next(
            record
            for record in registry["profiles"]
            if record["profile_id"] == "jendela_tx_migration_pr_v1"
        )
        duplicate_record = deepcopy(source_record)
        duplicate_record.update(
            {
                "profile_id": duplicate["profile_id"],
                "canonical_profile_id": "celcomdigi_jendela_tx_migration_pr_v1",
                "name_status": "LEGACY_ACCEPTED",
                "reason": "Negative-test duplicate.",
            }
        )
        registry["profiles"].append(duplicate_record)

        key = identity_key(duplicate)
        self.assertIn(
            f"DUPLICATE_PROFILE_IDENTITY:{key}",
            validate_identity_governance(profiles, registry),
        )

    def test_third_cd_consolidation_profile_fails(self):
        profiles = deepcopy(self.profiles)
        third = deepcopy(profiles["cd_consolidation_2023_decom_pr_v1"])
        third["profile_id"] = "cd_consolidation_2023_third_view_pr_v1"
        profiles[third["profile_id"]] = third

        registry = deepcopy(self.registry)
        source_record = next(
            record
            for record in registry["profiles"]
            if record["profile_id"] == "cd_consolidation_2023_decom_pr_v1"
        )
        third_record = deepcopy(source_record)
        third_record.update(
            {
                "profile_id": third["profile_id"],
                "accepted_view_ids": third["identity"]["accepted_view_ids"],
                "reason": "Negative-test third view.",
            }
        )
        registry["profiles"].append(third_record)

        key = identity_key(third)
        self.assertIn(
            f"DUPLICATE_IDENTITY_SET_MISMATCH:{key}",
            validate_identity_governance(profiles, registry),
        )

    def test_standard_record_with_noncanonical_id_fails(self):
        registry = deepcopy(self.registry)
        record = next(
            item for item in registry["profiles"] if item["profile_id"] == "mw_eos_swap_pr_v1"
        )
        record["canonical_profile_id"] = "mw_eos_swap_wrong_pr_v1"
        self.assertIn(
            "NONSTANDARD_PROFILE_ID_WITHOUT_EXCEPTION:mw_eos_swap_pr_v1",
            validate_identity_governance(self.profiles, registry),
        )

    def test_legacy_record_without_reason_fails(self):
        registry = deepcopy(self.registry)
        record = next(
            item for item in registry["profiles"] if item["profile_id"] == "tx_mini_pr_v1"
        )
        record["reason"] = ""
        self.assertIn(
            "LEGACY_PROFILE_WITHOUT_REASON:tx_mini_pr_v1",
            validate_identity_governance(self.profiles, registry),
        )

    def test_tx_mini_profiles_are_distinct_identities(self):
        self.assertNotEqual(
            identity_key(self.profiles["tx_mini_pr_v1"]),
            identity_key(self.profiles["zte_tx_mini_pr_v1"]),
        )

    def test_profile_lifecycle_statuses_are_unchanged(self):
        expected = {
            "tx_mini_pr_v1": "PR_INPUT_READY",
            "tx_rollout_2023_pr_v1": "PR_INPUT_READY",
            "mw_eos_swap_pr_v1": "PR_INPUT_READY",
            "celcomdigi_bau_2023_pr_v1": "PR_INPUT_READY",
            "celcomdigi_bau_2024_pr_v1": "PR_INPUT_READY",
            "celcomdigi_usp_pr_v1": "PR_INPUT_READY",
            "jendela_tx_migration_pr_v1": "PR_INPUT_READY",
            "zte_tx_mini_pr_v1": "PR_INPUT_READY",
            "cd_consolidation_2023_decom_pr_v1": "DRAFT",
            "cd_consolidation_2023_rollout_pr_v1": "DRAFT",
        }
        actual = {profile_id: profile["status"] for profile_id, profile in self.profiles.items()}
        self.assertEqual(actual, expected)
        self.assertNotIn("PRODUCTION", actual.values())

    def test_2023_celcomdigi_bau_identity_uses_corrected_tx_prpo_view(self):
        record = next(
            item for item in self.registry["profiles"] if item["profile_id"] == "celcomdigi_bau_2023_pr_v1"
        )
        self.assertEqual(record["profile_status"], "PR_INPUT_READY")
        self.assertEqual(record["accepted_view_ids"], ["3882899459299681347"])
        self.assertNotIn("6611960521271999255", record["accepted_view_ids"])


if __name__ == "__main__":
    unittest.main()
