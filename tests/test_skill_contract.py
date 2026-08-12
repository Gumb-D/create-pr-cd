import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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
                    "site_dispositions": [{
                        "site_code": "SITE-001",
                        "disposition": "GENERATED",
                        "reason_code": "",
                    }],
                }

            with patch.object(contract, "run_domain", side_effect=lambda parsed, _cancellation: fake_run(parsed)):
                self.assertEqual(contract.run(manifest), 0)

            result = json.loads((root / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["reconciliation"]["requestedCount"], 1)
            self.assertEqual(result["reconciliation"]["siteDispositions"], [{
                "siteCode": "SITE-001",
                "disposition": "GENERATED",
                "reasonCode": "",
            }])
            self.assertEqual(
                {item["path"] for item in result["outputs"]},
                {"output/result.xlsx", "output/summary.json", "output/CREATE_PR_DELIVERY_TSS.zip"},
            )
            self.assertTrue(all(item["sha256"] for item in result["outputs"]))
            archive = root / "output" / "CREATE_PR_DELIVERY_TSS.zip"
            with contract.zipfile.ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()), {"result.xlsx", "summary.json"})

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

    @staticmethod
    def domain_failure_context(root: Path):
        output = root / "output"
        output.mkdir()
        cancellation = root / "control" / "cancel.requested"
        parsed = SimpleNamespace(
            site_data=root / "site_data.xlsx",
            output=output,
            scope="TSS",
            all_sites=False,
            site_code="A0001,QA15_UNMATCHED",
            non_production_uat=False,
        )
        return parsed, cancellation

    @staticmethod
    def failed_process(payload):
        def fake_popen(*_args, **kwargs):
            kwargs["stderr"].write(json.dumps(payload).encode("utf-8"))
            kwargs["stderr"].flush()
            return SimpleNamespace(returncode=1, poll=lambda: 1)
        return fake_popen

    def test_domain_error_preserves_site_codes_not_found_details(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parsed, cancellation = self.domain_failure_context(root)
            domain_error = {
                "status": "ERROR",
                "code": "SITE_CODES_NOT_FOUND",
                "message": "Requested site codes were not found in the canonical input.",
                "details": {"missing_site_codes": ["QA15_UNMATCHED"]},
            }

            with patch.object(contract.subprocess, "Popen", side_effect=self.failed_process(domain_error)):
                with self.assertRaises(contract.ContractError) as caught:
                    contract.run_domain(parsed, cancellation)

            self.assertEqual(caught.exception.code, "SITE_CODES_NOT_FOUND")
            self.assertEqual(caught.exception.details["missing_site_codes"], ["QA15_UNMATCHED"])

    def test_domain_error_preserves_header_hash_revalidation_with_safe_details_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parsed, cancellation = self.domain_failure_context(root)
            domain_error = {
                "status": "ERROR",
                "code": "HEADER_HASH_REVALIDATION_REQUIRED",
                "message": "The export structure does not match an approved header layout for jendela_tx_migration_pr_v1.",
                "details": {
                    "profile_id": "jendela_tx_migration_pr_v1",
                    "actual_header_hash": "af03e909ff0476a91396efd0f4d735ed85a2af37b1c308bf5849d38d7e629149",
                    "structural_header_hash": "f9a30138c3d7ac088ad19d73aac66cf64d7dda7b337b8da48bebb52b1ae02e9f",
                    "approval_basis": "UNAPPROVED_STRUCTURE",
                    "source_path": "/sensitive/workspace/input.xlsx",
                    "raw_workbook_value": "must-not-leak",
                },
            }

            with patch.object(contract.subprocess, "Popen", side_effect=self.failed_process(domain_error)):
                with self.assertRaises(contract.ContractError) as caught:
                    contract.run_domain(parsed, cancellation)

            self.assertEqual(caught.exception.code, "HEADER_HASH_REVALIDATION_REQUIRED")
            self.assertEqual(
                caught.exception.details,
                {
                    "profile_id": "jendela_tx_migration_pr_v1",
                    "actual_header_hash": "af03e909ff0476a91396efd0f4d735ed85a2af37b1c308bf5849d38d7e629149",
                    "structural_header_hash": "f9a30138c3d7ac088ad19d73aac66cf64d7dda7b337b8da48bebb52b1ae02e9f",
                    "approval_basis": "UNAPPROVED_STRUCTURE",
                    "exitCode": 1,
                },
            )
    def test_unknown_domain_error_remains_generic_without_raw_details(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parsed, cancellation = self.domain_failure_context(root)
            domain_error = {
                "status": "ERROR",
                "code": "INTERNAL_DOMAIN_ERROR",
                "message": "Internal failure.",
                "details": {"source_path": "/sensitive/workspace/input.xlsx"},
            }

            with patch.object(contract.subprocess, "Popen", side_effect=self.failed_process(domain_error)):
                with self.assertRaises(contract.ContractError) as caught:
                    contract.run_domain(parsed, cancellation)

            self.assertEqual(caught.exception.code, "CREATE_PR_FAILED")
            self.assertEqual(caught.exception.details, {"exitCode": 1})


if __name__ == "__main__":
    unittest.main()
