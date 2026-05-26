#!/usr/bin/env python3
"""
validate_simple_packing_decision_pack.py
----------------------------------------
Validates alignment between:
1. Info/reference/geography_mapping.json
2. Info/reference/SIMPLE_PACKING_UNRESOLVED_DECISION_PACK.md
3. Simple Packing analyzer expectations and safety flags.
"""

import sys
import os
import json
from pathlib import Path

# Paths
GEOGRAPHY_MAPPING_PATH = Path("Info/reference/geography_mapping.json")
DECISION_PACK_PATH = Path("Info/reference/SIMPLE_PACKING_UNRESOLVED_DECISION_PACK.md")

def print_separator():
    print("=" * 100)

def main():
    print_separator()
    print("SIMPLE PACKING DECISION PACK ALIGNMENT VALIDATOR")
    print_separator()

    success = True

    # 1. Load geography_mapping.json
    if not GEOGRAPHY_MAPPING_PATH.exists():
        print(f"❌ ERROR: {GEOGRAPHY_MAPPING_PATH} does not exist.")
        sys.exit(1)

    try:
        with open(GEOGRAPHY_MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
        print(f"✓ Successfully loaded {GEOGRAPHY_MAPPING_PATH}")
    except Exception as e:
        print(f"❌ ERROR: Failed to parse JSON from {GEOGRAPHY_MAPPING_PATH}: {e}")
        sys.exit(1)

    # 2. Load SIMPLE_PACKING_UNRESOLVED_DECISION_PACK.md
    if not DECISION_PACK_PATH.exists():
        print(f"❌ ERROR: {DECISION_PACK_PATH} does not exist.")
        sys.exit(1)

    try:
        with open(DECISION_PACK_PATH, "r", encoding="utf-8") as f:
            md_content = f.read()
        print(f"✓ Successfully loaded {DECISION_PACK_PATH}")
    except Exception as e:
        print(f"❌ ERROR: Failed to read {DECISION_PACK_PATH}: {e}")
        sys.exit(1)

    print_separator()
    print("[STEP 1] Validating Safety Flags in geography_mapping.json...")
    
    metadata = mapping_data.get("metadata", {})
    simple_packing = mapping_data.get("simple_packing", {})

    # Validate metadata production_ready
    prod_ready = metadata.get("production_ready", None)
    if prod_ready is False:
        print("  ✓ metadata.production_ready is false (Safe)")
    else:
        print(f"  ❌ FAIL: metadata.production_ready expected false, got: {prod_ready}")
        success = False

    # Validate metadata status
    status = metadata.get("status", None)
    if status == "DISCOVERY_SKELETON":
        print("  ✓ metadata.status is 'DISCOVERY_SKELETON'")
    else:
        print(f"  ❌ FAIL: metadata.status expected 'DISCOVERY_SKELETON', got: {status}")
        success = False

    # Validate simple_packing section_status
    sec_status = simple_packing.get("section_status", None)
    if sec_status == "INCOMPLETE":
        print("  ✓ simple_packing.section_status is 'INCOMPLETE'")
    else:
        print(f"  ❌ FAIL: simple_packing.section_status expected 'INCOMPLETE', got: {sec_status}")
        success = False

    print_separator()
    print("[STEP 2] Validating Confirmed Simple Packing Mappings...")
    
    expected_mappings = {
        "Selangor / Kuala Lumpur": "350000589232",
        "Negeri Sembilan": "350000589263",
        "Melaka / Malacca": "350000589264",
        "Johor": "350000589265",
        "Kuching": "350000589306",
        "Sibu": "350000589307",
        "Bintulu": "350000589308",
        "Miri": "350000589309",
        "Limbang": "350000589310",
        "Sri Aman": "350000589312",
        "Kota Kinabalu": "350000589313",
        "Sandakan": "350000589314",
        "Tawau": "350000589315"
    }

    mappings = simple_packing.get("mappings", {})
    confirmed_count = 0

    print("  Checking normalized bucket aliases and material codes:")
    for name, code in expected_mappings.items():
        # Handle normalized naming aliases / combined entry explicitly
        matched_key = None
        for key in mappings.keys():
            if key == name or (name in expected_mappings and "/" in name and all(part.strip() in key for part in name.split("/"))):
                matched_key = key
                break
        
        if matched_key:
            entry = mappings[matched_key]
            mcode = entry.get("material_code")
            if mcode == code:
                print(f"    ✓ Found bucket '{matched_key}' mapping to expected code: {mcode}")
                confirmed_count += 1
            else:
                print(f"    ❌ FAIL: Bucket '{matched_key}' found but has material code: {mcode} (expected: {code})")
                success = False
        else:
            # Let's check potential normalizations or exact subsets
            print(f"    ❌ FAIL: Expected bucket mapping for '{name}' was not found.")
            success = False

    print(f"  ✓ Validated {confirmed_count} / {len(expected_mappings)} confirmed simple packing mappings.")

    print_separator()
    print("[STEP 3] Validating Unresolved Alternatives in geography_mapping.json...")
    
    expected_unresolved = {
        "North Region": ["Perlis", "Kedah", "Penang", "Perak"],
        "East Region": ["Pahang", "Terengganu", "Kelantan"],
        "Lawas": ["Lawas"]
    }

    unresolved_alts = simple_packing.get("unresolved_route_alternatives", {})
    unresolved_count = 0

    for region_name, states in expected_unresolved.items():
        if region_name not in unresolved_alts:
            print(f"  ❌ FAIL: Region '{region_name}' not found under unresolved_route_alternatives.")
            success = False
            continue

        region_data = unresolved_alts[region_name]
        print(f"  Checking unresolved region: '{region_name}'")
        for state in states:
            if state not in region_data:
                print(f"    ❌ FAIL: State '{state}' not found under region '{region_name}' unresolved alternatives.")
                success = False
                continue

            alternatives = region_data[state]
            if not isinstance(alternatives, list):
                print(f"    ❌ FAIL: Alternatives for '{state}' must be a list, got: {type(alternatives)}")
                success = False
                continue

            if len(alternatives) < 2:
                print(f"    ❌ FAIL: Alternatives list for '{state}' must contain at least 2 routes, got: {len(alternatives)}")
                success = False
                continue

            print(f"    ✓ State '{state}' has {len(alternatives)} unresolved alternative routes.")
            state_ok = True
            for i, alt in enumerate(alternatives):
                wh = alt.get("warehouse")
                mc = alt.get("material_code")
                direction = alt.get("direction")
                status = alt.get("status")

                if not wh or not mc:
                    print(f"      ❌ FAIL: Route {i+1} in '{state}' is missing 'warehouse' or 'material_code'")
                    state_ok = False
                if direction != "destination_to_warehouse":
                    print(f"      ❌ FAIL: Route {i+1} in '{state}' direction expected 'destination_to_warehouse', got: '{direction}'")
                    state_ok = False
                if status != "SME_VALIDATION_REQUIRED":
                    print(f"      ❌ FAIL: Route {i+1} in '{state}' status expected 'SME_VALIDATION_REQUIRED', got: '{status}'")
                    state_ok = False
            
            if state_ok:
                print(f"      ✓ Route parameters (warehouse, material_code, direction, status) are structurally correct.")
                unresolved_count += 1
            else:
                success = False

    print(f"  ✓ Validated {unresolved_count} unresolved state/bucket alternatives.")

    print_separator()
    print("[STEP 4] Validating Decision Pack Markdown Mentions...")

    required_keywords = {
        "North Region alternatives": ["North Region", "Perlis", "Kedah", "Penang", "Perak"],
        "East Region alternatives": ["East Region", "Pahang", "Terengganu", "Kelantan"],
        "Lawas special handling": ["Lawas", "Sarawak warehouse", "Sabah warehouse", "350000589311", "350000589316"],
        "REVIEW_REQUIRED fail-closed behavior": ["REVIEW_REQUIRED", "fail closed", "SME Decisions"],
        "No silent fallback keyword matching": ["silent fallback", "keyword", "resolver"]
    }

    for desc, keywords in required_keywords.items():
        all_found = True
        missing = []
        for kw in keywords:
            if kw.lower() not in md_content.lower():
                all_found = False
                missing.append(kw)
        
        if all_found:
            print(f"  ✓ Decision pack mentions all terms for: {desc}")
        else:
            print(f"  ❌ FAIL: Decision pack is missing keywords for '{desc}' (Missing: {missing})")
            success = False

    print_separator()
    print("VALIDATION SUMMARY")
    print_separator()
    print(f"Confirmed simple packing mappings validated: {confirmed_count}")
    print(f"Unresolved geographic buckets validated    : {unresolved_count}")
    print(f"Overall status                             : {'PASS' if success else 'FAIL'}")
    print_separator()

    if success:
        print("🎉 ALIGNMENT CHECK PASSED! All JSON structures and markdown references match.")
        sys.exit(0)
    else:
        print("❌ ALIGNMENT CHECK FAILED! Please inspect errors listed above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
