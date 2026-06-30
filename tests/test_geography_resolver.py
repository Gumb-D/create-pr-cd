#!/usr/bin/env python3
"""
tests/test_geography_resolver.py
---------------------------------
Unit tests for the GeographyResolver helper module.
This file provides exhaustive test coverage for confirmed West Malaysia states,
unresolved states and territories, missing and unknown data, malformed rows,
invalid route types, and metadata/safety integrity validations.
"""

import sys
import os
import unittest
import json
import tempfile
from pathlib import Path

# Add scripts directory to path to load geography_resolver
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from geography_resolver import GeographyResolver

class TestGeographyResolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = GeographyResolver()

    def test_load_and_validate_mapping(self):
        """Verify that mapping loads successfully and raises error if invalid path."""
        self.assertIsNotNone(self.resolver.mapping_data)
        with self.assertRaises(FileNotFoundError):
            GeographyResolver(mapping_path="Info/reference/non_existent.json")

    def test_normalize_state(self):
        """Verify state name normalizations for Province/State field."""
        self.assertEqual(self.resolver.normalize_state("sembilan"), "Negeri Sembilan")
        self.assertEqual(self.resolver.normalize_state("Negeri Sembilan"), "Negeri Sembilan")
        self.assertEqual(self.resolver.normalize_state("kuala lumpur"), "Kuala Lumpur")
        self.assertEqual(self.resolver.normalize_state("putrajaya"), "Putrajaya")
        self.assertEqual(self.resolver.normalize_state("malacca"), "Melaka")
        self.assertEqual(self.resolver.normalize_state("melaka"), "Melaka")
        self.assertEqual(self.resolver.normalize_state("Johor"), "Johor")
        self.assertIsNone(self.resolver.normalize_state(None))
        self.assertIsNone(self.resolver.normalize_state(""))
        self.assertIsNone(self.resolver.normalize_state("Atlantis"))

    def test_resolve_west_malaysia_state_bucket(self):
        """Verify WM state bucket resolution mapping."""
        # Simple Packing (outbound)
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Selangor", "outbound_route"), "Selangor / Kuala Lumpur")
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Kuala Lumpur", "outbound_route"), "Selangor / Kuala Lumpur")
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Putrajaya", "outbound_route"), "Selangor / Kuala Lumpur")
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Johor", "outbound_route"), "Johor")
        
        # Inland Transportation (inbound)
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Putrajaya", "inbound_route"), "Selangor")
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Selangor", "inbound_route"), "Selangor")
        self.assertEqual(self.resolver.resolve_west_malaysia_state_bucket("Kuala Lumpur", "inbound_route"), "Kuala Lumpur")

    def test_confirmed_simple_packing_west_malaysia(self):
        """Verify confirmed West Malaysia states resolve to correct material codes."""
        # Selangor / Kuala Lumpur
        row_selangor = {"customer site code": "WM01", "region": "Central", "Province/State": "Selangor"}
        res = self.resolver.resolve_material_code(row_selangor, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589232")
        self.assertEqual(res["warehouse"], "KV warehouse")

        row_kl = {"customer site code": "WM02", "region": "Central", "Province/State": "Kuala Lumpur"}
        res = self.resolver.resolve_material_code(row_kl, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589232")

        row_putrajaya = {"customer site code": "WM03", "region": "Central", "Province/State": "Putrajaya"}
        res = self.resolver.resolve_material_code(row_putrajaya, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589232")

        # Negeri Sembilan
        row_ns = {"customer site code": "WM04", "region": "Central", "Province/State": "Sembilan"}
        res = self.resolver.resolve_material_code(row_ns, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589263")

        row_ns2 = {"customer site code": "WM05", "region": "Central", "Province/State": "Negeri Sembilan"}
        res = self.resolver.resolve_material_code(row_ns2, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589263")

        # Melaka / Malacca
        row_melaka = {"customer site code": "WM06", "region": "Southern", "Province/State": "Melaka"}
        res = self.resolver.resolve_material_code(row_melaka, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589264")

        row_malacca = {"customer site code": "WM07", "region": "Southern", "Province/State": "Malacca"}
        res = self.resolver.resolve_material_code(row_malacca, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589264")

        # Johor
        row_johor = {"customer site code": "WM08", "region": "Southern", "Province/State": "Johor"}
        res = self.resolver.resolve_material_code(row_johor, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589265")

    def test_sabah_sarawak_coordinate_resolution_and_simple_packing(self):
        """Verify valid Sabah/Sarawak coordinates resolve to confirmed Simple Packing material codes."""
        cases = [
            ("KK01", "Sabah", "Kota Kinabalu", 5.9804, 116.0735, "350000589313", "Sabah warehouse"),
            ("SDK01", "Sabah", "Sandakan", 5.84, 118.12, "350000589314", "Sabah warehouse"),
            ("TWU01", "Sabah", "Tawau", 4.2607, 117.8768, "350000589315", "Sabah warehouse"),
            ("KCH01", "Sarawak", "Kuching", 1.55, 110.35, "350000589306", "Sarawak warehouse"),
            ("SBU01", "Sarawak", "Sibu", 2.30, 111.83, "350000589307", "Sarawak warehouse"),
            ("BTU01", "Sarawak", "Bintulu", 3.17, 113.04, "350000589308", "Sarawak warehouse"),
            ("MYY01", "Sarawak", "Miri", 4.39, 113.99, "350000589309", "Sarawak warehouse"),
            ("LMN01", "Sarawak", "Limbang", 4.75, 115.00, "350000589310", "Sarawak warehouse"),
            ("SAM01", "Sarawak", "Sri Aman", 1.24, 111.46, "350000589312", "Sarawak warehouse"),
        ]

        for site_code, region, district, lat, lon, material_code, warehouse in cases:
            row = {
                "customer site code": site_code,
                "region": region,
                "Province/State": region,
                "Latitude (North Plus South Minus)": lat,
                "Longitude (East Plus West Minus)": lon,
            }
            res = self.resolver.resolve_material_code(row, "outbound_route")
            self.assertEqual(res["status"], "RESOLVED", district)
            self.assertEqual(res["state"], region)
            self.assertEqual(res["city_or_district"], district)
            self.assertEqual(res["route_bucket"], district)
            self.assertEqual(res["material_code"], material_code)
            self.assertEqual(res["warehouse"], warehouse)

    def test_unresolved_simple_packing_bounds(self):
        """Verify that unresolved Simple Packing buckets for North, East, Lawas, and Labuan fail closed."""
        # North Region states
        north_states = ["Perlis", "Kedah", "Penang", "Perak"]
        for state in north_states:
            row = {"customer site code": "WM_N", "region": "Northern", "Province/State": state}
            res = self.resolver.resolve_material_code(row, "outbound_route")
            self.assertEqual(res["status"], "REVIEW_REQUIRED")
            self.assertIsNone(res["material_code"])
            self.assertEqual(res["reason_code"], "NORTH_REGION_UNRESOLVED")

        # East Region states
        east_states = ["Pahang", "Terengganu", "Kelantan"]
        for state in east_states:
            row = {"customer site code": "WM_E", "region": "Eastern", "Province/State": state}
            res = self.resolver.resolve_material_code(row, "outbound_route")
            self.assertEqual(res["status"], "REVIEW_REQUIRED")
            self.assertIsNone(res["material_code"])
            self.assertEqual(res["reason_code"], "EAST_REGION_UNRESOLVED")

        # Lawas resolves geographically, but Simple Packing remains unconfirmed.
        row_lawas = {
            "customer site code": "EM_L",
            "region": "Sarawak",
            "Province/State": "Sarawak",
            "Latitude (North Plus South Minus)": 4.85,
            "Longitude (East Plus West Minus)": 115.4
        }
        res = self.resolver.resolve_material_code(row_lawas, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertIsNone(res["material_code"])
        self.assertEqual(res["city_or_district"], "Lawas")
        self.assertEqual(res["reason_code"], "LAWAS_SIMPLE_PACKING_UNCONFIRMED")

        # Labuan Anomaly
        row_labuan = {"customer site code": "EM_LB", "region": "Central", "Province/State": "Labuan"}
        res = self.resolver.resolve_material_code(row_labuan, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertIsNone(res["material_code"])
        self.assertEqual(res["reason_code"], "LABUAN_UNRESOLVED")

    def test_unknown_and_missing_data(self):
        """Verify that missing, blank, unknown, or malformed data fails closed."""
        # Missing Province/State (None)
        row_none = {"customer site code": "ERR01", "region": "Central", "Province/State": None}
        res = self.resolver.resolve_material_code(row_none, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "MISSING_STATE")

        # Blank Province/State ("")
        row_blank = {"customer site code": "ERR02", "region": "Central", "Province/State": ""}
        res = self.resolver.resolve_material_code(row_blank, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "UNKNOWN_STATE")

        # Unknown State ("Atlantis")
        row_unknown = {"customer site code": "ERR03", "region": "Central", "Province/State": "Atlantis"}
        res = self.resolver.resolve_material_code(row_unknown, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "UNKNOWN_STATE")

        # Missing Region (None)
        row_no_region = {"customer site code": "ERR04", "Province/State": "Johor"}
        res = self.resolver.resolve_material_code(row_no_region, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "MISSING_REGION")

        # Unknown Region ("Overseas")
        row_wrong_region = {"customer site code": "ERR05", "region": "Overseas", "Province/State": "Johor"}
        res = self.resolver.resolve_material_code(row_wrong_region, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "UNKNOWN_REGION")

        # Unsupported route type
        row_valid = {"customer site code": "ERR06", "region": "Southern", "Province/State": "Johor"}
        res = self.resolver.resolve_material_code(row_valid, "invalid_route_type")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "INVALID_ROUTE_TYPE")

    def test_confirmed_inland_transportation_west_malaysia(self):
        """Verify confirmed West Malaysia Inland Transportation state routes resolve to correct material codes."""
        # Johor
        row_johor = {"customer site code": "WM08", "region": "Southern", "Province/State": "Johor"}
        res = self.resolver.resolve_material_code(row_johor, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000214932")
        self.assertEqual(res["warehouse"], "KV warehouse")

        # Selangor
        row_selangor = {"customer site code": "WM01", "region": "Central", "Province/State": "Selangor"}
        res = self.resolver.resolve_material_code(row_selangor, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000214911")
        self.assertEqual(res["warehouse"], "KV warehouse")

        # Kuala Lumpur
        row_kl = {"customer site code": "WM02", "region": "Central", "Province/State": "Kuala Lumpur"}
        res = self.resolver.resolve_material_code(row_kl, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000214911")

        # Putrajaya
        row_putrajaya = {"customer site code": "WM03", "region": "Central", "Province/State": "Putrajaya"}
        res = self.resolver.resolve_material_code(row_putrajaya, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000214911")

        # Sabah/Sarawak confirmed route buckets resolve by coordinate.
        row_sabah = {"customer site code": "EM_S1", "region": "Sabah", "Province/State": "Sabah", "Latitude (North Plus South Minus)": 5.9804, "Longitude (East Plus West Minus)": 116.0735}
        res_sabah = self.resolver.resolve_material_code(row_sabah, "inbound_route")
        self.assertEqual(res_sabah["status"], "RESOLVED")
        self.assertEqual(res_sabah["route_bucket"], "Kota Kinabalu")
        self.assertEqual(res_sabah["material_code"], "350000212474")

        # Lawas resolves for Inland Transportation.
        row_lawas = {"customer site code": "EM_L1", "region": "Sarawak", "Province/State": "Sarawak", "Latitude (North Plus South Minus)": 4.85, "Longitude (East Plus West Minus)": 115.4}
        res_lawas = self.resolver.resolve_material_code(row_lawas, "inbound_route")
        self.assertEqual(res_lawas["status"], "RESOLVED")
        self.assertEqual(res_lawas["route_bucket"], "Lawas")
        self.assertEqual(res_lawas["material_code"], "350000212473")

    def test_coordinate_validation_failures(self):
        """Verify missing, invalid, non-numeric, and out-of-bound coordinates fail closed."""
        base = {
            "customer site code": "BAD_COORD",
            "region": "Sabah",
            "Province/State": "Sabah",
            "Latitude (North Plus South Minus)": 5.9804,
            "Longitude (East Plus West Minus)": 116.0735,
        }
        cases = [
            ("Latitude (North Plus South Minus)", None, "MISSING_COORDINATES"),
            ("Longitude (East Plus West Minus)", "", "MISSING_COORDINATES"),
            ("Latitude (North Plus South Minus)", 91, "INVALID_COORDINATES"),
            ("Longitude (East Plus West Minus)", 181, "INVALID_COORDINATES"),
            ("Latitude (North Plus South Minus)", "not-a-number", "INVALID_COORDINATES"),
        ]
        for column, value, reason_code in cases:
            row = dict(base)
            row[column] = value
            res = self.resolver.resolve_material_code(row, "inbound_route")
            self.assertEqual(res["status"], "REVIEW_REQUIRED")
            self.assertEqual(res["reason_code"], reason_code)

    def test_coordinate_outside_boundary_and_state_mismatch(self):
        outside = {
            "customer site code": "OUTSIDE",
            "region": "Sabah",
            "Province/State": "Sabah",
            "Latitude (North Plus South Minus)": 0.0,
            "Longitude (East Plus West Minus)": 100.0,
        }
        res = self.resolver.resolve_material_code(outside, "inbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "COORDINATE_OUTSIDE_SUPPORTED_BOUNDARY")

        mismatch = {
            "customer site code": "MISMATCH",
            "region": "Sarawak",
            "Province/State": "Sarawak",
            "Latitude (North Plus South Minus)": 5.9804,
            "Longitude (East Plus West Minus)": 116.0735,
        }
        res = self.resolver.resolve_material_code(mismatch, "inbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "RESOLVED_STATE_MISMATCH")
        self.assertEqual(res["state"], "Sabah")

    def test_excel_route_bucket_mapping(self):
        """Verify Excel business mapping is used before nearest-distance fallback."""

        # Sabah example
        row = {
            "customer site code": "BFT01",
            "region": "Sabah",
            "Province/State": "Sabah",
            "Latitude (North Plus South Minus)": 5.35,
            "Longitude (East Plus West Minus)": 115.75,
        }

        res = self.resolver.resolve_coordinate(row)

        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["city_or_district"], "Beaufort")
        self.assertEqual(res["route_bucket"], "Kota Kinabalu")
        self.assertEqual(res["resolution_method"], "excel_mapping")

        # Sarawak example
        row = {
            "customer site code": "SER01",
            "region": "Sarawak",
            "Province/State": "Sarawak",
            "Latitude (North Plus South Minus)": 1.42,
            "Longitude (East Plus West Minus)": 110.48,
        }

        res = self.resolver.resolve_coordinate(row)

        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["city_or_district"], "Samarahan")
        self.assertEqual(res["route_bucket"], "Kuching")
        self.assertEqual(res["resolution_method"], "excel_mapping")

    def test_unsupported_district_route_mapping_missing(self):
        row = {
            "customer site code": "BFT01",
            "region": "Sabah",
            "Province/State": "Sabah",
            "Latitude (North Plus South Minus)": 5.35,
            "Longitude (East Plus West Minus)": 115.75,
        }
        res = self.resolver.resolve_material_code(row, "inbound_route")

        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["city_or_district"], "Beaufort")

        # Beaufort should now resolve through nearest bucket logic
        self.assertIn(
            res["route_bucket"],
            ["Kota Kinabalu", "Sandakan", "Tawau"]
        )
    def test_mapping_validation_missing_warehouse_and_material_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "mapping.json"
            mapping = json.loads(json.dumps(self.resolver.mapping_data))
            mapping["sabah_inland_transportation"]["Kota Kinabalu"]["warehouse"] = ""
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f)
            resolver = GeographyResolver(mapping_path=tmp_path)
            row = {
                "customer site code": "KK_MISSING_WH",
                "region": "Sabah",
                "Province/State": "Sabah",
                "Latitude (North Plus South Minus)": 5.9804,
                "Longitude (East Plus West Minus)": 116.0735,
            }
            res = resolver.resolve_material_code(row, "inbound_route")
            self.assertEqual(res["reason_code"], "WAREHOUSE_MAPPING_MISSING")

            mapping["sabah_inland_transportation"]["Kota Kinabalu"]["warehouse"] = "Sabah warehouse"
            mapping["sabah_inland_transportation"]["Kota Kinabalu"]["material_code"] = ""
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f)
            resolver = GeographyResolver(mapping_path=tmp_path)
            res = resolver.resolve_material_code(row, "inbound_route")
            self.assertEqual(res["reason_code"], "MATERIAL_CODE_MAPPING_MISSING")

    def test_ambiguous_boundary_fixture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            boundary_path = tmpdir / "boundary.geojson"
            mapping_path = tmpdir / "mapping.json"
            square = [
                [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]
            ]
            data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "bbox": [0.0, 0.0, 1.0, 1.0],
                        "properties": {"state": "Sabah", "district": "Kota Kinabalu"},
                        "geometry": {"type": "Polygon", "coordinates": [square]},
                    },
                    {
                        "type": "Feature",
                        "bbox": [0.0, 0.0, 1.0, 1.0],
                        "properties": {"state": "Sabah", "district": "Sandakan"},
                        "geometry": {"type": "Polygon", "coordinates": [square]},
                    },
                ],
            }
            with open(boundary_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            mapping = json.loads(json.dumps(self.resolver.mapping_data))
            mapping["coordinate_resolution"]["boundary_geojson"] = str(boundary_path)
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f)
            resolver = GeographyResolver(mapping_path=mapping_path)
            row = {
                "customer site code": "AMB01",
                "region": "Sabah",
                "Province/State": "Sabah",
                "Latitude (North Plus South Minus)": 0.5,
                "Longitude (East Plus West Minus)": 0.5,
            }
            res = resolver.resolve_material_code(row, "inbound_route")
            self.assertEqual(res["status"], "REVIEW_REQUIRED")
            self.assertEqual(res["reason_code"], "AMBIGUOUS_DISTRICT_BOUNDARY")

    def test_metadata_safety_integrity(self):
        """Verify safety assertions on metadata block inside geography_mapping.json."""
        meta = self.resolver.mapping_data.get("metadata", {})
        self.assertEqual(meta.get("status"), "DISCOVERY_SKELETON")
        self.assertFalse(meta.get("production_ready"))

        sp = self.resolver.mapping_data.get("simple_packing", {})
        self.assertEqual(sp.get("section_status"), "INCOMPLETE")

    def test_resolver_last_error_propagation(self):
        """Verify that resolver.last_error is correctly populated with structured metadata on failures."""
        # outbound_route Perlis -> NORTH_REGION_UNRESOLVED
        row_perlis = {"customer site code": "WM_N1", "region": "Northern", "Province/State": "Perlis"}
        self.resolver.last_error = None
        self.resolver.resolve_material_code(row_perlis, "outbound_route")
        self.assertIsNotNone(self.resolver.last_error)
        self.assertEqual(self.resolver.last_error["reason_code"], "NORTH_REGION_UNRESOLVED")
        self.assertEqual(self.resolver.last_error["route_type"], "outbound_route")
        self.assertEqual(self.resolver.last_error["bucket"], "Perlis")

        # outbound_route Pahang -> EAST_REGION_UNRESOLVED
        row_pahang = {"customer site code": "WM_E1", "region": "Eastern", "Province/State": "Pahang"}
        self.resolver.last_error = None
        self.resolver.resolve_material_code(row_pahang, "outbound_route")
        self.assertIsNotNone(self.resolver.last_error)
        self.assertEqual(self.resolver.last_error["reason_code"], "EAST_REGION_UNRESOLVED")
        self.assertEqual(self.resolver.last_error["bucket"], "Pahang")

        # outbound_route Lawas -> LAWAS_SIMPLE_PACKING_UNCONFIRMED
        row_lawas = {
            "customer site code": "EM_L1",
            "region": "Sarawak",
            "Province/State": "Sarawak",
            "Latitude (North Plus South Minus)": 4.85,
            "Longitude (East Plus West Minus)": 115.4
        }
        self.resolver.last_error = None
        self.resolver.resolve_material_code(row_lawas, "outbound_route")
        self.assertIsNotNone(self.resolver.last_error)
        self.assertEqual(self.resolver.last_error["reason_code"], "LAWAS_SIMPLE_PACKING_UNCONFIRMED")
        self.assertEqual(self.resolver.last_error["city_or_district"], "Lawas")

        # inbound_route unsupported Sabah district
        # should now auto-resolve using nearest route bucket

        row_sabah = {
            "customer site code": "EM_S1",
            "region": "Sabah",
            "Province/State": "Sabah",
            "Latitude (North Plus South Minus)": 5.35,
            "Longitude (East Plus West Minus)": 115.75
        }

        self.resolver.last_error = None

        result = self.resolver.resolve_material_code(
            row_sabah,
            "inbound_route"
        )

        self.assertEqual(result["status"], "RESOLVED")
        self.assertIsNone(self.resolver.last_error)
        # missing state -> MISSING_STATE
        row_missing_state = {"customer site code": "WM_ERR", "region": "Central", "Province/State": None}
        self.resolver.last_error = None
        self.resolver.resolve_material_code(row_missing_state, "outbound_route")
        self.assertIsNotNone(self.resolver.last_error)
        self.assertEqual(self.resolver.last_error["reason_code"], "MISSING_STATE")

        # unknown state -> UNKNOWN_STATE
        row_unknown_state = {"customer site code": "WM_ERR2", "region": "Central", "Province/State": "Atlantis"}
        self.resolver.last_error = None
        self.resolver.resolve_material_code(row_unknown_state, "outbound_route")
        self.assertIsNotNone(self.resolver.last_error)
        self.assertEqual(self.resolver.last_error["reason_code"], "UNKNOWN_STATE")

if __name__ == "__main__":
    unittest.main()
