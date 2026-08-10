import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sow_normalization import (
    CLASSIFICATION_MISSING,
    CLASSIFICATION_NO_PR_TRIGGER,
    CLASSIFICATION_PR_TRIGGER,
    CLASSIFICATION_REVIEW_REQUIRED,
    DEFAULT_REGISTRY_PATH,
    load_canonical_sow_registry,
    normalize_tx_sow,
)

LIVE_REGISTRY_PATH = ROOT / DEFAULT_REGISTRY_PATH

EXPECTED_PR_TRIGGER_VALUES = {
    "MW Swap",
    "MW New Link / Reroute",
    "MW Parallel Link",
    "MW IDU Patching",
    "MW Re-engineering",
    "MW Hardware Upgrade",
    "IDU-IPRAN",
    "BBU Patching",
    "MW IDU Relocation",
    "IPRAN Port Upgrade",
    "MW Dismantle",
    "Decom - Relo",
}


class TestLiveRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = load_canonical_sow_registry(LIVE_REGISTRY_PATH)

    def test_registry_covers_all_seventeen_observed_values(self):
        self.assertEqual(len(self.registry["entries"]), 17)

    def test_twelve_pr_trigger_values_use_identity_normalization(self):
        triggers = {
            e["raw_value"]: e
            for e in self.registry["entries"]
            if e["classification"] == CLASSIFICATION_PR_TRIGGER
        }
        self.assertEqual(set(triggers), EXPECTED_PR_TRIGGER_VALUES)
        for entry in triggers.values():
            self.assertEqual(entry["canonical_sow"], " ".join(entry["raw_value"].split()).upper())

    def test_decom_relo_is_independent_approved_pr_trigger(self):
        result = normalize_tx_sow("Decom - Relo", self.registry)
        self.assertEqual(result["canonical_sow"], "DECOM - RELO")
        self.assertEqual(result["classification"], CLASSIFICATION_PR_TRIGGER)
        self.assertEqual(result["normalization_status"], "APPROVED")

    def test_cancel_drop_is_intentional_no_pr_trigger(self):
        result = normalize_tx_sow("Cancel / Drop", self.registry)
        self.assertEqual(result["classification"], CLASSIFICATION_NO_PR_TRIGGER)
        self.assertEqual(result["normalization_status"], "APPROVED_NO_OUTPUT")

    def test_unmatched_model_values_are_review_required(self):
        for raw in ("MW Remote Upgrade", "New Starlink", "Under NIC", "Existing TX"):
            result = normalize_tx_sow(raw, self.registry)
            self.assertEqual(result["classification"], CLASSIFICATION_REVIEW_REQUIRED, raw)
            self.assertEqual(result["normalization_status"], CLASSIFICATION_REVIEW_REQUIRED, raw)

    def test_lookup_tolerates_case_and_whitespace_only(self):
        result = normalize_tx_sow("  mw   swap ", self.registry)
        self.assertEqual(result["canonical_sow"], "MW SWAP")
        self.assertEqual(result["classification"], CLASSIFICATION_PR_TRIGGER)
        self.assertEqual(result["normalization_status"], "APPROVED")

    def test_unknown_value_fails_closed(self):
        result = normalize_tx_sow("MW Teleportation", self.registry)
        self.assertEqual(result["classification"], CLASSIFICATION_REVIEW_REQUIRED)
        self.assertEqual(result["canonical_sow"], "")

    def test_blank_and_nan_like_values_are_missing(self):
        for raw in ("", "   ", None, "nan"):
            result = normalize_tx_sow(raw, self.registry)
            self.assertEqual(result["classification"], CLASSIFICATION_MISSING)
            self.assertEqual(result["normalization_status"], CLASSIFICATION_REVIEW_REQUIRED)


class TestRegistryValidation(unittest.TestCase):
    def _write_registry(self, tmp_dir, entries):
        path = Path(tmp_dir) / "registry.yaml"
        path.write_text(
            json.dumps({"registry_type": "canonical_sow_registry", "entries": entries}),
            encoding="utf-8",
        )
        return path

    def test_rejects_duplicate_normalized_raw_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_registry(
                tmp,
                [
                    {"raw_value": "MW Swap", "canonical_sow": "MW SWAP", "classification": "PR_TRIGGER"},
                    {"raw_value": "mw  swap", "canonical_sow": "MW SWAP", "classification": "PR_TRIGGER"},
                ],
            )
            with self.assertRaises(ValueError):
                load_canonical_sow_registry(path)

    def test_rejects_non_identity_canonical_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_registry(
                tmp,
                [{"raw_value": "MW Swap", "canonical_sow": "SOMETHING ELSE", "classification": "PR_TRIGGER"}],
            )
            with self.assertRaises(ValueError):
                load_canonical_sow_registry(path)

    def test_rejects_invalid_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_registry(
                tmp,
                [{"raw_value": "MW Swap", "canonical_sow": "MW SWAP", "classification": "AUTO_APPROVE"}],
            )
            with self.assertRaises(ValueError):
                load_canonical_sow_registry(path)

    def test_rejects_wrong_registry_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.yaml"
            path.write_text(json.dumps({"registry_type": "something_else", "entries": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_canonical_sow_registry(path)


if __name__ == "__main__":
    unittest.main()
