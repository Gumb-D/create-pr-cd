#!/usr/bin/env python3
"""
Deterministic geography and material resolver for TI route choose-groups.

The resolver intentionally fails closed. Coordinates are resolved only through a
checked-in Sabah/Sarawak administrative boundary GeoJSON and checked-in business
mapping tables. No live geocoding service is used by production code.
"""

import json
import math
from pathlib import Path


LATITUDE_COLUMN = "Latitude (North Plus South Minus)"
LONGITUDE_COLUMN = "Longitude (East Plus West Minus)"


REASON_DETAILS = {
    "MISSING_COORDINATES": (
        "Latitude or longitude is missing from the iEPMS site record.",
        "Update site coordinates and rerun PR generation.",
    ),
    "INVALID_COORDINATES": (
        "Latitude or longitude is non-numeric or outside the valid range.",
        "Correct the site latitude and longitude values and rerun PR generation.",
    ),
    "COORDINATE_OUTSIDE_SUPPORTED_BOUNDARY": (
        "The coordinate does not fall within a supported Sabah or Sarawak administrative boundary.",
        "Confirm the site coordinates and supported administrative boundary coverage.",
    ),
    "AMBIGUOUS_DISTRICT_BOUNDARY": (
        "The coordinate falls on or close to multiple administrative boundaries.",
        "Confirm the correct district or city before generating PR.",
    ),
    "RESOLVED_STATE_MISMATCH": (
        "The coordinate resolves to a different state from the declared site region or state.",
        "Confirm the declared region/state and the site coordinates.",
    ),
    "ROUTE_MAPPING_MISSING": (
        "The district was resolved geographically, but no confirmed business route exists.",
        "Obtain a confirmed city/district-to-route bucket mapping from the business owner.",
    ),
    "WAREHOUSE_MAPPING_MISSING": (
        "The route was resolved, but the warehouse mapping is missing or unconfirmed.",
        "Obtain a confirmed warehouse mapping from the business owner.",
    ),
    "MATERIAL_CODE_MAPPING_MISSING": (
        "The route was resolved, but the material code mapping is missing or unconfirmed.",
        "Obtain a confirmed material code from the business owner.",
    ),
    "LAWAS_SIMPLE_PACKING_UNCONFIRMED": (
        "Lawas was resolved geographically, but its Simple Packing business mapping is not confirmed.",
        "Obtain confirmed Lawas Simple Packing warehouse and material code from the business owner.",
    ),
}


class GeographyResolver:
    def __init__(
        self,
        mapping_path="Info/reference/geography_mapping.json",
        boundary_path=None,
        boundary_tolerance_degrees=None,
    ):
        self.mapping_path = Path(mapping_path)
        self.mapping_data = {}
        self.boundary_path = Path(boundary_path) if boundary_path else None
        self.boundary_tolerance_degrees = boundary_tolerance_degrees
        self.boundary_features = []
        self.last_error = None
        self.load_and_validate_mapping()
        self.load_boundary_features()

    def load_and_validate_mapping(self):
        """Loads and validates the integrity metadata of geography_mapping.json safely."""
        if not self.mapping_path.exists():
            raise FileNotFoundError(f"Geography mapping file not found at: {self.mapping_path}")

        try:
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                self.mapping_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse geography mapping JSON: {e}")

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

        if self.boundary_path is None:
            configured_path = self.mapping_data.get("coordinate_resolution", {}).get("boundary_geojson")
            if configured_path:
                self.boundary_path = Path(configured_path)

        tolerance = self.mapping_data.get("coordinate_resolution", {}).get("boundary_tolerance_degrees")
        if self.boundary_tolerance_degrees is None and tolerance is not None:
            self.boundary_tolerance_degrees = float(tolerance)

    def load_boundary_features(self):
        if self.boundary_path is None:
            return
        if not self.boundary_path.exists():
            raise FileNotFoundError(f"Boundary GeoJSON file not found at: {self.boundary_path}")
        with open(self.boundary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("type") != "FeatureCollection":
            raise ValueError(f"Boundary GeoJSON must be a FeatureCollection: {self.boundary_path}")
        self.boundary_features = data.get("features", [])

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
            "labuan": "Labuan",
        }

        return normalization_map.get(val_str, None)

    def resolve_west_malaysia_state_bucket(self, state, route_type):
        """Maps normalized West Malaysia state name into the target JSON mapping bucket name."""
        norm_state = self.normalize_state(state)
        if not norm_state:
            return None

        valid_wm_states = [
            "Selangor", "Kuala Lumpur", "Putrajaya", "Negeri Sembilan",
            "Penang", "Perak", "Perlis", "Kedah", "Pahang", "Johor",
            "Kelantan", "Terengganu", "Melaka", "Labuan",
        ]
        if norm_state not in valid_wm_states:
            return None

        if route_type == "outbound_route":
            if norm_state in ["Selangor", "Kuala Lumpur", "Putrajaya"]:
                return "Selangor / Kuala Lumpur"
            if norm_state in ["Melaka", "Malacca"]:
                return "Melaka / Malacca"
            return norm_state

        if norm_state == "Putrajaya":
            return "Selangor"
        return norm_state

    def _base_result(
        self,
        status,
        reason_code,
        site_code=None,
        state=None,
        city_or_district=None,
        route_bucket=None,
        warehouse=None,
        material_code=None,
        technical_detail=None,
    ):
        description, action = REASON_DETAILS.get(
            reason_code,
            (reason_code.replace("_", " ").title(), "Review the site input and business mapping."),
        )
        return {
            "status": status,
            "state": state,
            "city_or_district": city_or_district,
            "bucket": route_bucket,
            "route_bucket": route_bucket,
            "warehouse": warehouse,
            "material_code": material_code,
            "reason_code": reason_code,
            "reason_description": description,
            "required_action": action,
            "technical_detail": technical_detail or reason_code,
            "message": description,
            "site_code": site_code,
        }

    def _set_last_error(self, result, route_type):
        self.last_error = {
            "route_type": route_type,
            "reason_code": result.get("reason_code"),
            "bucket": result.get("route_bucket") or result.get("bucket"),
            "state": result.get("state"),
            "city_or_district": result.get("city_or_district"),
            "warehouse": result.get("warehouse"),
            "material_code": result.get("material_code"),
            "reason_description": result.get("reason_description"),
            "required_action": result.get("required_action"),
            "technical_detail": result.get("technical_detail"),
        }

    def _row_dict(self, site_row):
        return site_row if isinstance(site_row, dict) else site_row.to_dict()

    def _is_missing_value(self, value):
        if value is None:
            return True
        if isinstance(value, float) and math.isnan(value):
            return True
        return str(value).strip() == ""

    def _parse_coordinate(self, value, min_value, max_value):
        if self._is_missing_value(value):
            return None, "missing"
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None, "invalid"
        if math.isnan(parsed) or parsed < min_value or parsed > max_value:
            return None, "invalid"
        return parsed, None

    def _declared_east_state(self, region, state):
        region_text = str(region or "").strip().lower()
        normalized_state = self.normalize_state(state)
        if "sabah" in region_text:
            return "Sabah"
        if "sarawak" in region_text:
            return "Sarawak"
        if normalized_state in {"Sabah", "Sarawak"}:
            return normalized_state
        return None

    def _bbox_contains(self, bbox, lon, lat):
        return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]

    def _geometry_bbox(self, geometry):
        coords = []

        def walk(value):
            if isinstance(value, list) and value and isinstance(value[0], (int, float)):
                coords.append(value)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(geometry.get("coordinates", []))
        if not coords:
            return None
        xs = [pt[0] for pt in coords]
        ys = [pt[1] for pt in coords]
        return min(xs), min(ys), max(xs), max(ys)

    def _point_on_segment(self, lon, lat, a, b, tolerance):
        ax, ay = a
        bx, by = b
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            return abs(lon - ax) <= tolerance and abs(lat - ay) <= tolerance
        t = ((lon - ax) * dx + (lat - ay) * dy) / (dx * dx + dy * dy)
        if t < 0 or t > 1:
            return False
        proj_x = ax + t * dx
        proj_y = ay + t * dy
        return math.hypot(lon - proj_x, lat - proj_y) <= tolerance

    def _point_in_ring(self, lon, lat, ring):
        inside = False
        if not ring:
            return False
        j = len(ring) - 1
        for i, current in enumerate(ring):
            xi, yi = current[0], current[1]
            xj, yj = ring[j][0], ring[j][1]
            intersects = ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-30) + xi
            )
            if intersects:
                inside = not inside
            j = i
        return inside

    def _point_on_ring_boundary(self, lon, lat, ring, tolerance):
        for i in range(1, len(ring)):
            if self._point_on_segment(lon, lat, ring[i - 1], ring[i], tolerance):
                return True
        return False

    def _point_in_polygon(self, lon, lat, polygon):
        if not polygon:
            return False
        outer = polygon[0]
        if not self._point_in_ring(lon, lat, outer):
            return False
        for hole in polygon[1:]:
            if self._point_in_ring(lon, lat, hole):
                return False
        return True

    def _point_on_polygon_boundary(self, lon, lat, polygon, tolerance):
        for ring in polygon:
            if self._point_on_ring_boundary(lon, lat, ring, tolerance):
                return True
        return False

    def _geometry_contains(self, geometry, lon, lat):
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])
        if geom_type == "Polygon":
            return self._point_in_polygon(lon, lat, coords)
        if geom_type == "MultiPolygon":
            return any(self._point_in_polygon(lon, lat, polygon) for polygon in coords)
        return False

    def _geometry_on_boundary(self, geometry, lon, lat, tolerance):
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])
        if geom_type == "Polygon":
            return self._point_on_polygon_boundary(lon, lat, coords, tolerance)
        if geom_type == "MultiPolygon":
            return any(self._point_on_polygon_boundary(lon, lat, polygon, tolerance) for polygon in coords)
        return False

    def resolve_coordinate(self, site_row):
        row_dict = self._row_dict(site_row)
        site_code = row_dict.get("customer site code", "(unknown)")
        region = row_dict.get("region", "")
        state = row_dict.get("Province/State", None)
        lat_raw = row_dict.get(LATITUDE_COLUMN, None)
        lon_raw = row_dict.get(LONGITUDE_COLUMN, None)

        lat, lat_error = self._parse_coordinate(lat_raw, -90, 90)
        lon, lon_error = self._parse_coordinate(lon_raw, -180, 180)
        if lat_error == "missing" or lon_error == "missing":
            return self._base_result(
                "REVIEW_REQUIRED",
                "MISSING_COORDINATES",
                site_code=site_code,
                technical_detail=f"latitude={lat_raw}; longitude={lon_raw}",
            )
        if lat_error or lon_error:
            return self._base_result(
                "REVIEW_REQUIRED",
                "INVALID_COORDINATES",
                site_code=site_code,
                technical_detail=f"latitude={lat_raw}; longitude={lon_raw}",
            )

        if not self.boundary_features:
            return self._base_result(
                "REVIEW_REQUIRED",
                "COORDINATE_OUTSIDE_SUPPORTED_BOUNDARY",
                site_code=site_code,
                technical_detail="No Sabah/Sarawak boundary features are loaded.",
            )

        matches = []
        boundary_matches = []
        tolerance = float(self.boundary_tolerance_degrees or 0.0)
        for feature in self.boundary_features:
            geometry = feature.get("geometry") or {}
            bbox = feature.get("bbox") or self._geometry_bbox(geometry)
            if bbox and not self._bbox_contains(bbox, lon, lat):
                if tolerance <= 0:
                    continue
                expanded = [bbox[0] - tolerance, bbox[1] - tolerance, bbox[2] + tolerance, bbox[3] + tolerance]
                if not self._bbox_contains(expanded, lon, lat):
                    continue

            if tolerance > 0 and self._geometry_on_boundary(geometry, lon, lat, tolerance):
                boundary_matches.append(feature)
            if self._geometry_contains(geometry, lon, lat):
                matches.append(feature)

        unique_matches = {feature.get("properties", {}).get("district"): feature for feature in matches}
        unique_boundary = {feature.get("properties", {}).get("district"): feature for feature in boundary_matches}

        if len(unique_matches) != 1 or len(unique_boundary) > 1:
            names = sorted(name for name in set(unique_matches) | set(unique_boundary) if name)
            if names:
                return self._base_result(
                    "REVIEW_REQUIRED",
                    "AMBIGUOUS_DISTRICT_BOUNDARY",
                    site_code=site_code,
                    technical_detail=f"matches={names}; latitude={lat}; longitude={lon}",
                )
            return self._base_result(
                "REVIEW_REQUIRED",
                "COORDINATE_OUTSIDE_SUPPORTED_BOUNDARY",
                site_code=site_code,
                technical_detail=f"latitude={lat}; longitude={lon}",
            )

        feature = next(iter(unique_matches.values()))
        properties = feature.get("properties", {})
        resolved_state = properties.get("state")
        district = properties.get("district")
        declared_state = self._declared_east_state(region, state)
        if declared_state and resolved_state and declared_state != resolved_state:
            return self._base_result(
                "REVIEW_REQUIRED",
                "RESOLVED_STATE_MISMATCH",
                site_code=site_code,
                state=resolved_state,
                city_or_district=district,
                technical_detail=(
                    f"declared_state={declared_state}; resolved_state={resolved_state}; "
                    f"district={district}; latitude={lat}; longitude={lon}"
                ),
            )

        route_bucket = self._district_route_bucket(resolved_state, district)
        if not route_bucket:
            return self._base_result(
                "REVIEW_REQUIRED",
                "ROUTE_MAPPING_MISSING",
                site_code=site_code,
                state=resolved_state,
                city_or_district=district,
                technical_detail=f"state={resolved_state}; district={district}; latitude={lat}; longitude={lon}",
            )

        return self._base_result(
            "RESOLVED",
            "SUCCESS",
            site_code=site_code,
            state=resolved_state,
            city_or_district=district,
            route_bucket=route_bucket,
            technical_detail=f"state={resolved_state}; district={district}; route_bucket={route_bucket}",
        )

    def _district_route_bucket(self, state, district):
        section = self.mapping_data.get("coordinate_resolution", {}).get("district_route_buckets", {})
        return section.get(state, {}).get(district)

    def resolve_route_bucket(self, site_row, route_type):
        """
        Resolves geographical route bucket from daily site row.
        Returns a dictionary indicating resolution status, resolved bucket name, and reason codes.
        """
        row_dict = self._row_dict(site_row)
        site_code = row_dict.get("customer site code", "(unknown)")
        region = str(row_dict.get("region", "")).strip().lower()
        state = row_dict.get("Province/State", None)

        if not region:
            return self._base_result(
                "REVIEW_REQUIRED",
                "MISSING_REGION",
                site_code=site_code,
                technical_detail=f"Site {site_code} is missing broad region field.",
            )

        is_west_malaysia = region in ["central", "northern", "southern", "eastern"]
        is_sabah = "sabah" in region
        is_sarawak = "sarawak" in region

        if is_west_malaysia:
            if state is None or (isinstance(state, float) and math.isnan(state)):
                return self._base_result(
                    "REVIEW_REQUIRED",
                    "MISSING_STATE",
                    site_code=site_code,
                    technical_detail=f"West Malaysia site {site_code} is missing Province/State field.",
                )

            norm_state = self.normalize_state(state)
            if not norm_state:
                return self._base_result(
                    "REVIEW_REQUIRED",
                    "UNKNOWN_STATE",
                    site_code=site_code,
                    technical_detail=f"State '{state}' on site {site_code} is unrecognized.",
                )

            if norm_state == "Labuan":
                return self._base_result(
                    "REVIEW_REQUIRED",
                    "LABUAN_UNRESOLVED",
                    site_code=site_code,
                    state=norm_state,
                    technical_detail=f"Labuan territory in site {site_code} cannot be resolved to West Malaysia.",
                )

            if route_type == "outbound_route":
                if norm_state in ["Perlis", "Kedah", "Penang", "Perak"]:
                    return self._base_result(
                        "REVIEW_REQUIRED",
                        "NORTH_REGION_UNRESOLVED",
                        site_code=site_code,
                        state=norm_state,
                        route_bucket=norm_state,
                        technical_detail=f"Simple Packing for North Region state {norm_state} is unresolved.",
                    )
                if norm_state in ["Pahang", "Terengganu", "Kelantan"]:
                    return self._base_result(
                        "REVIEW_REQUIRED",
                        "EAST_REGION_UNRESOLVED",
                        site_code=site_code,
                        state=norm_state,
                        route_bucket=norm_state,
                        technical_detail=f"Simple Packing for East Region state {norm_state} is unresolved.",
                    )

            resolved_bucket = self.resolve_west_malaysia_state_bucket(norm_state, route_type)
            if not resolved_bucket:
                return self._base_result(
                    "REVIEW_REQUIRED",
                    "UNKNOWN_STATE",
                    site_code=site_code,
                    technical_detail=f"State '{state}' on site {site_code} is unrecognized.",
                )

            return self._base_result(
                "RESOLVED",
                "SUCCESS",
                site_code=site_code,
                state=norm_state,
                city_or_district=norm_state,
                route_bucket=resolved_bucket,
                technical_detail=f"Successfully mapped to West Malaysia state bucket: {resolved_bucket}",
            )

        if is_sabah or is_sarawak:
            return self.resolve_coordinate(site_row)

        return self._base_result(
            "REVIEW_REQUIRED",
            "UNKNOWN_REGION",
            site_code=site_code,
            technical_detail=f"Site {site_code} has unrecognized region: {region}",
        )

    def _mapping_section_for_route(self, route_type, state):
        if route_type == "outbound_route":
            return self.mapping_data.get("simple_packing", {}).get("mappings", {})
        if route_type == "inbound_route":
            if state == "Sabah":
                return self.mapping_data.get("sabah_inland_transportation", {})
            if state == "Sarawak":
                return self.mapping_data.get("sarawak_inland_transportation", {})
            return self.mapping_data.get("west_malaysia_inland_transportation", {})
        return None

    def resolve_material_code(self, site_row, route_type):
        """
        Resolves the exact target material code and warehouse from daily site row.
        Fails closed with a structured dict if mapping is incomplete, missing, or ambiguous.
        """
        self.last_error = None
        if route_type not in {"inbound_route", "outbound_route"}:
            result = self._base_result(
                "REVIEW_REQUIRED",
                "INVALID_ROUTE_TYPE",
                technical_detail=f"Invalid route type requested: {route_type}",
            )
            self._set_last_error(result, route_type)
            return result

        bucket_res = self.resolve_route_bucket(site_row, route_type)
        if bucket_res["status"] == "REVIEW_REQUIRED":
            self._set_last_error(bucket_res, route_type)
            return bucket_res

        bucket_name = bucket_res["route_bucket"]
        mapping_sec = self._mapping_section_for_route(route_type, bucket_res.get("state"))
        entry = mapping_sec.get(bucket_name) if mapping_sec else None

        if bucket_name == "Lawas" and route_type == "outbound_route":
            result = self._base_result(
                "REVIEW_REQUIRED",
                "LAWAS_SIMPLE_PACKING_UNCONFIRMED",
                site_code=bucket_res.get("site_code"),
                state=bucket_res.get("state"),
                city_or_district=bucket_res.get("city_or_district"),
                route_bucket=bucket_name,
                technical_detail="Lawas Simple Packing has multiple SME_VALIDATION_REQUIRED alternatives and no confirmed mapping.",
            )
            self._set_last_error(result, route_type)
            return result

        if not entry or entry.get("status") != "CONFIRMED":
            result = self._base_result(
                "REVIEW_REQUIRED",
                "ROUTE_MAPPING_MISSING",
                site_code=bucket_res.get("site_code"),
                state=bucket_res.get("state"),
                city_or_district=bucket_res.get("city_or_district"),
                route_bucket=bucket_name,
                technical_detail=f"Missing confirmed mapping for route_type={route_type}; bucket={bucket_name}",
            )
            self._set_last_error(result, route_type)
            return result

        warehouse = str(entry.get("warehouse") or "").strip()
        material_code = str(entry.get("material_code") or "").strip()
        if not warehouse:
            result = self._base_result(
                "REVIEW_REQUIRED",
                "WAREHOUSE_MAPPING_MISSING",
                site_code=bucket_res.get("site_code"),
                state=bucket_res.get("state"),
                city_or_district=bucket_res.get("city_or_district"),
                route_bucket=bucket_name,
                technical_detail=f"Confirmed mapping has blank warehouse for route_type={route_type}; bucket={bucket_name}",
            )
            self._set_last_error(result, route_type)
            return result
        if not material_code:
            result = self._base_result(
                "REVIEW_REQUIRED",
                "MATERIAL_CODE_MAPPING_MISSING",
                site_code=bucket_res.get("site_code"),
                state=bucket_res.get("state"),
                city_or_district=bucket_res.get("city_or_district"),
                route_bucket=bucket_name,
                warehouse=warehouse,
                technical_detail=f"Confirmed mapping has blank material code for route_type={route_type}; bucket={bucket_name}",
            )
            self._set_last_error(result, route_type)
            return result

        return self._base_result(
            "RESOLVED",
            "SUCCESS",
            site_code=bucket_res.get("site_code"),
            state=bucket_res.get("state"),
            city_or_district=bucket_res.get("city_or_district"),
            route_bucket=bucket_name,
            warehouse=warehouse,
            material_code=material_code,
            technical_detail=f"route_type={route_type}; bucket={bucket_name}; material_code={material_code}",
        )
