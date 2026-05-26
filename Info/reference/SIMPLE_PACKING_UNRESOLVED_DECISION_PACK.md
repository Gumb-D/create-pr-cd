# Simple Packing Unresolved Decision Pack

## 1. Purpose
This document serves as a comprehensive business and SME (Subject Matter Expert) decision pack for unresolved **Simple Packing and Inland Transportation** mapping rules within the `create-pr-cd` repository. 

To prevent errors, regressions, or incorrect automated PR generation, programmatic resolvers cannot be deployed to production until these warehouse assignment and boundary rules are explicitly confirmed by the business.

---

## 2. Current Confirmed Simple Packing Mappings
The following safe, unambiguous **one-to-one** Simple Packing mappings have been verified against the PR model and are currently registered in `geography_mapping.json`:

| Destination State / Region | Inferred Bucket | target Warehouse | Simple Packing Material Code | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Selangor / Kuala Lumpur** | `KV Region exact site location` | KV warehouse | `350000589232` | CONFIRMED |
| **Negeri Sembilan** | `Negeri Sembilan` | KV warehouse | `350000589263` | CONFIRMED |
| **Melaka / Malacca** | `Melaka / Malacca` | KV warehouse | `350000589264` | CONFIRMED |
| **Johor** | `Johor` | KV warehouse | `350000589265` | CONFIRMED |
| **Kuching** | `Kuching` | Sarawak warehouse | `350000589306` | CONFIRMED |
| **Sibu** | `Sibu` | Sarawak warehouse | `350000589307` | CONFIRMED |
| **Bintulu** | `Bintulu` | Sarawak warehouse | `350000589308` | CONFIRMED |
| **Miri** | `Miri` | Sarawak warehouse | `350000589309` | CONFIRMED |
| **Limbang** | `Limbang` | Sarawak warehouse | `350000589310` | CONFIRMED |
| **Sri Aman** | `Sri Aman` | Sarawak warehouse | `350000589312` | CONFIRMED |
| **Kota Kinabalu** | `Kota Kinabalu` | Sabah warehouse | `350000589313` | CONFIRMED |
| **Sandakan** | `Sandakan` | Sabah warehouse | `350000589314` | CONFIRMED |
| **Tawau** | `Tawau` | Sabah warehouse | `350000589315` | CONFIRMED |

---

## 3. Unresolved North Region Alternatives
In the North Region, sites can be routed to either the **KV Warehouse** or the regional **Penang Warehouse**, resulting in duplicate mapping alternatives in the PR model.

### Mapping Alternatives:
*   **Perlis:**
    *   *Option A (KV Warehouse):* `350000589241` ("North Region to KV warehouse--Perlis exact site location for MW")
    *   *Option B (Penang Warehouse):* `350000589254` ("North Region to Penang warehouse--Perlis exact site location for MW")
*   **Kedah:**
    *   *Option A (KV Warehouse):* `350000589242` ("North Region to KV warehouse--Kedah exact site location for MW")
    *   *Option B (Penang Warehouse):* `350000589255` ("North Region to Penang warehouse--Kedah exact site location for MW")
*   **Penang:**
    *   *Option A (KV Warehouse):* `350000589243` ("North Region to KV warehouse--Penang exact site location for MW")
    *   *Option B (Penang Warehouse):* `350000589253` ("North Region to Penang warehouse--Penang exact site location for MW")
*   **Perak:**
    *   *Option A (KV Warehouse):* `350000589244` ("North Region to KV warehouse--Perak exact site location for MW")
    *   *Option B (Penang Warehouse):* `350000589256` ("North Region to Penang warehouse--Perak exact site location for MW")

### Why a Decision is Required:
A programmatic resolver cannot determine whether a site in Perlis, Kedah, Penang, or Perak should route to KV Warehouse or Penang Warehouse. We require a clear business rule (e.g., depending on the subcontractor, regional contract boundary, or a static default) to select the correct material code.

---

## 4. Unresolved East Region Alternatives
In the East Region, sites can be routed to either the **KV Warehouse** or the regional **Kuantan Warehouse**, resulting in duplicate mapping alternatives in the PR model.

### Mapping Alternatives:
*   **Pahang:**
    *   *Option A (KV Warehouse):* `350000589272` ("East Region to KV warehouse--Pahang exact site location for MW")
    *   *Option B (Kuantan Warehouse):* `350000589281` ("East Region to Kuantan warehouse--Pahang exact site location for MW")
*   **Terengganu:**
    *   *Option A (KV Warehouse):* `350000589273` ("East Region to KV warehouse--Terengganu exact site location for MW")
    *   *Option B (Kuantan Warehouse):* `350000589282` ("East Region to Kuantan warehouse--Terengganu exact site location for MW")
*   **Kelantan:**
    *   *Option A (KV Warehouse):* `350000589274` ("East Region to KV warehouse--Kelantan exact site location for MW")
    *   *Option B (Kuantan Warehouse):* `350000589283` ("East Region to Kuantan warehouse--Kelantan exact site location for MW")

### Why a Decision is Required:
A programmatic resolver cannot determine whether a site in Pahang, Terengganu, or Kelantan should route to KV Warehouse or Kuantan Warehouse. A specific business logic rule must be defined to select the correct code.

---

## 5. Lawas Special Handling
Lawas acts as a geographic boundary anomaly between Sabah and Sarawak. The PR model specifies two separate Simple Packing PBOM codes for Lawas depending on the destination warehouse:

*   **Lawas to Sarawak:** `350000589311` ("Simple Packing and Inland transportation from Lawas to Salawak warehouse for MW")
*   **Lawas to Sabah:** `350000589316` ("Simple Packing and Inland transportation from Lawas to Sabah warehouse for MW")

### Why a Decision is Required:
Because Lawas sits on the regional border, programmatic routing requires a coordinate-based threshold rule, specific site-code list, or manual override rule to assign the correct warehouse.

---

## 6. Suspicious / Unknown Bucket Rows

### A. Suspicious Multiple-Keyword Match Rows
The mapping analyzer flagged **21 rows** under the North Region as "suspicious" because their descriptions mention both a regional state (Perlis, Kedah, Perak) and the "Penang warehouse" (e.g., Rows 79, 80, 81, 167, 168, 169, 238, 239, 240, 345, 346, 347, 405, 406, 407, 465, 466, 467, 495, 496, 497). 

*   *Implication:* A simple keyword matcher looking for "Penang" will incorrectly assign these to the Penang state bucket instead of their true physical site locations (Perlis, Kedah, Perak). 
*   *Correction Rule:* The parsing resolver must prioritize the **exact site location** suffix (e.g., `Perlis exact site location`) over the warehouse prefix (e.g., `Penang warehouse`) to extract the correct geographic state.

### B. General "Unknown" KV Region Rows
The mapping analyzer identified **7 rows** (Rows 73, 161, 232, 339, 399, 459, 489) that contain general descriptions such as:
`Simple Packing and Inland transportation from KV Region exact site location to KV warehouse for MW`

*   *Implication:* These do not mention a specific state (e.g., Selangor or Kuala Lumpur) in the description text. 
*   *Correction Rule:* These general items must be programmatically associated with the core `Selangor / Kuala Lumpur` (KV Region) bucket.

---

## 7. Required SME Decisions

Please review and provide explicit confirmation for the following routing rules:

- [ ] **1. North Region Warehouse Routing Rule:**
  Which warehouse destination should sites in **Perlis, Kedah, Penang, and Perak** use by default?
  *   *Options:* Always KV Warehouse, Always Penang Warehouse, Subcontractor-dependent (please specify), or Contract-dependent (please specify).

- [ ] **2. East Region Warehouse Routing Rule:**
  Which warehouse destination should sites in **Pahang, Terengganu, and Kelantan** use by default?
  *   *Options:* Always KV Warehouse, Always Kuantan Warehouse, Subcontractor-dependent (please specify), or Contract-dependent (please specify).

- [ ] **3. Lawas Warehouse Assignment Rule:**
  How should the resolver decide whether a site located in **Lawas** routes to the Sabah warehouse (`350000589316`) or the Sarawak warehouse (`350000589311`)?
  *   *Options:* Coordinate boundary (GIS), Site code suffix list, or manual override table.

- [ ] **4. Unknown / Ambiguous Bucket Resolver Safety:**
  Should the resolver "fail closed" by triggering a `REVIEW_REQUIRED` state and writing details to the review CSV if a site has an unknown coordinate, missing state, or ambiguous routing alternative?
  *   *Options:* Yes (Highly Recommended for production safety), or No (silently fallback to a default).

- [ ] **5. Province/State Column Reliability:**
  Can the `Province/State` column in the daily `Site PR/PO View` sheet be 100% trusted for West Malaysia state categorization?
  *   *Options:* Yes, or No (need secondary verification via City/Postcode).

- [ ] **6. Site Code Override Table:**
  Should we implement a static site-code override mapping table to handle exceptions where standard routing logic is intentionally bypassed?
  *   *Options:* Yes, or No.

---

## 8. Recommended Resolver Behavior After SME Confirmation

Once the decisions above are finalized, we recommend implementing the programmatic `GeographyResolver` with the following robust behaviors:

1.  **Confirmed Bucket Matching:** If a site maps to a confirmed bucket, output the exact corresponding material code directly.
2.  **Unresolved/Ambiguous Bucket Routing:** If a site belongs to the North Region, East Region, or Lawas, the resolver must apply the confirmed SME routing rules (e.g., check subcon or site code suffix). If the rule cannot resolve the ambiguity, trigger `REVIEW_REQUIRED` and write to the review CSV.
3.  **Unknown/Out-of-Bounds Buckets:** If a site lacks coordinate data or falls outside known state buckets, immediately trigger `REVIEW_REQUIRED` to halt automated execution and alert the operator.
4.  **No Silent Fallbacks:** Under no circumstances should the resolver perform a silent default guess or keyword fallback when a regional boundary is ambiguous.
