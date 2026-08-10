import json
import re
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pr_model_baseline import (
    PR_MODEL_BASELINE_MISMATCH,
    PrModelBaselineError,
    load_pr_model_baseline,
    validate_pr_model_baseline,
)


class TestPrModelBaseline(unittest.TestCase):
    def test_repository_declares_one_authoritative_production_baseline(self):
        baseline = load_pr_model_baseline(ROOT)
        self.assertEqual(baseline["baseline_id"], "celcomdigi_tx_pr_model_current")
        self.assertEqual(baseline["status"], "PRODUCTION")
        self.assertTrue(str(baseline["model"]["version"]).strip())
        self.assertEqual(baseline["workbook"]["path"], "Info/input/pr_model.xlsx")
        self.assertRegex(str(baseline["workbook"]["sha256"]), r"^[0-9a-f]{64}$")

    def test_repository_workbook_matches_declared_baseline(self):
        baseline = load_pr_model_baseline(ROOT)
        result = validate_pr_model_baseline(root=ROOT)
        self.assertEqual(result["version"], str(baseline["model"]["version"]))
        self.assertEqual(result["path"], ROOT / "Info/input/pr_model.xlsx")
        self.assertEqual(result["actual_sha256"], result["expected_sha256"])
        self.assertEqual(result["actual_sha256"], str(baseline["workbook"]["sha256"]))

    def test_legacy_bare_default_alias_resolves_only_to_current_baseline(self):
        result = validate_pr_model_baseline(Path("pr_model.xlsx"), root=ROOT)
        self.assertEqual(result["path"], ROOT / "Info/input/pr_model.xlsx")
        self.assertEqual(result["actual_sha256"], result["expected_sha256"])

    def test_hash_mismatch_fails_closed_with_precise_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "Info/input").mkdir(parents=True)
            workbook = root / "Info/input/pr_model.xlsx"
            workbook.write_bytes(b"candidate")
            config = {
                "baseline_id": "celcomdigi_tx_pr_model_current",
                "status": "PRODUCTION",
                "model": {"name": "CelcomDigi TX PR Model", "version": "9.9"},
                "workbook": {"path": "Info/input/pr_model.xlsx", "sha256": "0" * 64},
                "validation": {"mismatch_policy": "FAIL_CLOSED", "error_code": PR_MODEL_BASELINE_MISMATCH},
            }
            (root / "config/pr_model_baseline.yaml").write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(PrModelBaselineError) as ctx:
                validate_pr_model_baseline(root=root)
            self.assertEqual(ctx.exception.code, PR_MODEL_BASELINE_MISMATCH)
            self.assertIn(sha256(b"candidate").hexdigest(), str(ctx.exception))

    def test_official_entrypoint_enforces_authoritative_baseline(self):
        entrypoint = (ROOT / "scripts/create_pr.py").read_text(encoding="utf-8")
        self.assertIn('validate_pr_model_baseline(getattr(parsed, "pr_model", None))', entrypoint)
        self.assertIn("except PrModelBaselineError as error", entrypoint)
        self.assertIn('summary["pr_model_baseline"]', entrypoint)

    def test_entrypoint_rejects_wrong_model_before_engine_run(self):
        import create_pr

        parsed = SimpleNamespace(pr_model="definitely-not-approved.xlsx", output="output")
        with patch.object(create_pr._impl, "run") as engine_run:
            with self.assertRaises(PrModelBaselineError) as ctx:
                create_pr.run(parsed)
        self.assertEqual(ctx.exception.code, PR_MODEL_BASELINE_MISMATCH)
        engine_run.assert_not_called()

    def test_legacy_hash_mirrors_match_authoritative_baseline(self):
        baseline = load_pr_model_baseline(ROOT)
        expected = baseline["workbook"]["sha256"]
        pattern = re.compile(r'APPROVED_PR_MODEL_SHA256\s*=\s*["\']([0-9a-f]{64})["\']')
        for relative in (
            "scripts/generate_tss_pr_ecc.py",
            "scripts/run_tx_mini_ecc_parity.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            match = pattern.search(text)
            self.assertIsNotNone(match, relative)
            self.assertEqual(match.group(1), expected, relative)

    def test_audit_metadata_describes_the_authoritative_current_baseline(self):
        baseline = load_pr_model_baseline(ROOT)
        version = str(baseline["model"]["version"])
        expected_sha = str(baseline["workbook"]["sha256"])

        history = (ROOT / "docs/pr_model_history.md").read_text(encoding="utf-8")
        current_rows = [line for line in history.splitlines() if "| CURRENT |" in line]
        self.assertEqual(len(current_rows), 1)
        self.assertIn(f"| v{version} | `{expected_sha}` | CURRENT |", current_rows[0])

        inventory = (ROOT / "docs/pr_model_reference_inventory.md").read_text(encoding="utf-8")
        self.assertIn(f"version = {version}", inventory)
        self.assertIn(f"sha256 = {expected_sha}", inventory)
        self.assertIn(f"## v{version} production status", inventory)
        self.assertNotIn(f"## v{version} candidate status", inventory)

        registry = (ROOT / "config/registries/canonical_sow_registry.yaml").read_text(encoding="utf-8")
        self.assertIn(f"PR Model v{version}", registry)


if __name__ == "__main__":
    unittest.main()
