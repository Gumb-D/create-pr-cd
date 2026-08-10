# Issue #74 — Decom - Relo silent-loss root cause

## Production symptom

`PR-20260810-002` requested 24 TI sites. Eight PostMOCN/Additional sites reached ECC; 16 `Decom - Relo` Relocate sites did not.

## Proven first loss point

The current canonical SOW registry did not contain `Decom - Relo`. Unknown SOW values fail closed during canonical validation, so these records never entered the renderer candidate set. The existing engine summary exposed partition counts but did not expose one terminal disposition per explicitly requested site, allowing downstream consumers to present a successful job without reconciling requested sites.

## Approved business evidence

Business owner confirmation on 2026-08-10: `Decom - Relo` is an independent approved SOW in the current PR Model v4.0; it is not an alias for `MW IDU RELOCATION`.

PR Model v4.0 contains a dedicated `Decom - Relo` TI group with PR Model-driven mandatory/choose-one items. The engine must continue to load those rows from the approved workbook and must not hard-code PBOM codes, descriptions, or quantities.

Historical human-UAT ruling for Issue #53 also requires Decom-Relo output Site ID normalization:

```text
<base>_RELOCATE1 / <base>_Relocate_1 / <base>_Relocate
→ <base>_Relocate
```

The source canonical site identity remains unchanged; only the renderer-facing Site ID is normalized.

## Fix boundary

- Register `Decom - Relo` as exact identity-normalized `PR_TRIGGER`.
- Preserve strict PR Model-driven item selection and fail-closed renderer review behavior.
- Reconcile renderer ECC/review artifacts back to every selected source site.
- Expose requested/generated/review/ignored/duplicate/failed/unaccounted counts plus per-site dispositions in the official create-pr summary.
- A renderer candidate that returns neither ECC nor review/duplicate evidence becomes explicit `FAILED / RENDERER_SITE_UNACCOUNTED`; it can no longer silently disappear.
- AI Worker Platform lifecycle/status behavior remains outside this issue.
