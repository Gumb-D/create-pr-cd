# DU Export Adapter Foundation

This change introduces only a safe foundation. The current runtime remains unchanged: it accepts the existing normalized site input and supports only TSS and TI.

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

The initial TX Mini profile is deliberately DRAFT. It contains no approved fingerprints or Header Hash because no original four-header source fixture is committed in this repository.

Next delivery: formalize TX Mini source fingerprints and prove golden output equality before any runtime integration.
