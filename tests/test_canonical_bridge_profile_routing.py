import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "tx_mini_du_export_fixture.xlsx"
SOW_REGISTRY = ROOT / "config" / "registries" / "canonical_sow_registry.yaml"
PROFILE_ROOT = ROOT / "config" / "du_profiles"
BRIDGE = ROOT / "scripts" / "canonical_generator_bridge.py"


class TestCanonicalBridgeProfileRouting(unittest.TestCase):
    def test_cli_auto_selects_profile_without_profile_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / (
                "A-P202202168750_D002-TX Mini Project-Any View-"
                "20260805090102.xlsx"
            )
            output = root / "output"
            shutil.copy2(FIXTURE, source)

            result = subprocess.run(
                [
                    sys.executable,
                    str(BRIDGE),
                    "--input",
                    str(source),
                    "--scope",
                    "TSS",
                    "--sow-registry",
                    str(SOW_REGISTRY),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["resolved_profile_id"], "tx_mini_pr_v1")
            self.assertEqual(
                payload["profile_selection_basis"],
                "PROJECT_AND_DU_MODEL",
            )

    def test_manual_profile_is_assertion_and_cannot_override_auto_route(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / (
                "A-P202202168750_D002-TX Mini Project-Any View-"
                "20260805090102.xlsx"
            )
            output = root / "output"
            shutil.copy2(FIXTURE, source)
            wrong_profile = PROFILE_ROOT / "tx_rollout_2023_pr_v1.yaml"

            result = subprocess.run(
                [
                    sys.executable,
                    str(BRIDGE),
                    "--input",
                    str(source),
                    "--profile",
                    str(wrong_profile),
                    "--scope",
                    "TSS",
                    "--sow-registry",
                    str(SOW_REGISTRY),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                '"error": "DU_PROFILE_IDENTITY_MISMATCH"',
                result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
