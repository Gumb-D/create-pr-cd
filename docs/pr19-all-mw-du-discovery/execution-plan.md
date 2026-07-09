# PR #19 Execution Plan

## Mission Outcome

Build a discovery-only, human-reviewable all-MW-DU mapping recommendation matrix for Issue `#19` without changing production behavior, approving mappings, or promoting profile lifecycle status.

## Bounded-Step Strategy

Each autonomous wake-up performs exactly one bounded continuation step, updates this state packet, and creates a checkpoint commit if intended changes exist.

## Confirmed Implementation Path

The safest path is to add one new discovery-only builder and wire it into the existing refresh pipeline instead of altering production profile logic or repurposing the current cross-profile action review matrix.

### Existing inputs to reuse

- `config/registries/mw_du_model_discovery_registry.yaml`
  - authoritative per-export/profile identity, source file names, and profile ids
- `config/registries/mw_du_structure_grouping_review.yaml`
  - current exact-fingerprint structural similarity evidence
- `config/registries/mw_du_unresolved_skill_field_review.yaml`
  - current per-profile unresolved field review state
- `config/registries/mw_du_missing_field_bridge_review.yaml`
  - donor/bridge hints for missing PR-critical fields
- `config/du_profiles/*.yaml`
  - read-only required/conditional flags and transform seeds
- `output/du-20260706-profile/*/header_inventory.json`
  - exact four-layer fingerprints for every export column
- `output/du-20260706-profile/*/canonical_field_candidates.json`
  - discovery candidates and ambiguity/missing signals per field
- `output/local_du_reference_inventory.json`
  - optional local relative paths under `Info/reference` when present

### Planned code changes

- Create `scripts/build_all_du_mapping_recommendation_matrix.py`
  - read the existing discovery-only registries plus profiler artifacts
  - produce one sanitized machine-readable matrix registry
  - render one committed markdown report and optional local-only output copies under `output/`
- Modify `scripts/refresh_mw_du_discovery_packet.py`
  - call the new builder as part of the single refresh path
- Create `tests/test_all_du_mapping_recommendation_matrix.py`
  - verify recommendation classification, grouping assignment, and sanitized row rendering
- Modify `tests/test_refresh_mw_du_discovery_packet.py`
  - lock the new refresh call order into the orchestration test
- Create `docs/MW_DU_All_DU_Discovery_Mapping_Review.md`
  - committed sanitized report for human review
- Create `docs/pr19-all-mw-du-discovery/mapping-review-schema.json`
  - committed schema/template for the matrix row contract

### Why this path is the narrowest safe change

- `scripts/build_profile_review_matrix.py` batches action-queue themes across profiles, but it does not produce one row per canonical field per DU export, so repurposing it would distort an existing artifact.
- `scripts/build_mapping_decision_workbook.py` already solves candidate ranking, four-layer fingerprint handling, and masking patterns, so the new builder should reuse its concepts rather than invent new field-review semantics.
- `scripts/refresh_mw_du_discovery_packet.py` is already the single refresh entrypoint for tracked discovery artifacts, so adding one new discovery-only output there preserves operator expectations and test coverage.

## Step Sequence

1. Completed: initialize branch, heartbeat, and persistent mission state.
2. Completed: inspect the current discovery packet builders and choose the narrowest safe implementation path.
3. Completed: define and commit the sanitized matrix row schema plus builder interfaces.
4. Completed: implement `build_all_du_mapping_recommendation_matrix.py` and wire it into `refresh_mw_du_discovery_packet.py`.
5. Completed: add targeted tests for the new builder and refresh orchestration.
6. Completed: generate the first committed sanitized doc and local-only matrix outputs from the real profiler artifacts.
7. Run broader verification commands, inspect the generated matrix quality, and tighten recommendation/grouping heuristics where the first pass is too coarse.
8. Prepare final report, create `COMPLETED`, push branch, and open the draft PR.

## Decision Rules

- Prefer extending existing discovery-only builders over introducing parallel logic when the data contracts already exist.
- Treat TX Mini and MW EOS Swap as semantic donors only, never as automatic approval proof.
- Preserve fail-closed behavior and local-only raw-reference handling.
- Keep committed artifacts sanitized and metadata-only.
- Use four-layer fingerprints as the only authoritative source-column identity; never use column index as evidence.

## Next Bounded Step

Review the generated matrix outputs, refine any weak grouping or blocker heuristics, and run the broader validation set for the updated discovery pipeline.
