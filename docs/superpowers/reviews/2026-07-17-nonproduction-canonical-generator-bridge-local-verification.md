# Local Verification Evidence

Initial local execution on 2026-07-17 completed:

- focused bridge suite: 4/4 passed;
- adapter suite: 70/70 passed;
- full suite: 330/330 passed;
- compileall passed;
- ZTE TX MINI TSS and TI packets generated from 180 records;
- source SHA-256 and Header Hash matched the approved profile;
- Git tracking guards returned no customer exports or output artifacts.

The initial packet exposed a classification-order defect: existing PR records with another incomplete field were placed in `REVIEW_REQUIRED` before duplicate detection. Evidence was TSS 107 duplicates versus 109 populated existing-TSS references and TI 11 duplicates versus 18 populated existing-TI references.

The implementation now gives `PR_EXISTS` and `NO_PR_REQUIRED` precedence over canonical completeness, with a dedicated regression test. Post-fix focused verification and packet regeneration remain required before Ready/Merge.
