import os
import json
import sys

def main():
    mapping_path = os.path.join("Info", "reference", "geography_mapping.json")
    print("=" * 80)
    print("GEOGRAPHY MAPPING INTEGRITY VALIDATOR")
    print("=" * 80)
    print(f"Loading reference file: {mapping_path}")

    if not os.path.exists(mapping_path):
        print(f"FAIL: File does not exist at {mapping_path}")
        sys.exit(1)

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("✓ Successfully parsed JSON structure.")
    except Exception as e:
        print(f"FAIL: Invalid JSON syntax or error reading file: {e}")
        sys.exit(1)

    failures = []

    # 1. Validate required top-level sections exist
    required_sections = [
        "metadata",
        "warehouse_mapping",
        "west_malaysia_inland_transportation",
        "sabah_inland_transportation",
        "sarawak_inland_transportation",
        "simple_packing",
        "coordinate_resolution",
        "missing_data_required_before_phase_2c",
        "open_questions"
    ]
    print("\n[Step 1] Checking top-level sections...")
    for sec in required_sections:
        if sec not in data:
            failures.append(f"Missing required top-level section: '{sec}'")
        else:
            print(f"  ✓ Section '{sec}' exists.")

    if failures:
        print(f"\nValidation failed with {len(failures)} errors:")
        for fail in failures:
            print(f"  - {fail}")
        sys.exit(1)

    # 2. Validate metadata
    print("\n[Step 2] Validating metadata safety flags...")
    metadata = data.get("metadata", {})
    if metadata.get("status") != "DISCOVERY_SKELETON":
        failures.append(f"Expected metadata.status == 'DISCOVERY_SKELETON', got: {repr(metadata.get('status'))}")
    else:
        print("  ✓ metadata.status is 'DISCOVERY_SKELETON'")

    if metadata.get("production_ready") is not False:
        failures.append(f"Expected metadata.production_ready == false, got: {metadata.get('production_ready')}")
    else:
        print("  ✓ metadata.production_ready is false (Safe for non-production)")

    # 3. Validate warehouse_mapping
    print("\n[Step 3] Validating warehouse mapping...")
    wh_mapping = data.get("warehouse_mapping", {})
    required_wh_fields = ["West Malaysia", "Sabah", "Sarawak", "Lawas Special Handling Note"]
    for field in required_wh_fields:
        if field not in wh_mapping:
            failures.append(f"Missing field in warehouse_mapping: '{field}'")
        else:
            print(f"  ✓ warehouse_mapping.{field} exists.")

    # 4. Validate Inland Transportation entries
    print("\n[Step 4] Validating Inland Transportation entries...")
    it_sections = [
        "west_malaysia_inland_transportation",
        "sabah_inland_transportation",
        "sarawak_inland_transportation"
    ]
    required_it_fields = ["destination_bucket", "warehouse", "material_code", "direction", "status"]
    
    for sec in it_sections:
        section_data = data.get(sec, {})
        if not isinstance(section_data, dict):
            failures.append(f"Section '{sec}' must be a dictionary.")
            continue
        print(f"  Checking {sec} ({len(section_data)} entries)...")
        for key, entry in section_data.items():
            if not isinstance(entry, dict):
                failures.append(f"Entry '{key}' in section '{sec}' must be an object.")
                continue
            for field in required_it_fields:
                if field not in entry:
                    failures.append(f"Entry '{key}' in section '{sec}' is missing field: '{field}'")
            # Direction check
            direction = entry.get("direction")
            if direction != "warehouse_to_destination":
                failures.append(f"Entry '{key}' in section '{sec}' has invalid direction: '{direction}' (expected 'warehouse_to_destination')")

    # 5. Validate Simple Packing
    print("\n[Step 5] Validating Simple Packing...")
    sp = data.get("simple_packing", {})
    if sp.get("section_status") != "INCOMPLETE":
        failures.append(f"Expected simple_packing.section_status == 'INCOMPLETE', got: {repr(sp.get('section_status'))}")
    else:
        print("  ✓ simple_packing.section_status is 'INCOMPLETE'")

    mappings = sp.get("mappings", {})
    if not isinstance(mappings, dict) or not mappings:
        failures.append("simple_packing.mappings is missing, empty, or not a dictionary.")
    else:
        print(f"  ✓ simple_packing.mappings has {len(mappings)} entries.")
        for key, entry in mappings.items():
            if not isinstance(entry, dict):
                failures.append(f"Simple packing mapping '{key}' is not an object.")
                continue
            if entry.get("direction") != "destination_to_warehouse":
                failures.append(f"Simple packing mapping '{key}' has invalid direction: '{entry.get('direction')}' (expected 'destination_to_warehouse')")

    missing_sp_data = sp.get("missing_simple_packing_data", [])
    if not isinstance(missing_sp_data, list) or not missing_sp_data:
        failures.append("simple_packing.missing_simple_packing_data is empty or not a list.")
    else:
        print(f"  ✓ simple_packing.missing_simple_packing_data is not empty (contains {len(missing_sp_data)} items).")

    # 6. Validate coordinate_resolution
    print("\n[Step 6] Validating coordinate resolution resolution methods...")
    coord = data.get("coordinate_resolution", {})
    if coord.get("status") != "SME_VALIDATION_REQUIRED":
        failures.append(f"Expected coordinate_resolution.status == 'SME_VALIDATION_REQUIRED', got: {repr(coord.get('status'))}")
    else:
        print("  ✓ coordinate_resolution.status is 'SME_VALIDATION_REQUIRED'")

    if coord.get("automatic_gis") is not False:
        failures.append(f"Expected coordinate_resolution.automatic_gis == false, got: {coord.get('automatic_gis')}")
    else:
        print("  ✓ coordinate_resolution.automatic_gis is false")

    if coord.get("google_maps_api_required") is not False:
        failures.append(f"Expected coordinate_resolution.google_maps_api_required == false, got: {coord.get('google_maps_api_required')}")
    else:
        print("  ✓ coordinate_resolution.google_maps_api_required is false")

    # 7. Validate safety lists
    print("\n[Step 7] Checking safety list validations...")
    missing_data = data.get("missing_data_required_before_phase_2c", [])
    if not isinstance(missing_data, list) or not missing_data:
        failures.append("missing_data_required_before_phase_2c is empty or not a list.")
    else:
        print(f"  ✓ missing_data_required_before_phase_2c is not empty (contains {len(missing_data)} items).")

    open_qs = data.get("open_questions", [])
    if not isinstance(open_qs, list) or not open_qs:
        failures.append("open_questions is empty or not a list.")
    else:
        print(f"  ✓ open_questions is not empty (contains {len(open_qs)} items).")

    print("\n" + "=" * 80)
    if failures:
        print(f"RESULT: FAIL ({len(failures)} validation errors detected)")
        print("=" * 80)
        for fail in failures:
            print(f"  - {fail}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("RESULT: PASS (All integrity and safety validations successfully passed!)")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    main()
