# PR #19 Decision Log

## 2026-07-09

- Decision: attach a persistent `/goal` to this thread instead of creating ad hoc follow-up work.
  - Rationale: the master prompt explicitly requires long-running autonomous recovery through the same mission controller.
- Decision: create a heartbeat automation on hourly cadence for this thread.
  - Rationale: the user requested recurring follow-up and the prompt requires wake-up recovery after usage-limit interruption.
- Decision: treat the first bounded step as mission-state scaffolding only.
  - Rationale: the prompt explicitly requires state creation on the first run, and this gives future wake-ups a durable source of truth before implementation changes begin.
- Decision: use the existing tracked discovery packet as the initial evidence baseline.
  - Rationale: the repository already contains discovery-only coverage, grouping, and unresolved-review artifacts for the 10 profiled exports.
- Decision: add a new discovery-only all-DU mapping recommendation builder instead of repurposing `build_profile_review_matrix.py`.
  - Rationale: the current review matrix batches action-queue themes across profiles and does not satisfy the issue's required per-DU, per-canonical-field row model.
- Decision: wire the new builder into `scripts/refresh_mw_du_discovery_packet.py`.
  - Rationale: the repo already treats that script as the single refresh entrypoint for tracked discovery artifacts, and `tests/test_refresh_mw_du_discovery_packet.py` already protects that orchestration contract.
- Decision: reuse concepts from `build_mapping_decision_workbook.py` for candidate ranking, fingerprint presentation, and masking guidance.
  - Rationale: that existing local-only review packager already encodes the right discovery-only semantics for four-layer fingerprint review without writing back approvals.
