# Non-Production Canonical Generator Bridge Self-Review

## Scope

Changed only:

- design and implementation plan;
- one new non-production bridge module;
- one synthetic test module;
- one operating guide.

The existing ECC generator, DU profiles, Header Hashes, PR model rules, and production gates are unchanged.

## Safety review

- The bridge does not import `generate_tss_pr_ecc.py`.
- The bridge accepts only `PR_INPUT_READY` or `PRODUCTION` profiles.
- Header Hash must match an approved profile hash.
- Required source mappings must resolve exactly.
- Every emitted row sets `ECC Allowed` to `False`.
- Output paths are caller-supplied and intended for ignored `output/`.
- No customer workbook or generated packet is committed.

## Known verification limitation

The GitHub connector can create and inspect repository changes, but cannot execute the repository test suite. No test-pass claim is made in this review. Full local verification remains mandatory before Ready/Merge.

## Required local verification

```powershell
python -m unittest tests.test_canonical_generator_bridge -v
python -m unittest tests.test_du_export_adapter -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q scripts tests
git diff --check
git ls-files "Info/reference/du_exports/**"
git ls-files "output/**"
```
