# PR Model Rule Discovery and Rule Engine Design

**Project:** `create-pr-cd`  
**Repository:** `https://github.com/Gumb-D/create-pr-cd`  
**Document Type:** Consolidated business + technical discovery design  
**Status:** Discovery / design baseline  
**Last Updated:** 2026-05-25

---

## 1. Purpose

This document consolidates PR Model business rule discovery, technical rule-engine design, and relevant amendment implementation history for CelcomDigi TX PR ECC generation.

It replaces the need to maintain these separate documents as active references:

- `BUSINESS_DESIGN_PR_MODEL_RULE_DISCOVERY_V1.md`
- `TECHNICAL_DESIGN_PR_RULE_ENGINE_DISCOVERY_V1.md`
- `AMENDMENT_IMPLEMENTATION.md`

The old documents may be archived after this consolidated document is accepted.

---

## 2. Document Scope

### In Scope

- PR ECC generation behavior for TSS and TI.
- TI mandatory choose-item discovery.
- Geography-based Inland Transportation selection.
- Geography-based Simple Packing selection.
- Antenna size selection.
- Swap - MW Link matching.
- MW Hardware Cutover manual handling.
- REVIEW_REQUIRED and whole-site blocking behavior.
- Rule engine architecture direction.
- Relevant implementation baseline from Amendments 1-5.

### Out of Scope

- Final implementation specification.
- UI design.
- Database schema finalization.
- Automated Google Maps/GIS integration.
- Commercial contract validation beyond current reference mapping.
- Final PR Model data cleanup.

---

## 3. Current Repository Baseline

Known baseline at time of consolidation:

- Branch expected: `main`
- PR #4 merged.
- Branch `fix/ti-preserve-non-antenna-choose-groups` deleted locally and remotely.
- Working tree was clean after cleanup.
- Issue #5 fixed partial ECC emission for unresolved mandatory TI choose groups.

Important Issue #5 behavior:

```text
If mandatory TI choose group is unresolved or ambiguous:
→ REVIEW_REQUIRED
→ no partial ECC row for that site/SOW
```

Reference site behavior:

| Site | Expected Behavior |
|---|---|
| `1106L_HU` | Fixed; correct MW Swap ECC behavior. |
| `1007D_HU` | Blocked correctly. |
| `9743C_AD` | MW Reroute unchanged. |

---

## 4. Active Input Files

| Input | Purpose |
|---|---|
| `Info/input/site_pr_po_view.xlsx` | Site scope, TX SOW, TX Upgrade Scope, region, subcon, status, antenna, coordinate fields. |
| `Info/input/pr_model.xlsx` | PR Model rows, PBOM/material code, descriptions, quantity, unit, mandatory/optional choose logic. |
| `Info/input/ecc_template.xls` | Final ECC workbook structure. |
| `Info/input/contract_info_reference.md` | Region to Purchasing Area and Subcontractor to Contract Number mapping. |

Confirmed coordinate columns:

```text
Latitude:  Latitude (North Plus South Minus)
Longitude: Longitude (East Plus West Minus)
```

Confirmed antenna columns:

```text
Microwave MW Config Antenna Size NE
Microwave MW Config Antenna Size FE
```

---

## 5. Classification Legend

| Classification | Meaning |
|---|---|
| CONFIRMED | Agreed business rule or already verified behavior. |
| LIKELY | Strong indication, but not fully validated. |
| SME VALIDATION REQUIRED | Needs business/domain confirmation before automation hardening. |
| OPEN QUESTION | Design or business detail still undecided. |
| OUT OF SCOPE | Not covered by this document. |

---

## 6. Rule Discovery Status Matrix

| Rule Area | Classification | Confidence | Notes |
|---|---:|---:|---|
| Global REVIEW_REQUIRED policy | CONFIRMED | High | Any unresolved mandatory mapping blocks the whole site. |
| Geography Resolver | CONFIRMED | High | Latitude/longitude is the confirmed primary source. |
| Inland Transportation | CONFIRMED | High | 29 choose 1 mandatory; warehouse to destination bucket. |
| Simple Packing | CONFIRMED | High | Triggered by `TX Upgrade Scope` containing `Dismantle`; destination bucket to warehouse. |
| Antenna Selection | CONFIRMED | High | Compare NE/FE antenna size and choose the bigger size. |
| Swap - MW Link | SME VALIDATION REQUIRED | Medium-High | Team stated it applies to all MW-related work; flow-specific validation still recommended. |
| MW Hardware Cutover | CONFIRMED | High | Manual optional item only; no auto-generation. |
| Contract reference mapping | CONFIRMED | High | Markdown reference file introduced by Amendments 1-5. |
| Full Simple Packing mapping table | OPEN QUESTION | Medium | Only known examples captured; full mapping still needed. |
| Lawas Sabah/Sarawak side handling | SME VALIDATION REQUIRED | Medium | Must resolve by coordinate/manual geography. |

---

## 7. Global Failure and REVIEW_REQUIRED Policy

### Business Rule

If any unresolved mandatory mapping condition occurs:

```text
REVIEW_REQUIRED
whole site blocked
no ECC generated
```

### Applies To

- Missing coordinate.
- Unknown state.
- Unknown city bucket.
- Missing region.
- Missing warehouse mapping.
- Missing antenna size.
- Invalid antenna size.
- No PR Model row.
- Multiple PR Model rows.
- Zero PR Model rows for mandatory choose group.
- Missing mandatory choose input.
- Invalid or unsupported SOW.
- Missing `TX Upgrade Scope` when required.

### Technical Enforcement

```text
Rule Engine may produce candidate rows.
Review Engine decides final site pass/fail.
ECC Generator receives only passed sites.
```

Guardrail:

```text
ECC Generator must not receive rows for blocked sites.
```

---

## 8. Shared Business Resolvers

## 8.1 Geography Resolver

### Purpose

Convert site coordinate information into normalized geography fields used by Inland Transportation, Simple Packing, and warehouse selection.

### Input

```text
site_code
latitude
longitude
region/state if available
```

### Output

```text
geo_class: WEST_MALAYSIA | SABAH | SARAWAK
state
city_bucket
warehouse
review_flags
```

### Business Process

```text
Latitude + Longitude
→ Google Maps / manual geography interpretation
→ determine actual geography
→ assign destination bucket and warehouse
```

Warehouse mapping:

```text
West Malaysia → KV warehouse
Sabah → Sabah warehouse
Sarawak → Sarawak warehouse
```

Lawas special exception:

```text
Lawas coordinate
→ determine whether physically Sabah side or Sarawak side
→ assign corresponding warehouse
```

### Technical Direction

For MVP, avoid silent GIS guessing.

Preferred approach:

```text
Coordinate/manual lookup
→ maintained mapping table
→ deterministic mapping
→ REVIEW_REQUIRED if not found
```

---

## 8.2 Antenna Resolver

### Purpose

Normalize NE/FE antenna size into one selected antenna size.

### Input

```text
ne_antenna_size
fe_antenna_size
```

### Output

```text
selected_size
review_flags
```

### Rule

```text
Both NE and FE are required.
Choose the bigger size.
If same size, select that size.
If either side is missing or invalid, REVIEW_REQUIRED.
```

Examples:

| NE | FE | Selected Size |
|---:|---:|---:|
| 0.6m | 1.2m | 1.2m |
| 0.9m | 1.2m | 1.2m |
| 0.3m | 0.6m | 0.6m |
| 0.9m | 0.9m | 0.9m |

Normalization example:

```text
"0.6", "0.6m", "0.6 M", "0.6 meter"
→ 0.6m
```

---

## 9. Rule Catalog

## 9.1 Inland Transportation

Classification: **CONFIRMED**

Type:

```text
29 choose 1 Mandatory
```

Coordinate usage:

```text
All sites use Latitude + Longitude.
West Malaysia included.
```

Business logic:

```text
Coordinate
→ Google Maps/manual geography
→ destination bucket

FROM warehouse
→ TO destination bucket
→ choose exactly one Inland Transportation PR row
```

Failure behavior:

```text
No destination bucket, no warehouse, zero match, or multiple matches
→ REVIEW_REQUIRED
→ whole site blocked
→ no ECC generated
```

---

## 9.2 Simple Packing

Classification: **CONFIRMED**

Trigger:

```text
TX Upgrade Scope contains "Dismantle"
```

Important:

- `TX Upgrade Scope` is the only confirmed trigger source.
- `TX SOW Details` containing decom/decommission is not operationally used.

Route direction:

```text
Inland Transportation: Warehouse → Destination bucket
Simple Packing:        Destination bucket → Warehouse
```

Correct selector:

```text
Coordinate
→ Google Maps/manual geography
→ destination bucket
→ choose matching Simple Packing row
```

Accepted rule:

```text
Simple Packing uses the same geographic destination mapping as Inland Transportation,
but reversed route direction.
```

Rejected rule:

```text
Generic Region + Warehouse only
```

Reason rejected:

Generic Region + Warehouse cannot distinguish Sarawak destination buckets such as Sibu, Miri, and Bintulu.

Known examples:

| Material Code | Description |
|---|---|
| `350000589307` | Simple Packing and Inland transportation from Sibu to Sarawak warehouse for MW |
| `350000589308` | Simple Packing and Inland transportation from Bintulu to Sarawak warehouse for MW |
| `350000589309` | Simple Packing and Inland transportation from Miri to Sarawak warehouse for MW |
| `350000589313` | Simple Packing and Inland transportation from Kota Kinabalu to Sabah warehouse for MW |
| `350000589314` | Simple Packing and Inland transportation from Sandakan to Sabah warehouse for MW |

Open item:

```text
Need complete Simple Packing mapping table.
```

---

## 9.3 Antenna Rule

Classification: **CONFIRMED**

Source fields:

```text
Microwave MW Config Antenna Size NE
Microwave MW Config Antenna Size FE
```

Logic:

```text
compare NE and FE
choose bigger antenna size
```

Tie:

```text
if same size → select that size and generate ONE antenna line item
```

Missing one side:

```text
manual review required
whole site blocked
no ECC
```

PR Model expectation:

```text
Only one PR row should exist per antenna size.
```

---

## 9.4 Swap - MW Link

Classification: **SME VALIDATION REQUIRED**

Team statement:

```text
"Swap - MW Link" applies to ALL MW-related work
```

Inputs:

```text
TX SOW
selected antenna size
```

Selection:

```text
TX SOW + selected antenna size
→ select exactly one PR Model row
```

Failure behavior:

```text
missing antenna, zero match, or multiple matches
→ REVIEW_REQUIRED
→ whole site blocked
→ no ECC
```

Validation note:

The statement “applies to all MW-related work” should be validated because MW Reroute, MW New Link, and MW Swap may have flow-specific differences.

---

## 9.5 MW Hardware Cutover

Classification: **CONFIRMED**

Applicability:

```text
Optional / manually selected
```

Trigger:

```text
No fixed source column
```

Selection:

```text
Manual operator decision only
```

Do not automatically determine from:

- Antenna size.
- Region.
- Coordinate.
- TX SOW.
- MW type.

Technical behavior:

```text
manual selected = true
→ attempt PR Model match

manual selected = false
→ do not generate row
```

If selected but not uniquely matched:

```text
REVIEW_REQUIRED
```

---

## 10. Mapping Tables

## 10.1 Inland Transportation — West Malaysia

| State | Destination Bucket | Material Code |
|---|---|---:|
| Perlis | North Region--Perlis | 350000214920 |
| Kedah | North Region--Kedah | 350000214921 |
| Penang | North Region--Penang | 350000214922 |
| Perak | North Region--Perak | 350000214923 |
| Selangor | KV Region exact site location | 350000214911 |
| Kuala Lumpur | KV Region exact site location | 350000214911 |
| Negeri Sembilan | South Region--Negeri Sembilan | 350000214930 |
| Melaka | South Region--Malacca | 350000214931 |
| Johor | South Region--Johor | 350000214932 |
| Pahang | East Region--Pahang | 350000214939 |
| Terengganu | East Region--Terengganu | 350000214940 |
| Kelantan | East Region--Kelantan | 350000214941 |

## 10.2 Inland Transportation — Sabah

| City Bucket | Material Code |
|---|---:|
| Kota Kinabalu | 350000212474 |
| Sandakan | 350000212475 |
| Tawau | 350000212476 |

## 10.3 Inland Transportation — Sarawak

| City Bucket | Material Code |
|---|---:|
| Kuching | 350000212468 |
| Sibu | 350000212469 |
| Bintulu | 350000212470 |
| Miri | 350000212471 |
| Limbang | 350000212472 |
| Lawas | 350000212473 |
| Sri Aman | 350000358611 |

---

## 11. Technical Architecture

Recommended architecture:

```text
Input Layer
  - Site PR/PO View
  - IEPMS coordinate columns
  - PR Model
  - Contract Info
  - ECC Template

Shared Resolver Layer
  - GeographyResolver
  - AntennaResolver

Rule Engine Layer
  - Deterministic mandatory rules
  - Choose-1 mandatory rules
  - Optional/manual rules

Review Engine
  - REVIEW_REQUIRED creation
  - whole-site block decision
  - no partial ECC policy

ECC Generator
  - receives only fully resolved site rows
```

Design principle:

```text
Resolve first.
Validate second.
Generate ECC last.
```

---

## 12. Suggested Technical Objects

## 12.1 SiteContext

Suggested fields:

```python
SiteContext = {
    "site_code": str,
    "tx_sow": str,
    "tx_upgrade_scope": str,
    "tx_sow_details": str,
    "region": str,
    "subcontractor": str,
    "latitude": str,
    "longitude": str,
    "antenna_ne": str,
    "antenna_fe": str,
    "manual_options": dict,
}
```

## 12.2 RuleResult

Suggested fields:

```python
RuleResult = {
    "rule_name": str,
    "status": "RESOLVED | REVIEW_REQUIRED | NOT_APPLICABLE",
    "blocking": bool,
    "ecc_rows": list,
    "review_reasons": list,
}
```

## 12.3 Review Reason

Suggested fields:

```python
ReviewReason = {
    "site_code": str,
    "rule_name": str,
    "severity": "BLOCKING | NON_BLOCKING",
    "reason_code": str,
    "message": str,
    "source_fields": list,
}
```

---

## 13. PR Model Match Validation

For every mandatory match:

```text
match_count == 1
```

Failure behavior:

```text
match_count == 0 → REVIEW_REQUIRED: NO_PR_MODEL_MATCH
match_count > 1 → REVIEW_REQUIRED: MULTIPLE_PR_MODEL_MATCH
```

---

## 14. Amendment Implementation Baseline

This section preserves the useful baseline from the previous amendment implementation summary.

### Amendment 1 — Separate Contract Info Reference

- Replaced dependency on `contract infor` sheet in PR Model Excel with `Info/input/contract_info_reference.md`.
- Added Region → Purchasing Area mapping.
- Added Subcontractor → Contract Number mapping.

### Amendment 2 — Single `details` Sheet Only

- Output workbook must contain only one sheet named `details`.
- No summary/log/contract sheets in ECC output.

### Amendment 3 — Output Data Correction Rules

| Rule | Behavior |
|---|---|
| SN Sequential | SN starts from 1 per file. |
| Purchasing Area | Derived from Region mapping. |
| Contract Number | Derived from Subcontractor mapping. |
| Column P | Must equal Column 8 Contract Number. |
| Fuzzy Matching | Unknown subcontractor may use conservative fuzzy match. |
| File Split | Maximum 30 unique sites per output file. |

### Amendment 4 — PR Model Line Item Mapping

ECC line item fields should come from PR Model line item definitions, not site-level TX SOW values:

| ECC Field | Source |
|---|---|
| `PBOM Code*` | PR Model line item `Code` |
| `SOW*` | PR Model line item `Description` |
| `Unit*` | PR Model line item `Unit` |
| `Quantity*` | PR Model line item quantity or approved quantity rule |

### Amendment 5 — Site Selection / Filtering

- CLI supports explicit site selection and full generation selection.
- Use `--site-code` for explicit site selection.
- Use `--all-sites` for full generation.
- Error if both are provided.
- Error if neither is provided.
- Apply site filtering before PR scope candidate evaluation.

---

## 15. Implementation Phases

### Phase 1 — Documentation Consolidation

- Use this document as the active PR rule design baseline.
- Archive superseded design documents.
- Do not overwrite README with discovery details.

### Phase 2 — Test Fixture Design

Create representative tests for:

- `1106L_HU` MW Swap.
- `1007D_HU` blocked case.
- `9743C_AD` MW Reroute unchanged.
- Sabah/Sarawak Inland Transportation.
- Simple Packing from Miri/Sibu/Bintulu/Sandakan.
- Same-size antenna tie.
- Missing NE/FE antenna.
- Missing coordinate.
- Multiple PR Model matches.

### Phase 3 — Resolver Extraction

- Implement `GeographyResolver` behind existing behavior.
- Implement `AntennaResolver` behind existing behavior.
- Add unit tests.
- No business expansion.

### Phase 4 — Rule Engine Guard

- Introduce `RuleResult`.
- Centralize mandatory failure handling.
- Enforce whole-site block before ECC generation.

### Phase 5 — Mapping Table Hardening

- Move mappings into reviewed table/config.
- Add validation report for duplicate or missing PR Model rows.
- Add clear REVIEW_REQUIRED reason codes.

### Phase 6 — Optional Manual Override Support

- Add explicit operator/manual input for MW Hardware Cutover.
- Do not auto-generate manual items.

---

## 16. Open Questions

| ID | Question | Owner |
|---|---|---|
| BQ-001 | Confirm whether Swap - MW Link applies to all MW-related work or only selected flows. | SME |
| BQ-002 | Provide complete Simple Packing mapping table. | SME / PR Model Owner |
| BQ-003 | Confirm Lawas Sabah/Sarawak warehouse handling method. | SME |
| BQ-004 | Confirm exact PR Model columns for choose-group matching. | SME / Developer |
| BQ-005 | Decide where geography mapping should live: config file, Excel sheet, database, or code table. | Technical Owner |
| BQ-006 | Decide whether blocked candidate rows should be preserved in diagnostic output but excluded from ECC. | Business + Technical |
| BQ-007 | Decide how manual optional items should be provided in CLI mode. | Business + Technical |

---

## 17. Design Guardrails

- Do not generate partial ECC for a site with unresolved mandatory TI rule.
- Do not auto-select MW Hardware Cutover.
- Do not guess geography when coordinate mapping is unclear.
- Do not collapse Simple Packing to generic Region + Warehouse.
- Do not treat `TX SOW Details` as the confirmed Simple Packing trigger.
- Do not expand business logic beyond confirmed rules without SME validation.
- Do not overwrite README with long discovery details.
