import json
import csv
import contextlib
import io
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import create_pr
import pr_helpers
from du_export_adapter import build_canonical_site_record, resolve_profile_field_mappings
from du_profile_loader import load_du_profile
from geography_resolver import GeographyResolver
from profile_du_export import fingerprint_key


JENDELA_PROFILE_PATH = ROOT / "config" / "du_profiles" / "jendela_tx_migration_pr_v1.yaml"
TX_MINI_PROFILE_PATH = ROOT / "config" / "du_profiles" / "tx_mini_pr_v1.yaml"
SOW_REGISTRY_PATH = ROOT / "config" / "registries" / "canonical_sow_registry.yaml"


class CanonicalRecordFactory:
    def __init__(self, profile_path):
        self.profile = load_du_profile(profile_path)
        self.inventory = {
            "sheets": [
                {
                    "sheet_name": "DU Export",
                    "columns": [
                        {
                            "fingerprint": candidate["fingerprint"],
                            "fingerprint_key": fingerprint_key(candidate["fingerprint"]),
                        }
                        for config in self.profile["field_mapping"].values()
                        for candidate in config.get("source_candidates", [])
                    ],
                }
            ]
        }
        self.resolved = resolve_profile_field_mappings(self.inventory, self.profile)

    def build(self, values, *, scope="TI", site_code="GENERIC-1", sow_registry=None):
        defaults = {
            "site_code": site_code,
            "site_name": "Generic Site",
            "du_key": "DU-1",
            "tx_sow_raw": "MW Swap",
            "tx_upgrade_scope_raw": "TSS+TI",
            "region": "Northern",
            "state": "Kedah",
            "subcontractor_tss": "GTSB",
            "subcontractor_ti": "GTSB",
            "existing_tss_pr_status": "",
            "existing_ti_pr_status": "",
            "antenna_size_ne": "0.6m",
            "antenna_size_fe": "0.6m",
            "tx_before_migration": "Starlink",
            "final_backhaul": "Fiber Own Build",
        }
        defaults.update(values)
        raw = {}
        for field_name, config in self.profile["field_mapping"].items():
            if field_name not in defaults:
                continue
            for candidate in config.get("source_candidates", []):
                raw[fingerprint_key(candidate["fingerprint"])] = defaults[field_name]
        identity = self.profile["identity"]
        return build_canonical_site_record(
            raw,
            self.profile,
            {
                "project_key": identity["project_key"],
                "du_model_name": identity["accepted_du_models"][0],
                "du_model_id": identity["accepted_du_model_ids"][0],
                "view_id": identity["accepted_view_ids"][0],
                "source_file_name": "synthetic-export.xlsx",
                "source_file_hash": "source-hash",
                "header_hash": self.profile["export_structure"]["approved_header_hashes"][0],
                "source_row_number": 7,
            },
            scope=scope,
            resolved_mappings=self.resolved,
            sow_registry=sow_registry,
        )


class TestJendelaMigrationDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = CanonicalRecordFactory(JENDELA_PROFILE_PATH)
        cls.sow_registry = json.loads(SOW_REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_profile_maps_both_migration_fields_with_full_approved_provenance(self):
        expected = {
            "tx_before_migration": {
                "field_code": "docata|ZDCSZ01016454",
                "wbs_stage": "Installation",
                "task_name": "Wireless RAN",
                "display_header": "TX Before Migration",
            },
            "final_backhaul": {
                "field_code": "docata|ZDCSZ00823600",
                "wbs_stage": "Installation",
                "task_name": "Wireless RAN",
                "display_header": "Final Backhaul",
            },
        }
        for field_name, fingerprint in expected.items():
            with self.subTest(field=field_name):
                config = self.factory.profile["field_mapping"].get(field_name)
                self.assertIsNotNone(config)
                self.assertEqual(config["source_candidates"], [{"fingerprint": fingerprint, "mapping_status": "APPROVED"}])
                record = self.factory.build({"tx_sow_raw": ""})
                evidence = record["source_evidence"]["fields"][field_name]
                self.assertEqual(evidence["source_header_fingerprint"], fingerprint)
                self.assertEqual(evidence["mapping_status"], "APPROVED")

    def test_profile_maps_corrected_jendela_state_with_full_approved_provenance(self):
        expected = {
            "field_code": "site|fix00008",
            "wbs_stage": "Site Basic Info",
            "task_name": "Site Basic Info",
            "display_header": "Province/State",
        }
        mapping = self.factory.profile["field_mapping"]["state"]
        self.assertEqual(mapping["source_candidates"], [{"fingerprint": expected, "mapping_status": "APPROVED"}])

        record = self.factory.build(
            {
                "state": "Johor",
                "region": "Southern",
                "tx_before_migration": "Starlink",
                "final_backhaul": "MW",
                "tx_sow_raw": "",
            },
            sow_registry=self.sow_registry,
        )
        self.assertEqual(record["pr_context"]["state"], "Johor")
        self.assertEqual(
            record["source_evidence"]["fields"]["state"],
            {
                "source_header_fingerprint": expected,
                "source_value": "Johor",
                "transformation": "trim",
                "mapping_status": "APPROVED",
            },
        )

    def test_exact_mw_source_value_normalizes_at_jendela_decision_boundary(self):
        cases = [
            ("Starlink", "STARLINK_TO_MICROWAVE", ["Dismantle Starlink", "MW New Link"]),
            ("MW", "MICROWAVE_TO_MICROWAVE", ["Dismantle MW", "MW New Link"]),
        ]
        for before, expected_code, expected_work_items in cases:
            with self.subTest(before=before):
                record = self.factory.build(
                    {
                        "tx_before_migration": before,
                        "final_backhaul": "MW",
                        "state": "Johor",
                        "region": "Southern",
                        "tx_sow_raw": "",
                    },
                    sow_registry=self.sow_registry,
                )
                decision = record["pr_context"]["migration_decision"]
                self.assertEqual(decision["classification"], "APPROVED")
                self.assertEqual(decision["decision_code"], expected_code)
                self.assertEqual([item["work_item"] for item in decision["work_items"]], expected_work_items)
                self.assertEqual(decision["source_values"]["tx_before_migration"], before)
                self.assertEqual(decision["source_values"]["final_backhaul"], "MW")

    def test_mw_normalization_is_exact_and_unknown_values_fail_closed(self):
        for value in ("MW link", "BMW", "MW-1"):
            with self.subTest(value=value):
                record = self.factory.build(
                    {
                        "tx_before_migration": "Starlink",
                        "final_backhaul": value,
                        "state": "Johor",
                        "region": "Southern",
                        "tx_sow_raw": "",
                    },
                    sow_registry=self.sow_registry,
                )
                decision = record["pr_context"]["migration_decision"]
                self.assertEqual(decision["classification"], "REVIEW_REQUIRED")
                self.assertEqual(decision["reason_code"], "JENDELA_MIGRATION_COMBINATION_NOT_APPROVED")

    def test_jendela_state_reaches_existing_west_and_east_malaysia_routing(self):
        cases = [
            ("Southern", "Johor", 1.49, 103.74, "Johor"),
            ("Sabah", "Sabah", 5.9804, 116.0735, "Sabah"),
            ("Sarawak", "Sarawak", 1.5533, 110.3592, "Sarawak"),
        ]
        resolver = GeographyResolver()
        for region, state, latitude, longitude, expected_state in cases:
            with self.subTest(region=region, state=state):
                record = self.factory.build(
                    {
                        "tx_before_migration": "Starlink",
                        "final_backhaul": "MW",
                        "region": region,
                        "state": state,
                        "latitude": latitude,
                        "longitude": longitude,
                        "tx_sow_raw": "",
                    },
                    sow_registry=self.sow_registry,
                )
                mw_row = create_pr._renderer_rows(record)[-1]
                result = resolver.resolve_route_bucket(mw_row, "inbound_route")
                self.assertEqual(result["status"], "RESOLVED", result)
                self.assertEqual(result["state"], expected_state)
                self.assertEqual(mw_row["Province/State"], state)

    def test_jendela_blank_or_unknown_state_fails_closed_at_existing_route_boundary(self):
        resolver = GeographyResolver()
        for state in ("", "Atlantis"):
            with self.subTest(state=state):
                record = self.factory.build(
                    {
                        "tx_before_migration": "Starlink",
                        "final_backhaul": "MW",
                        "region": "Southern",
                        "state": state,
                        "tx_sow_raw": "",
                    },
                    sow_registry=self.sow_registry,
                )
                mw_row = create_pr._renderer_rows(record)[-1]
                result = resolver.resolve_route_bucket(mw_row, "inbound_route")
                self.assertEqual(result["status"], "REVIEW_REQUIRED")
                self.assertEqual(result["reason_code"], "UNKNOWN_STATE")

    def test_all_four_approved_combinations_create_complete_ti_work_plans(self):
        cases = {
            ("Starlink", "Fiber Own Build"): ["Dismantle Starlink", "BBU Patching"],
            ("Microwave", "Fiber Own Build"): ["Dismantle MW", "BBU Patching"],
            ("Starlink", "Microwave"): ["Dismantle Starlink", "MW New Link"],
            ("Microwave", "Microwave"): ["Dismantle MW", "MW New Link"],
        }
        for (before, final), expected in cases.items():
            with self.subTest(before=before, final=final):
                record = self.factory.build(
                    {"tx_before_migration": before, "final_backhaul": final, "tx_sow_raw": ""},
                    scope="TI",
                )
                self.assertIn("migration_decision", record["pr_context"])
                decision = record["pr_context"].get("migration_decision", {})
                self.assertEqual(decision["classification"], "APPROVED")
                self.assertEqual([item["work_item"] for item in decision["work_items"]], expected)
                self.assertEqual(record["validation"]["pr_input_classification"], "PR_INPUT_READY")

    def test_blank_or_unknown_combination_fails_closed_without_partial_work(self):
        cases = [("", "Fiber Own Build"), ("Starlink", ""), ("Satellite", "Fiber Own Build"), ("Starlink", "5G")]
        for before, final in cases:
            with self.subTest(before=before, final=final):
                record = self.factory.build(
                    {"tx_before_migration": before, "final_backhaul": final, "tx_sow_raw": ""},
                    scope="TI",
                )
                self.assertIn("migration_decision", record["pr_context"])
                decision = record["pr_context"].get("migration_decision", {})
                self.assertEqual(decision["classification"], "REVIEW_REQUIRED")
                self.assertEqual(decision["work_items"], [])
                self.assertNotEqual(record["validation"]["pr_input_classification"], "PR_INPUT_READY")
                self.assertTrue(
                    any(reason.startswith("JENDELA_MIGRATION_") for reason in record["validation"]["blocking_reasons"])
                )

    def test_matrix_is_ti_only_and_tss_new_starlink_remains_review_required(self):
        record = self.factory.build(
            {
                "tx_before_migration": "Starlink",
                "final_backhaul": "Fiber Own Build",
                "tx_sow_raw": "New Starlink",
            },
            scope="TSS",
            sow_registry=self.sow_registry,
        )
        partitions = create_pr._partition_records([record], "TSS")
        self.assertEqual(partitions["candidates"], [])
        self.assertEqual(partitions["review_required"], [record])
        self.assertNotEqual(record["pr_context"].get("migration_decision", {}).get("classification"), "APPROVED")
        self.assertEqual(
            record["source_evidence"]["fields"]["tx_sow_normalized"]["normalization_status"],
            "REVIEW_REQUIRED",
        )

    def test_other_du_profiles_do_not_use_the_jendela_exception(self):
        factory = CanonicalRecordFactory(TX_MINI_PROFILE_PATH)
        record = factory.build({"tx_sow_raw": "New Starlink"}, scope="TI", sow_registry=self.sow_registry)
        partitions = create_pr._partition_records([record], "TI")
        self.assertEqual(partitions["candidates"], [])
        self.assertEqual(partitions["review_required"], [record])
        self.assertNotIn("migration_decision", record["pr_context"])

    def test_site_8048r_uses_same_generic_matrix_as_any_other_site(self):
        values = {"tx_before_migration": "Starlink", "final_backhaul": "Fiber Own Build", "tx_sow_raw": ""}
        observed_context = self.factory.build(values, scope="TI", site_code="8048R")["pr_context"]
        generic_context = self.factory.build(values, scope="TI", site_code="ANOTHER-SITE")["pr_context"]
        self.assertIn("migration_decision", observed_context)
        self.assertIn("migration_decision", generic_context)
        observed = observed_context.get("migration_decision")
        generic = generic_context.get("migration_decision")
        self.assertEqual(observed, generic)


class TestJendelaRendererAndPbomAtomicity(unittest.TestCase):
    def _candidate_record(self):
        return {
            "identity": {"source_row_number": 7},
            "site": {"site_code": "8048R", "site_name": "Jendela Site", "du_key": "DU-8048R"},
            "pr_context": {
                "region": "Northern",
                "state": "Perak",
                "subcontractor_ti": "GTSB",
                "migration_decision": {
                    "classification": "APPROVED",
                    "decision_code": "STARLINK_TO_FIBER_OWN_BUILD",
                    "work_items": [
                        {
                            "work_item": "Dismantle Starlink",
                            "model_sow": "Starlink Dismantle (Return/MRCF included) & Migration",
                            "required_pbom_codes": ["350000597850", "350000597852"],
                        },
                        {"work_item": "BBU Patching", "model_sow": "BBU Patching", "required_pbom_codes": []},
                    ],
                },
            },
            "technical_context": {"antenna_size_ne": "0.6m", "antenna_size_fe": "0.6m"},
            "approved_contract": {"scope": "TI", "subcontractor": "GTSB"},
            "validation": {"profile_id": "jendela_tx_migration_pr_v1"},
        }

    def test_renderer_consumes_structured_decision_and_emits_each_work_item(self):
        renderer_rows = getattr(create_pr, "_renderer_rows", None)
        self.assertIsNotNone(renderer_rows)
        rows = renderer_rows(self._candidate_record())
        self.assertEqual([row["Migration Work Item"] for row in rows], ["Dismantle Starlink", "BBU Patching"])
        self.assertEqual(
            [row["Tx SOW"] for row in rows],
            ["Starlink Dismantle (Return/MRCF included) & Migration", "BBU Patching"],
        )
        self.assertEqual(rows[0]["Required PBOM Codes"], "350000597850|350000597852")
        self.assertEqual(rows[0]["Migration Decision ID"], rows[1]["Migration Decision ID"])

    def test_renderer_workbook_keeps_atomic_decision_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "renderer.xlsx"
            create_pr._write_renderer_input(path, [self._candidate_record()])
            workbook = load_workbook(path, read_only=True, data_only=True)
            worksheet = workbook["data"]
            rows = list(worksheet.iter_rows(min_row=4, values_only=True))
            workbook.close()
            headers = list(rows[0])
            data = [dict(zip(headers, row)) for row in rows[1:]]
        self.assertEqual(len(data), 2)
        self.assertEqual({row["Migration Work Item"] for row in data}, {"Dismantle Starlink", "BBU Patching"})

    def test_starlink_requires_both_pboms_once_each(self):
        validate = getattr(pr_helpers, "validate_required_pbom_selection", None)
        self.assertIsNotNone(validate)
        required = ["350000597850", "350000597852"]
        valid = [{"PBOM_Code": "350000597850"}, {"PBOM_Code": "350000597852"}]
        self.assertEqual(validate(valid, required), (True, None))
        for invalid in (
            [{"PBOM_Code": "350000597850"}],
            [{"PBOM_Code": "350000597852"}],
            valid + [{"PBOM_Code": "350000597852"}],
        ):
            with self.subTest(invalid=invalid):
                ok, reason = validate(invalid, required)
                self.assertFalse(ok)
                self.assertEqual(reason, "JENDELA_REQUIRED_PBOM_NOT_UNIQUE")

    def test_any_failed_component_removes_all_atomic_decision_output(self):
        filter_atomic = getattr(pr_helpers, "filter_failed_migration_decisions", None)
        self.assertIsNotNone(filter_atomic)
        rows = [
            {"Site_ID": "8048R", "PBOM_Code": "350000597850", "Migration_Decision_ID": "decision-7"},
            {"Site_ID": "8048R", "PBOM_Code": "350000597852", "Migration_Decision_ID": "decision-7"},
            {"Site_ID": "8048R", "PBOM_Code": "350001095420", "Migration_Decision_ID": "decision-7"},
            {"Site_ID": "OTHER", "PBOM_Code": "KEEP", "Migration_Decision_ID": ""},
        ]
        self.assertEqual(filter_atomic(rows, {"decision-7"}), [rows[-1]])

    def test_excel_nan_metadata_does_not_turn_ordinary_rows_into_migration_decisions(self):
        optional_text = getattr(pr_helpers, "optional_cell_text", None)
        self.assertIsNotNone(optional_text)
        self.assertEqual(optional_text(float("nan")), "")
        self.assertEqual(optional_text(None), "")
        self.assertEqual(optional_text(" decision-7 "), "decision-7")

    def test_generator_emits_no_partial_pr_when_one_decision_component_is_unresolved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            renderer_input = temp_path / "renderer.xlsx"
            output = temp_path / "output"
            output.mkdir()
            create_pr._write_renderer_input(renderer_input, [self._candidate_record()])
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_tss_pr_ecc.py"),
                    "--site-data",
                    str(renderer_input),
                    "--pr-model",
                    str(ROOT / "Info" / "input" / "pr_model.xlsx"),
                    "--template",
                    str(ROOT / "Info" / "input" / "ecc_template.xls"),
                    "--mapping",
                    str(ROOT / "Info" / "input" / "contract_info_reference.md"),
                    "--output",
                    str(output),
                    "--scope",
                    "TI",
                    "--all-sites",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(output.glob("*.xlsx")), [])
            review_files = list(output.glob("REVIEW_REQUIRED_TI_*.csv"))
            self.assertEqual(len(review_files), 1)
            with review_files[0].open(encoding="utf-8-sig", newline="") as handle:
                review_rows = list(csv.DictReader(handle))
        self.assertEqual({row["Site_ID"] for row in review_rows}, {"8048R"})

    def test_missing_mw_installation_antenna_sizes_remove_resolved_starlink_rows(self):
        candidate = self._candidate_record()
        candidate["pr_context"]["migration_decision"] = {
            "classification": "APPROVED",
            "decision_code": "STARLINK_TO_MICROWAVE",
            "work_items": [
                {
                    "work_item": "Dismantle Starlink",
                    "model_sow": "Starlink Dismantle (Return/MRCF included) & Migration",
                    "required_pbom_codes": ["350000597850", "350000597852"],
                },
                {"work_item": "MW New Link", "model_sow": "MW Installation", "required_pbom_codes": []},
            ],
        }
        candidate["technical_context"] = {"antenna_size_ne": "", "antenna_size_fe": ""}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            renderer_input = temp_path / "renderer.xlsx"
            pr_model = temp_path / "pr-model-with-jendela-migration.xlsx"
            output = temp_path / "output"
            output.mkdir()
            create_pr._write_renderer_input(renderer_input, [candidate])

            approved_model = ROOT / "Info" / "input" / "pr_model.xlsx"
            shutil.copy2(approved_model, pr_model)
            workbook = load_workbook(pr_model)
            worksheet = workbook["TX Line Item (After 21-Apr 26)"]
            worksheet.insert_rows(392, amount=6)
            model_rows = [
                ["Starlink Dismantle (Return/MRCF included) & Migration", "350000597850", "Starlink dismantling", "Site", 1, "Mandatory"],
                ["Starlink Dismantle (Return/MRCF included) & Migration", "350000597852", "Starlink cutover", "Site", 1, "Mandatory"],
                ["MW Installation", "350000214923", "Inland transportation to North Region--Perak", "Hop", 1, "Mandatory"],
                ["MW Installation", "350001095409", "New - MW Link (0.3/0.6m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
                ["MW Installation", "350001095410", "New - MW Link (0.9/1.2m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
                ["MW Installation", "350001095411", "New - MW Link (1.8m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
            ]
            for row_number, values in enumerate(model_rows, start=392):
                for column_number, value in enumerate(values, start=1):
                    worksheet.cell(row=row_number, column=column_number, value=value)
            workbook.save(pr_model)
            workbook.close()

            original_read_bytes = Path.read_bytes
            approved_bytes = approved_model.read_bytes()

            def approved_hash_bytes(path):
                if Path(path).resolve() == pr_model.resolve():
                    return approved_bytes
                return original_read_bytes(path)

            argv = [
                "generate_tss_pr_ecc.py",
                "--site-data",
                str(renderer_input),
                "--pr-model",
                str(pr_model),
                "--template",
                str(ROOT / "Info" / "input" / "ecc_template.xls"),
                "--mapping",
                str(ROOT / "Info" / "input" / "contract_info_reference.md"),
                "--output",
                str(output),
                "--scope",
                "TI",
                "--all-sites",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(Path, "read_bytes", approved_hash_bytes),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                runpy.run_path(str(ROOT / "scripts" / "generate_tss_pr_ecc.py"), run_name="__main__")

            self.assertEqual(list(output.glob("*.xlsx")), [])
            review_files = list(output.glob("REVIEW_REQUIRED_TI_*.csv"))
            self.assertEqual(len(review_files), 1)
            with review_files[0].open(encoding="utf-8-sig", newline="") as handle:
                review_rows = list(csv.DictReader(handle))
        self.assertEqual({row["Site_ID"] for row in review_rows}, {"8048R"})

    def test_approved_mw_transitions_reach_complete_atomic_ecc_output(self):
        cases = [
            (
                "STARLINK_TO_MICROWAVE",
                [
                    {
                        "work_item": "Dismantle Starlink",
                        "model_sow": "Starlink Dismantle (Return/MRCF included) & Migration",
                        "required_pbom_codes": ["350000597850", "350000597852"],
                    },
                    {"work_item": "MW New Link", "model_sow": "MW Installation", "required_pbom_codes": []},
                ],
                {"350000597850", "350000597852", "350000214932", "350001095409"},
            ),
            (
                "MICROWAVE_TO_MICROWAVE",
                [
                    {"work_item": "Dismantle MW", "model_sow": "MW Dismantle", "required_pbom_codes": []},
                    {"work_item": "MW New Link", "model_sow": "MW Installation", "required_pbom_codes": []},
                ],
                {"350000589265", "350001095413", "350000214932", "350001095409"},
            ),
        ]
        for decision_code, work_items, expected_pboms in cases:
            with self.subTest(decision_code=decision_code), tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                renderer_input = temp_path / "renderer.xlsx"
                pr_model = temp_path / "pr-model-with-jendela-migration.xlsx"
                output = temp_path / "output"
                output.mkdir()

                candidate = self._candidate_record()
                candidate["pr_context"]["region"] = "Southern"
                candidate["pr_context"]["state"] = "Johor"
                candidate["pr_context"]["migration_decision"] = {
                    "classification": "APPROVED",
                    "decision_code": decision_code,
                    "work_items": work_items,
                }
                create_pr._write_renderer_input(renderer_input, [candidate])

                approved_model = ROOT / "Info" / "input" / "pr_model.xlsx"
                shutil.copy2(approved_model, pr_model)
                workbook = load_workbook(pr_model)
                worksheet = workbook["TX Line Item (After 21-Apr 26)"]
                worksheet.insert_rows(392, amount=6)
                model_rows = [
                    ["Starlink Dismantle (Return/MRCF included) & Migration", "350000597850", "Starlink dismantling", "Site", 1, "Mandatory"],
                    ["Starlink Dismantle (Return/MRCF included) & Migration", "350000597852", "Starlink cutover", "Site", 1, "Mandatory"],
                    ["MW Installation", "350000214932", "Inland transportation to South Region--Johor", "Hop", 1, "Mandatory"],
                    ["MW Installation", "350001095409", "New - MW Link (0.3/0.6m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
                    ["MW Installation", "350001095410", "New - MW Link (0.9/1.2m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
                    ["MW Installation", "350001095411", "New - MW Link (1.8m, 2 antenna)", "Hop", 1, "4 choose 1 (Mandatory)"],
                ]
                for row_number, values in enumerate(model_rows, start=392):
                    for column_number, value in enumerate(values, start=1):
                        worksheet.cell(row=row_number, column=column_number, value=value)
                workbook.save(pr_model)
                workbook.close()

                original_read_bytes = Path.read_bytes
                approved_bytes = approved_model.read_bytes()

                def approved_hash_bytes(path):
                    if Path(path).resolve() == pr_model.resolve():
                        return approved_bytes
                    return original_read_bytes(path)

                argv = [
                    "generate_tss_pr_ecc.py",
                    "--site-data", str(renderer_input),
                    "--pr-model", str(pr_model),
                    "--template", str(ROOT / "Info" / "input" / "ecc_template.xls"),
                    "--mapping", str(ROOT / "Info" / "input" / "contract_info_reference.md"),
                    "--output", str(output),
                    "--scope", "TI",
                    "--all-sites",
                ]
                captured_stdout = io.StringIO()
                captured_stderr = io.StringIO()
                with (
                    mock.patch.object(sys, "argv", argv),
                    mock.patch.object(Path, "read_bytes", approved_hash_bytes),
                    contextlib.redirect_stdout(captured_stdout),
                    contextlib.redirect_stderr(captured_stderr),
                ):
                    runpy.run_path(str(ROOT / "scripts" / "generate_tss_pr_ecc.py"), run_name="__main__")

                output_files = list(output.glob("*.xlsx"))
                self.assertEqual(
                    len(output_files),
                    1,
                    f"stdout:\n{captured_stdout.getvalue()}\nstderr:\n{captured_stderr.getvalue()}",
                )
                self.assertEqual(list(output.glob("REVIEW_REQUIRED_TI_*.csv")), [])
                workbook = load_workbook(output_files[0], read_only=True, data_only=True)
                worksheet = workbook["details"]
                actual_pboms = {str(row[9]) for row in worksheet.iter_rows(min_row=2, values_only=True)}
                workbook.close()
                self.assertEqual(actual_pboms, expected_pboms)


class TestGlobalGeographyCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = CanonicalRecordFactory(TX_MINI_PROFILE_PATH)

    def test_northern_pahang_becomes_perak_with_audit_evidence(self):
        record = self.factory.build({"region": " Northern ", "state": " pahang "}, scope="TI")
        self.assertEqual(record["pr_context"]["state"], "Perak")
        self.assertEqual(
            record["source_evidence"]["geography_corrections"],
            [
                {
                    "reason_code": "NORTHERN_PAHANG_CORRECTED_TO_PERAK",
                    "field": "state",
                    "original_value": "pahang",
                    "corrected_value": "Perak",
                }
            ],
        )

    def test_other_state_or_other_region_is_not_corrected(self):
        cases = [("Northern", "Kedah"), ("Eastern", "Pahang")]
        for region, state in cases:
            with self.subTest(region=region, state=state):
                record = self.factory.build({"region": region, "state": state}, scope="TI")
                self.assertEqual(record["pr_context"]["state"], state)
                self.assertEqual(record["source_evidence"].get("geography_corrections", []), [])

    def test_incomplete_or_malformed_geography_is_not_silently_corrected(self):
        for region, state in (("Northern", ""), ("Northern", "Atlantis"), ("", "Pahang")):
            with self.subTest(region=region, state=state):
                record = self.factory.build({"region": region, "state": state}, scope="TI")
                self.assertNotEqual(record["pr_context"].get("state"), "Perak")
                self.assertEqual(record["source_evidence"].get("geography_corrections", []), [])


if __name__ == "__main__":
    unittest.main()
