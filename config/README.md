# PR Input Configuration

`du_profiles/` contains versioned four-header source profiles. A profile is not a PR rule engine and cannot introduce ECC logic.

Safety rules:

- Fingerprints contain all four iEPMS header layers. Excel column position is inventory-only metadata.
- Every production profile must have approved exact fingerprints and at least one approved Header Hash.
- `DRAFT`, `PROFILED`, and `BUSINESS_VALIDATED` profiles are not ECC-enabled.
- Profiles must never contain browser cookies, tokens, employee numbers, session IDs, or proxy credentials.
- Local iEPMS auth belongs only in the Git-ignored `scripts/api_auth.json` file.

`pr_model_profiles/` is reserved for the later PR Model workbook version gate. It is intentionally not connected to current runtime behavior.
