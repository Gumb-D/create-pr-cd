# Business Rules Reference - MW New Link / Reroute

## Context
This document summarizes the business rules implemented in the `create-pr-cd` skill for handling "MW New Link / Reroute" SOW items. These rules ensure consistent and correct ECC output.

---

## Rule Table

| Rule # | Rule Name | Description | Conditions | Output |
|--------|-----------|-------------|------------|--------|
| **1** | **LOS Survey Selection - Reroute without LOS** | For MW Reroute projects on non-LOS sites | SOW = "MW New Link / Reroute"<br>TX Upgrade Scope **contains** "dismantle"<br>Site ID **does NOT** contain "_LOS" | **350000062773** (quantity = 1) |
| **2** | **LOS Survey Selection - Reroute with LOS** | For MW Reroute projects on LOS sites | SOW = "MW New Link / Reroute"<br>TX Upgrade Scope **contains** "dismantle"<br>Site ID **contains** "_LOS" | **350000062776** (quantity = 1) |
| **3** | **LOS Survey Selection - New Link** | For MW New Link projects (any site) | SOW = "MW New Link / Reroute"<br>TX Upgrade Scope **does NOT** contain "dismantle" | **350000062773** (quantity = 1) <br>*(ignores _LOS pattern)* |
| **4** | **Quantity Enforcement - Reroute** | For MW Reroute, specific items must have 1.5 hop | SOW = "MW New Link / Reroute"<br>Applies to PBOM: 350000589343, 350000589344<br>Condition: `is_mw_reroute = True` | **Quantity = 1.5**<br>Reject entries with quantity = 1.0 |
| **5** | **Quantity Enforcement - New Link** | For MW New Link, specific items must have 1 hop | SOW = "MW New Link / Reroute"<br>Applies to PBOM: 350000589343, 350000589344<br>Condition: `is_mw_reroute = False` | **Quantity = 1.0**<br>Reject entries with quantity = 1.5 |

---

## Decision Flowchart

```
Start: Site with Tx SOW = "MW New Link / Reroute
   │
   ├─ Read TX Upgrade Scope
   │      │
   │      ├─ Contains "dismantle"? ──Yes─→ MW Reroute
   │      │                              │
   │      No                              ├─ Site ID contains "_LOS"?
   │      │                              │      │
   │      └─→ MW New Link                 │      Yes ─→ Select 350000062776
   │                                      │      │      Set quantity: 1.5 for 589343/344
   │                                      │      No ──→ Select 350000062773
   │                                      │             Set quantity: 1.5 for 589343/344
   │                                      │
   │                                      └─ For New Link: Select 350000062773
   │                                                 Set quantity: 1.0 for 589343/344
   │
   └─ Apply filters to eliminate duplicate PR model entries
```

---

## Field References

| Field Name | Source | Purpose |
|------------|--------|---------|
| `Tx SOW` | Site Data Input | Must equal "MW New Link / Reroute" (exact match, case-insensitive) |
| `TX Upgrade Scope` | Site Data Input | Determines Reroute vs New Link by presence of "dismantle" |
| `Site ID` | Site Data Input | Determines LOS Survey selection (checks for "_LOS" substring) |
| `PBOM Code` | PR Model Reference | Matched items filtered by rules above |
| `Quantity` | PR Model Reference | Filtered based on Reroute/New Link determination |

---

## Examples

### Example 1: New Link Project (Non-LOS Site)
**Input**:
- Tx SOW: "MW New Link / Reroute"
- TX Upgrade Scope: "MW deployment" (no "dismantle")
- Site ID: "A01073_AD"

**Processing**:
1. is_mw_reroute = False
2. Rule 3 applies → Select 350000062773
3. Rule 5 applies → 350000589343/344 must have quantity 1.0

**Output Items**:
| PBOM Code | SOW Description | Quantity |
|-----------|-----------------|----------|
| 350000062773 | LOS Survey | 1 |
| 350000589343 | Item A (example) | 1.0 |
| 350000589344 | Item B (example) | 1.0 |

---

### Example 2: Reroute Project (Non-LOS Site)
**Input**:
- Tx SOW: "MW New Link / Reroute"
- TX Upgrade Scope: "MW dismantle and reinstall" (contains "dismantle")
- Site ID: "B00256"

**Processing**:
1. is_mw_reroute = True
2. Site ID has no "_LOS" → Rule 1 applies → Select 350000062773
3. Rule 4 applies → 350000589343/344 must have quantity 1.5

**Output Items**:
| PBOM Code | SOW Description | Quantity |
|-----------|-----------------|----------|
| 350000062773 | LOS Survey | 1 |
| 350000589343 | Item A (example) | 1.5 |
| 350000589344 | Item B (example) | 1.5 |

---

### Example 3: Reroute Project (LOS Site)
**Input**:
- Tx SOW: "MW New Link / Reroute"
- TX Upgrade Scope: "dismantle existing MW link" (contains "dismantle")
- Site ID: "SITE_LOS_001"

**Processing**:
1. is_mw_reroute = True
2. Site ID contains "_LOS" → Rule 2 applies → Select 350000062776
3. Rule 4 applies → 350000589343/344 must have quantity 1.5

**Output Items**:
| PBOM Code | SOW Description | Quantity |
|-----------|-----------------|----------|
| 350000062776 | LOS Survey | 1 |
| 350000589343 | Item A (example) | 1.5 |
| 350000589344 | Item B (example) | 1.5 |

---

## PR Model Filtering Logic

The PR model contains duplicate entries for some PBOMs. The filtering logic removes entries that don't match the scenario:

**Original PR Model Entries** (simplified):
| SOW | PBOM | Quantity |
|-----|------|----------|
| MW New Link / Reroute | 350000062773 | 1 |
| MW New Link / Reroute | 350000062776 | 1 |
| MW New Link / Reroute | 350000589343 | 1.0 |
| MW New Link / Reroute | 350000589343 | 1.5 |
| MW New Link / Reroute | 350000589344 | 1.0 |
| MW New Link / Reroute | 350000589344 | 1.5 |

**Filtered Result** (depending on scenario):
- **New Link**: Keep only 350000062773 + 350000589343(qty=1.0) + 350000589344(qty=1.0)
- **Reroute**: Keep only appropriate survey + 350000589343(qty=1.5) + 350000589344(qty=1.5)

---

## Validation Criteria

✅ **No duplicate PBOMs** in final output  
✅ **Correct LOS Survey** selected based on rules  
✅ **Consistent quantities** for 350000589343/344 across all rows  
✅ **Other MW SOWs** (e.g., MW Swap, MW Hardware Upgrade) are **unaffected** by these rules

---

## Related Files

- `scripts/generate_tss_pr_ecc.py` - Implementation
- `SKILL.md` - Technical documentation
- `CHANGELOG.md` - Version history
- `test_fix.py` - Test script
- `VALIDATION_REPORT.md` - Detailed test results

---

**Last Updated**: 2025-06-24  
**Owner**: create-pr-cd skill development team  
**Status**: Production Ready