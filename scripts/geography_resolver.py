#!/usr/bin/env python3
"""
scripts/geography_resolver.py
-----------------------------
Helper scaffolding for Phase 2C-1 Geography Resolver.
This module is isolated and runs in test-only mode, safely loading and validating
the geography mapping reference file without affecting production ECC generation.
"""

import json
import math
from pathlib import Path

class GeographyResolver:
    def __init__(self, mapping_path="Info/reference/geography_mapping.json"):
        self.mapping_path = Path(mapping_path)
        self.mapping_data = {}
        self.last_error = None
        self.load_and_validate_mapping()

    def load_and_validate_mapping(self):
        """Loads and validates the integrity metadata of geography_mapping.json safely."""
        if not self.mapping_path.exists():
            raise FileNotFoundError(f"Geography mapping file not found at: {self.mapping_path}")

        try:
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                self.mapping_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse geography mapping JSON: {e}")

        # Metadata integrity assertions
        metadata = self.mapping_data.get("metadata", {})
        if "status" not in metadata:
            raise ValueError("Integrity error: metadata.status is missing.")
        
        prod_ready = metadata.get("production_ready", None)
        if prod_ready is not False:
            raise ValueError(f"Integrity error: expected metadata.production_ready to be false, got: {prod_ready}")

        simple_packing = self.mapping_data.get("simple_packing", {})
        sp_status = simple_packing.get("section_status", None)
        if sp_status != "INCOMPLETE":
            raise ValueError(f"Integrity error: expected simple_packing.section_status to be 'INCOMPLETE', got: {sp_status}")

    def normalize_state(self, value):
        """
        Normalizes Province/State field names from the CelcomDigi daily site view sheet.
        Handles common spelling quirks and maps territories. Returns None for unrecognized states.
        """
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None

        val_str = str(value).strip().lower()
        if not val_str:
            return None

        # State Normalization Table
        normalization_map = {
            "sembilan": "Negeri Sembilan",
            "negeri sembilan": "Negeri Sembilan",
            "selangor": "Selangor",
            "kuala lumpur": "Kuala Lumpur",
            "putrajaya": "Putrajaya",
            "penang": "Penang",
            "pulau pinang": "Penang",
            "perak": "Perak",
            "perlis": "Perlis",
            "kedah": "Kedah",
            "pahang": "Pahang",
            "johor": "Johor",
            "kelantan": "Kelantan",
            "terengganu": "Terengganu",
            "melaka": "Melaka",
            "malacca": "Melaka",
            "sabah": "Sabah",
            "sarawak": "Sarawak",
            "labuan": "Labuan"
        }

        return normalization_map.get(val_str, None)

    def resolve_west_malaysia_state_bucket(self, state, route_type):
        """Maps normalized West Malaysia state name into the target JSON mapping bucket name."""
        norm_state = self.normalize_state(state)
        if not norm_state:
            return None

        # Validate that the normalized state belongs to West Malaysia/Labuan
        valid_wm_states = [
            "Selangor", "Kuala Lumpur", "Putrajaya", "Negeri Sembilan", 
            "Penang", "Perak", "Perlis", "Kedah", "Pahang", "Johor", 
            "Kelantan", "Terengganu", "Melaka", "Labuan"
        ]
        if norm_state not in valid_wm_states:
            return None

        if route_type == "outbound_route":  # Simple Packing
            if norm_state in ["Selangor", "Kuala Lumpur", "Putrajaya"]:
                return "Selangor / Kuala Lumpur"
            if norm_state in ["Melaka", "Malacca"]:
                return "Melaka / Malacca"
            return norm_state
        else:  # inbound_route (Inland Transportation)
            if norm_state == "Putrajaya":
                return "Selangor"
            return norm_state

    def resolve_route_bucket(self, site_row, route_type):
        """
        Resolves geographical route bucket from daily site row.
        Returns a dictionary indicating resolution status, resolved bucket name, and reason codes.
        """
        # Ensure row is accessible via get
        row_dict = site_row if isinstance(site_row, dict) else site_row.to_dict()

        site_code = row_dict.get("customer site code", "(unknown)")
        region = str(row_dict.get("region", "")).strip().lower()
        state = row_dict.get("Province/State", None)
        lat = row_dict.get("Latitude (North Plus South Minus)", None)
        lon = row_dict.get("Longitude (East Plus West Minus)", None)

        # Basic inputs validation
        if not region:
            return {
                "status": "REVIEW_REQUIRED",
                "bucket": None,
                "reason_code": "MISSING_REGION",
                "message": f"Site {site_code} is missing broad region field."
            }

        # Determine broad division
        is_west_malaysia = region in ["central", "northern", "southern", "eastern"]
        is_sabah = "sabah" in region
        is_sarawak = "sarawak" in region

        # Handle West Malaysia state buckets
        if is_west_malaysia:
            if state is None or (isinstance(state, float) and math.isnan(state)):
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": None,
                    "reason_code": "MISSING_STATE",
                    "message": f"West Malaysia site {site_code} is missing Province/State field."
                }
            
            norm_state = self.normalize_state(state)
            if not norm_state:
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": None,
                    "reason_code": "UNKNOWN_STATE",
                    "message": f"State '{state}' on site {site_code} is unrecognized."
                }

            if norm_state == "Labuan":
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": None,
                    "reason_code": "LABUAN_UNRESOLVED",
                    "message": f"Labuan territory in site {site_code} cannot be resolved to West Malaysia."
                }

            # Unresolved Simple Packing buckets check for West Malaysia
            if route_type == "outbound_route":
                # Check North Region unresolved alternatives
                if norm_state in ["Perlis", "Kedah", "Penang", "Perak"]:
                    return {
                        "status": "REVIEW_REQUIRED",
                        "bucket": norm_state,
                        "reason_code": "NORTH_REGION_UNRESOLVED",
                        "message": f"Simple Packing for North Region state {norm_state} is unresolved (KV vs Penang warehouse)."
                    }
                # Check East Region unresolved alternatives
                if norm_state in ["Pahang", "Terengganu", "Kelantan"]:
                    return {
                        "status": "REVIEW_REQUIRED",
                        "bucket": norm_state,
                        "reason_code": "EAST_REGION_UNRESOLVED",
                        "message": f"Simple Packing for East Region state {norm_state} is unresolved (KV vs Kuantan warehouse)."
                    }

            resolved_bucket = self.resolve_west_malaysia_state_bucket(norm_state, route_type)
            if not resolved_bucket:
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": None,
                    "reason_code": "UNKNOWN_STATE",
                    "message": f"State '{state}' on site {site_code} is unrecognized."
                }

            return {
                "status": "RESOLVED",
                "bucket": resolved_bucket,
                "reason_code": "SUCCESS",
                "message": f"Successfully mapped to West Malaysia state bucket: {resolved_bucket}"
            }

        # Handle East Malaysia (Sabah / Sarawak) buckets
        elif is_sabah or is_sarawak:
            # We strictly enforce that coordinate resolution is only a stub for now as city/district is absent
            # Check Lawas specifically
            if is_sarawak and str(state).strip().lower() == "lawas":
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": "Lawas",
                    "reason_code": "LAWAS_UNRESOLVED",
                    "message": f"Lawas boundary site {site_code} requires coordinate/manual selection rules (Sabah vs Sarawak)."
                }

            if lat is None or lon is None or (isinstance(lat, float) and math.isnan(lat)) or (isinstance(lon, float) and math.isnan(lon)):
                return {
                    "status": "REVIEW_REQUIRED",
                    "bucket": None,
                    "reason_code": "MISSING_COORDINATES",
                    "message": f"East Malaysia site {site_code} is missing coordinates (Latitude/Longitude)."
                }

            # Coordinates city resolution bounding box stub
            return {
                "status": "REVIEW_REQUIRED",
                "bucket": state,
                "reason_code": "COORDINATE_RESOLUTION_UNSUPPORTED",
                "message": f"City bucket resolution from coordinates ({lat}, {lon}) is currently unsupported for site {site_code}."
            }

        else:
            return {
                "status": "REVIEW_REQUIRED",
                "bucket": None,
                "reason_code": "UNKNOWN_REGION",
                "message": f"Site {site_code} has unrecognized region: {region}"
            }

    def resolve_material_code(self, site_row, route_type):
        """
        Resolves the exact target material code and warehouse from daily site row.
        Fails closed with a structured dict if mapping is incomplete, missing, or ambiguous.
        """
        bucket_res = self.resolve_route_bucket(site_row, route_type)
        if bucket_res["status"] == "REVIEW_REQUIRED":
            res = {
                "status": "REVIEW_REQUIRED",
                "material_code": None,
                "bucket": bucket_res["bucket"],
                "warehouse": None,
                "reason_code": bucket_res["reason_code"],
                "message": bucket_res["message"]
            }
            self.last_error = {
                "route_type": route_type,
                "reason_code": res["reason_code"],
                "bucket": res["bucket"]
            }
            return res

        bucket_name = bucket_res["bucket"]

        # 1. Inland Transportation
        if route_type == "inbound_route":
            region = str(site_row.get("region", "")).strip().lower()
            is_west_malaysia = region in ["central", "northern", "southern", "eastern"]

            if is_west_malaysia:
                mapping_sec = self.mapping_data.get("west_malaysia_inland_transportation", {})
                entry = mapping_sec.get(bucket_name)
                if entry and entry.get("status") == "CONFIRMED":
                    return {
                        "status": "RESOLVED",
                        "material_code": entry.get("material_code"),
                        "bucket": bucket_name,
                        "warehouse": entry.get("warehouse"),
                        "reason_code": "SUCCESS",
                        "message": f"Resolved Inland Transportation route to: {bucket_name}"
                    }
                
                res = {
                    "status": "REVIEW_REQUIRED",
                    "material_code": None,
                    "bucket": bucket_name,
                    "warehouse": None,
                    "reason_code": "INLAND_TRANS_MAPPING_MISSING",
                    "message": f"Inland Transportation mapping missing for West Malaysia state: {bucket_name}"
                }
                self.last_error = {
                    "route_type": route_type,
                    "reason_code": res["reason_code"],
                    "bucket": res["bucket"]
                }
                return res
            
            # Sabah/Sarawak Inland Transportation requires resolved city bucket first (currently stubs)
            res = {
                "status": "REVIEW_REQUIRED",
                "material_code": None,
                "bucket": bucket_name,
                "warehouse": None,
                "reason_code": "COORDINATE_RESOLUTION_UNSUPPORTED",
                "message": "Inland Transportation city resolution not implemented."
            }
            self.last_error = {
                "route_type": route_type,
                "reason_code": res["reason_code"],
                "bucket": res["bucket"]
            }
            return res

        # 2. Simple Packing
        elif route_type == "outbound_route":
            simple_packing = self.mapping_data.get("simple_packing", {})
            mappings = simple_packing.get("mappings", {})

            entry = mappings.get(bucket_name)
            if entry and entry.get("status") == "CONFIRMED":
                return {
                    "status": "RESOLVED",
                    "material_code": entry.get("material_code"),
                    "bucket": bucket_name,
                    "warehouse": entry.get("warehouse"),
                    "reason_code": "SUCCESS",
                    "message": f"Resolved Simple Packing outbound route to: {bucket_name}"
                }

            res = {
                "status": "REVIEW_REQUIRED",
                "material_code": None,
                "bucket": bucket_name,
                "warehouse": None,
                "reason_code": "SIMPLE_PACKING_MAPPING_MISSING",
                "message": f"Simple Packing mapping is missing or unconfirmed for bucket: {bucket_name}"
            }
            self.last_error = {
                "route_type": route_type,
                "reason_code": res["reason_code"],
                "bucket": res["bucket"]
            }
            return res

        else:
            res = {
                "status": "REVIEW_REQUIRED",
                "material_code": None,
                "bucket": bucket_name,
                "warehouse": None,
                "reason_code": "INVALID_ROUTE_TYPE",
                "message": f"Invalid route type requested: {route_type}"
            }
            self.last_error = {
                "route_type": route_type,
                "reason_code": res["reason_code"],
                "bucket": res["bucket"]
            }
            return res

