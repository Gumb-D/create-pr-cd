# DU Export Adapter Foundation

This document describes the architecture foundation introduced by PR [#16](https://github.com/Gumb-D/create-pr-cd/pull/16) (merged into `main`). The foundation itself introduced no production runtime change: it accepted the existing normalized site input and supported only TSS and TI. Since the merge, Phase 1 TX Mini canonical-input validation has completed — see [MW_DU_Extension_Implementation_Plan.md](/C:/dev/create-pr-cd/docs/MW_DU_Extension_Implementation_Plan.md) for current status. The runtime output path is still unchanged: ECC output remains blocked for every profile by `PROFILE_NOT_PRODUCTION`.

Target flow:

```text
Original export
  -> read-only four-header profiler
  -> versioned DU profile
  -> Canonical PR Site Record v1
  -> existing shared rule engine
  -> controlled output
```

Controls:

- Source fields are identified with Field ID/Code, WBS Stage, Task Name, and Display Header.
- Header Hash is calculated from the complete ordered normalized header inventory.
- Unknown DU identity, changed Header Hash, ambiguous mapping, and missing critical source field are blocked.
- Draft profiles cannot allow automatic output.
- The profiler emits only UNVERIFIED suggestions.

At foundation merge time, the initial TX Mini profile was deliberately `DRAFT` with no approved fingerprints or Header Hash, because no original four-header source fixture was committed in this repository. That has since changed: `tx_mini_pr_v1` is now `PR_INPUT_READY`, with an approved Header Hash and fully approved field mappings, proven against golden-parity evidence (TSS 87/87, TI 19/19 identical). It remains explicitly non-production; `PROFILE_NOT_PRODUCTION` still blocks all ECC output. No source export fixture is committed to this repository — approved evidence remains local-only per the foundation's controls.

Next delivery: Phase 2 (MW EOS Swap) onboarding, which is open and not yet started.
