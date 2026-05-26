# Phase 2C Route Resolver Checkpoint / Handover

## 1. Repository State
* **Repository Path:** `D:\Users\10265696\Documents\AI Transformation\Skill\create-pr-cd`
* **GitHub Repository:** `Gumb-D/create-pr-cd`
* **Active Branch:** `main`
* **Latest Pushed Commit:** `b52312a` (`fix: propagate route resolver review reasons`)
* **Working Tree State:** Completely clean (zero untracked or modified files)
* **Sync Status:** Up-to-date with remote tracking `origin/main`

---

## 2. Purpose of Phase 2C
The main purpose of the Phase 2C route resolver workstream was to design and implement a safe, deterministic geographical route resolution system to replace the legacy, broad substring/keyword search loops used during the TI PR ECC choose-group matching.

Previously, candidate items for Inland Transportation and Simple Packing choose groups were matched using raw keyword scanning on the site's broad region field. This mechanism carried a significant risk of silent wrong PBOM selections when SOW descriptions overlapped or sites were assigned to incorrect broad divisions.

To solve this, Phase 2C:
* Introduced a centralized `GeographyResolver` utilizing an structured reference mapping file (`geography_mapping.json`).
* Transitioned both Simple Packing and Inland Transportation choose groups to exact-matching resolved PBOM codes.
* Enforced a strict fail-closed policy: any unresolved, unconfirmed, or ambiguous route resolutions immediately block partial ECC generation and append a detailed review warning to `REVIEW_REQUIRED_TI_*.csv` to prevent incomplete output rows.

---

## 3. Completed Phase Timeline

### Phase 2C-1
* **Objective:** Added the isolated `GeographyResolver` scaffolding/helper module in test-only mode.
* **Commit:** `2b83db5` (`test: add route resolver scaffolding`)

### Phase 2C-2
* **Objective:** Expanded fail-closed unit test coverage inside `tests/test_geography_resolver.py` to assert correct behavior for unresolved bounds, missing coordinates, and malformed fields.
* **Commit:** `56d31b9` (`test: expand route resolver fail-closed coverage`)

### Phase 2C-3B
* **Objective:** Wired the `GeographyResolver` into production matching for confirmed **Simple Packing (outbound_route)** choose groups.
* **Commit:** `4493b06` (`fix: wire simple packing resolver selection`)

### Phase 2C-3C
* **Objective:** Audited Simple Packing outputs, confirming successful exact PBOM resolution for `1106L_HU` and fail-closed blocking for unconfirmed regions.

### Phase 2C-4B
* **Objective:** Wired the `GeographyResolver` into production matching for confirmed **Inland Transportation (inbound_route)** choose groups and completely decoupled `'inbound_route'` SOWs from the legacy string search block.
* **Commit:** `f3d3902` (`fix: wire inland transportation resolver selection`)

### Phase 2C-4C
* **Objective:** Audited Inland Transportation outputs, confirming exact PBOM mapping and fail-closed state preservation.

### Phase 2C-5B
* **Objective:** Implemented **Option D (Resolver Instance State Preservation)** reason-code plumbing to safely propagate high-fidelity route resolver failure reason codes up to the review CSV without altering core function signatures or return tuples.
* **Commit:** `b52312a` (`fix: propagate route resolver review reasons`)

### Phase 2C-5C
* **Objective:** Audited the reason-code plumbing, verifying that structured resolver warnings work correctly for all failure cases while preserving existing generic review reasons for standard non-resolver failures.

---

## 4. Current Production Behavior

### Simple Packing / outbound_route
* Category `'outbound_route'` is identified from the PR model item.
* When matched in the choose group, the system executes `resolver.resolve_material_code(row, "outbound_route")`.
* Uses confirmed geography mapping to select the exact target PBOM code (e.g. `350000589232` for Selangor/KL).
* Bypasses keyword fallback scanning completely.
* Any unconfirmed or unresolved states immediately return `REVIEW_REQUIRED` (fail-closed).

### Inland Transportation / inbound_route
* Category `'inbound_route'` is identified from the PR model item.
* When matched in choose groups, the system executes `resolver.resolve_material_code(row, "inbound_route")`.
* Maps confirmed states (e.g. Johor resolves to `350000214932`, Selangor/KL/Putrajaya resolve to `350000214911`).
* Keyword fallback scanning is fully disabled.
* East Malaysia coordinates and boundary anomalies (like Lawas) are strictly fail-closed.

### Still Unchanged / Regression-Safe
* **Antenna choose behavior:** Evaluated strictly under standard matching rules.
* **MW Hardware Cutover exclusion:** Preserved.
* **MW Reroute behavior:** Standard multi-hop Reroute matching is completely preserved.
* **TSS logic:** Stays fully isolated.
* **Non-route TI choose groups:** Bypassed and unaffected.
* **Metadata flags:** `geography_mapping.json` metadata `production_ready` remains `false`.

---

## 5. Known Verified Output (Smoke Baseline)

During the smoke test execution (`python scripts/smoke_test_phase1c.py`), the following deterministic site behaviors are verified:

### 1. Site `1106L_HU` (Successful Generation)
* **ECC Row Count:** Exactly 3 rows
* **Resolved PBOM Codes:**
  - **Inland Transportation (inbound):** `350000214911`
  - **Swap MW Link:** `350001095406` (verified actual output value; *note: previous typo `35001095406` is resolved*)
  - **Simple Packing (outbound):** `350000589232`
* **Result:** `PASS` (zero duplicate or missing route rows, correct warehouse assignment).

### 2. Site `1007D_HU` (Blocked)
* **Result:** Sent to `REVIEW_REQUIRED_TI_*.csv`.
* **Reason:** `No matching antenna group item` (generic antenna size fallback reason).
* **ECC Spreadsheet:** Successfully **blocked** (preventing partial/corrupt ECC generation).

### 3. Site `9743C_AD` (Partial Preserved)
* **Result:** Standard installation row written to ECC spreadsheet; decommissioning SOW sent to review.
* **Reason:** `MW Reroute decom antenna size ambiguous` (preserved fallback generic reason).

### 4. Site `A01073_AD` (Blocked)
* **Result:** Sent to `REVIEW_REQUIRED_TI_*.csv`.
* **Reason:** `Missing TI antenna size - review required` (preserved fallback generic reason).
* **ECC Spreadsheet:** Successfully **blocked**.

---

## 6. Structured Review Reason Behavior
When the route resolver fails closed, it propagates specific key-value structured warnings directly into the `Review_Reason` column of `REVIEW_REQUIRED_TI_*.csv`:

### Type 1: Geography Resolver Fail-Closed
Format: `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=<route_type>; reason=<reason_code>; bucket=<bucket_name>`
* **Outbound Perlis State:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=outbound_route; reason=NORTH_REGION_UNRESOLVED; bucket=Perlis`
* **Outbound Pahang State:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=outbound_route; reason=EAST_REGION_UNRESOLVED; bucket=Pahang`
* **Inbound East Malaysia State:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=inbound_route; reason=COORDINATE_RESOLUTION_UNSUPPORTED; bucket=Kota Kinabalu`
* **Lawas Special Boundary:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=outbound_route; reason=LAWAS_UNRESOLVED; bucket=Lawas`
* **Missing State Field:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=outbound_route; reason=MISSING_STATE; bucket=`
* **Unknown State Field:** `ROUTE_RESOLVER_REVIEW_REQUIRED: route_type=outbound_route; reason=UNKNOWN_STATE; bucket=`

### Type 2: PR Model Code Mismatch
Format: `ROUTE_RESOLVER_PR_MODEL_MISMATCH: route_type=<route_type>; material_code=<resolved_code>; reason=MATERIAL_CODE_NOT_FOUND`
* **Example:** `ROUTE_RESOLVER_PR_MODEL_MISMATCH: route_type=outbound_route; material_code=350000589265; reason=MATERIAL_CODE_NOT_FOUND`

### Type 3: PR Model Code Duplicate
Format: `ROUTE_RESOLVER_PR_MODEL_DUPLICATE: route_type=<route_type>; material_code=<resolved_code>; reason=DUPLICATE_MATERIAL_CODE`
* **Example:** `ROUTE_RESOLVER_PR_MODEL_DUPLICATE: route_type=outbound_route; material_code=350000589232; reason=DUPLICATE_MATERIAL_CODE`

*Note: Non-resolver matching failures continue to preserve their existing generic Review_Reason texts.*

---

## 7. Validation Commands
The standard validation suite must be run to guarantee repository safety:
```bash
python -m unittest tests/test_geography_resolver.py
python scripts/validate_geography_mapping.py
python scripts/validate_simple_packing_decision_pack.py
python scripts/smoke_test_phase1c.py
git diff --check
git status --short
```
* **Tests Passed:** All 10 unit tests pass cleanly.
* **Integrity Validators Passed:** Centralized map validator and decision pack aligner succeed with `PASS`.
* **Smoke Tests Passed:** Dashboard matches smoke expectations with zero regressions.
* **Whitespace & Git Status:** Safe diff checks and 100% clean working trees.

---

## 8. Remaining Risks / Not Yet Done
Future phases must note the following incomplete areas:
* **`production_ready` flag:** Currently `false` in `geography_mapping.json`. It must not be set to `true` without full SME verification.
* **Sabah/Sarawak Coordinate Resolution:** Stubs exist, but actual coordinate bounding-box resolution into city/district buckets is **not** implemented.
* **Unresolved North/East Simple Packing:** Alternate routes (KV vs regional warehouses) for Perlis, Kedah, Penang, Perak, Pahang, Terengganu, and Kelantan are still unresolved by SMEs.
* **Lawas Special Handling:** Stubs exist, but it remains fully fail-closed.
* **GIS / Google Maps Integration:** No live API integration exists.

---

## 9. Recommended Next Phase
We highly recommend that **Phase 2D** begins with a **planning-only** exploration focusing on one of the following directions:
1. Designing the coordinate-to-city bounding-box resolution stubs for Sabah/Sarawak.
2. Formulating SME resolution decisions for North and East Region outbound warehouse alternates.
3. Defining a production-readiness gate workflow to safely transition `production_ready` to `true`.
4. Designing Lawas boundary manual override assign rules.

---

## 10. Agent Safety Instructions
> [!WARNING]
> Future agents working on this repository MUST NOT:
> * Re-enable keyword fallback scanning for `inbound_route` or `outbound_route`.
> * Set `production_ready` to `true` without SME approvals and test assertions.
> * Implement coordinate bounding box models without strict schema specs.
> * Silently resolve Lawas boundary or auto-assign regional Simple Packing alternates.
> * Bypass running `python scripts/smoke_test_phase1c.py` before any commit.
