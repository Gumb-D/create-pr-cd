# Non-Production Canonical-to-Generator Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert an approved four-header iEPMS export into a local-only normalized UAT workbook without invoking or enabling ECC generation.

**Architecture:** Add one focused bridge module that reuses the existing profiler, profile loader, adapter, validator, and SOW registry. Keep the existing ECC generator unchanged and expose a CLI that writes only UAT workbook/JSON artifacts.

**Tech Stack:** Python 3, `openpyxl`, existing JSON-compatible YAML profiles and registries, `unittest`.

## Global Constraints

- Exact four-layer fingerprints only.
- Strict approved Header Hash.
- No raw customer export or output artifact tracked.
- No profile lifecycle promotion.
- No import or invocation of the ECC generator.
- Every row must set `ECC Allowed` to `false`.

---

### Task 1: Bridge classification and row mapping

**Files:**
- Create: `scripts/canonical_generator_bridge.py`
- Test: `tests/test_canonical_generator_bridge.py`

**Interfaces:**
- Produces: `canonical_record_to_generator_row(record, scope) -> dict`
- Produces: `classify_uat_record(record, scope) -> tuple[str, list[str]]`

- [ ] Write tests for generator column mapping and four UAT classifications.
- [ ] Run `python -m unittest tests.test_canonical_generator_bridge -v` and confirm failure because the module is absent.
- [ ] Implement minimal mapping and classification logic with permanent `ECC Allowed = False`.
- [ ] Run the focused test and confirm pass.

### Task 2: Four-header export ingestion

**Files:**
- Modify: `scripts/canonical_generator_bridge.py`
- Modify: `tests/test_canonical_generator_bridge.py`

**Interfaces:**
- Produces: `build_records_from_export(input_path, profile_path, scope, sow_registry_path) -> tuple[list[dict], dict]`

- [ ] Add a synthetic four-header workbook test.
- [ ] Assert strict Header Hash rejection and exact source-row provenance.
- [ ] Implement workbook/CSV row iteration by resolved fingerprint position.
- [ ] Reuse `build_header_inventory`, `calculate_header_hash`, `resolve_profile_field_mappings`, and `build_canonical_site_record`.
- [ ] Run the focused test and confirm pass.

### Task 3: UAT packet writer and CLI

**Files:**
- Modify: `scripts/canonical_generator_bridge.py`
- Modify: `tests/test_canonical_generator_bridge.py`

**Interfaces:**
- Produces: `write_uat_packet(records, metadata, output_dir, scope) -> dict[str, Path]`
- CLI arguments: `--input`, `--profile`, `--scope`, `--sow-registry`, `--output`.

- [ ] Add tests for required workbook sheets, JSON counts, and ECC lock.
- [ ] Implement workbook and JSON writing.
- [ ] Implement CLI with output-directory creation and readable summary.
- [ ] Run focused tests.

### Task 4: Portable real-workbook integration

**Files:**
- Modify: `tests/test_canonical_generator_bridge.py`

- [ ] Add a ZTE TX MINI local-only integration test that skips when the workbook is absent.
- [ ] Assert 180 records, approved source hash, approved Header Hash, and permanent ECC lock.
- [ ] Run focused and full adapter suites.

### Task 5: Documentation and verification

**Files:**
- Modify: `README.md`

- [ ] Document the non-production bridge command and output sheets.
- [ ] Run `python -m unittest tests.test_canonical_generator_bridge -v`.
- [ ] Run `python -m unittest tests.test_du_export_adapter -v`.
- [ ] Run `python -m unittest discover -s tests -p "test_*.py" -v`.
- [ ] Run `python -m compileall -q scripts tests` and `git diff --check`.
- [ ] Confirm `git ls-files "Info/reference/du_exports/**"` and `git ls-files "output/**"` return nothing.
