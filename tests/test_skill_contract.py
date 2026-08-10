import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("create_pr_contract", ROOT / "src" / "main.py")
contract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(contract)


class SkillContractTests(unittest.TestCase):
    def make_request(self, root: Path, *, cancelled: bool = False) -> Path:
        input_dir = root / "input"
        input_dir.mkdir()
        source = input_dir / "site_data.xlsx"
        source.write_bytes(b"contract-test")
        if cancelled:
            (root / "control").mkdir()
            (root / "control" / "cancel.requested").write_text("cancel", encoding="utf-8")
        envelope = {
            "schemaVersion": "1.0",
            "jobId": "JOB-CONTRACT-001",
            "skill": {"skillId": "create-pr-cd", "version": "4.0.0"},
            "parameters": {"scope": "TSS", "allSites": True},
            "files": [{
                "name": "site_data",
                "path": "input/site_data.xlsx",
                "size": source.stat().st_size,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }],
            "paths": {
                "workspace": ".",
                "output": "output",
                "result": "result.json",
                "cancellation": "control/cancel.requested",
            },
        }
        manifest = root / "input.json"
        manifest.write_text(json.dumps(envelope), encoding="utf-8")
        return manifest

    def test_success_writes_authoritative_result_and_declares_every_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.make_request(root)

            def fake_run(parsed):
                deliverable = parsed.output / "result.xlsx"
                deliverable.write_bytes(b"xlsx")
                summary_path = parsed.output / "summary.json"
                summary_path.write_text("{}", encoding="utf-8")
                return {
                    "created_files": [str(deliverable)],
                    "summary_path": str(summary_path),
                    "requested_count": 1,
                    "generated_count": 1,
                    "review_required_count": 0,
                    "approved_ignored_count": 0,
                    "duplicate_blocked_count": 0,
                    "failed_count": 0,
                    "unaccounted_count": 0,
                }

            with patch.object(contract, "run_domain", side_effect=lambda parsed, _cancellation: fake_run(parsed)):
                self.assertEqual(contract.run(manifest), 0)

            result = json.loads((root / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["reconciliation"]["requestedCount"], 1)
            self.assertEqual({item["path"] for item in result["outputs"]}, {"output/result.xlsx", "output/summary.json"})
            self.assertTrue(all(item["sha256"] for item in result["outputs"]))

    def test_cancellation_is_terminal_and_does_not_start_domain_pipeline(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.make_request(root, cancelled=True)
            with patch.object(contract, "run_domain") as run:
                self.assertEqual(contract.run(manifest), 130)
                run.assert_not_called()
            result = json.loads((root / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(result["error"]["code"], "SKILL_CANCELLED")

    def test_rejects_workspace_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.make_request(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"][0]["path"] = "../outside.xlsx"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(contract.run(manifest), 2)
            result = json.loads((root / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["error"]["code"], "CONTRACT_PATH_INVALID")


if __name__ == "__main__":
    unittest.main()
