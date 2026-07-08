# DU Model Registry

This directory is reserved for a versioned Project and DU Model identity registry. The first foundation PR intentionally does not promote any DU Model to production PR input.

Each later entry must contain only approved non-secret identifiers and profile metadata:

- `project_key`
- `du_model_name`
- `du_model_id`
- `view_id`
- `pr_input_status`
- `profile_id`

Do not store cookies, authorization tokens, employee numbers, session identifiers, or proxy credentials.

Discovery-only registries may also exist in this directory when the repository
needs to track profiled DU metadata before any mappings or header hashes are
approved. Those files must:

- remain explicit about their discovery-only status
- avoid claiming production readiness or approved mappings
- keep unapproved profile references as `null` rather than inventing IDs
- keep manual-review packets separate from approval-bearing registries
- distinguish exact-structure identity from similarity/reuse guidance
- treat cross-model donor suggestions as review leads only, never as approved mappings
- distinguish same display labels from same exact four-layer fingerprints in pairwise comparisons
- keep deprecation evidence separate from active approval claims; a deprecation review may record successor and rollback references without approving a new production profile by itself
