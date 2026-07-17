# Draft PR Ready Checklist

- [x] Design documented.
- [x] Implementation plan documented.
- [x] Bridge module added without modifying the ECC generator.
- [x] Synthetic behavior tests added.
- [x] Operating guide added.
- [x] Customer exports and generated outputs excluded from the branch.
- [x] Initial focused bridge tests executed locally: 4/4 passed before duplicate-precedence fix.
- [x] Existing adapter tests executed locally: 70/70 passed.
- [x] Initial full suite executed locally: 330/330 passed before duplicate-precedence fix.
- [x] ZTE TX MINI TSS and TI UAT packets generated locally.
- [x] Initial packet evidence exposed duplicate-precedence defect: TSS 107/109 and TI 11/18 existing PR references were partitioned as duplicate.
- [x] Duplicate-precedence fix and regression test committed.
- [ ] Post-fix focused test and packet regeneration completed.
- [ ] Post-fix counts confirm TSS duplicate 109 and TI duplicate 18.
- [ ] JJ business review of final candidate and review-required partitions completed.
