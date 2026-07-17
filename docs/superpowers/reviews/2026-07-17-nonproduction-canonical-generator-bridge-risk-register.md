# Bridge Risk Register

| Risk | Control |
|---|---|
| Bridge output is mistaken for approved ECC input | Every row and summary permanently set `ECC Allowed = false`; operating guide states non-production only |
| Changed iEPMS export layout is processed silently | Strict approved Header Hash check |
| Wrong column selected by display name or index | Exact four-layer fingerprint resolver only |
| Existing PR is duplicated | Scope-specific `PR_EXISTS` records are partitioned into `duplicate_blocked` |
| Unsupported SOW enters candidate output | Approved canonical SOW normalization required |
| Generator behavior changes unintentionally | Existing generator file is untouched |
| Customer data enters Git | No workbook or output file added; local-only paths remain ignored |
| Unverified code is merged | Draft PR; local full-suite verification required before Ready/Merge |
