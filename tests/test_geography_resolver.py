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

    def test_unresolved_sabah_sarawak_simple_packing(self):
        """Verify that Sabah/Sarawak city buckets fail closed because coordinates resolution is a stub."""
        cities = ["Kuching", "Sibu", "Bintulu", "Miri", "Limbang", "Sri Aman", "Kota Kinabalu", "Sandakan", "Tawau"]

        # All of these are expected to fail-closed with COORDINATE_RESOLUTION_UNSUPPORTED
        for city in cities:
            row = {
                "customer site code": "EM01",
                "region": "Sabah" if "Kota" in city or "Sandakan" in city or "Tawau" in city else "Sarawak",
                "Province/State": city,
                "Latitude (North Plus South Minus)": 5.0,
                "Longitude (East Plus West Minus)": 115.0
            }
            res = self.resolver.resolve_material_code(row, "outbound_route")
            self.assertEqual(res["status"], "REVIEW_REQUIRED")
            self.assertIsNone(res["material_code"])
            self.assertEqual(res["reason_code"], "COORDINATE_RESOLUTION_UNSUPPORTED")

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

        # Lawas Anomaly
        row_lawas = {"customer site code": "EM_L", "region": "Sarawak", "Province/State": "Lawas"}
        res = self.resolver.resolve_material_code(row_lawas, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertIsNone(res["material_code"])
        self.assertEqual(res["reason_code"], "LAWAS_UNRESOLVED")

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

    def test_metadata_safety_integrity(self):
        """Verify safety assertions on metadata block inside geography_mapping.json."""
        meta = self.resolver.mapping_data.get("metadata", {})
        self.assertEqual(meta.get("status"), "DISCOVERY_SKELETON")
        self.assertFalse(meta.get("production_ready"))

        sp = self.resolver.mapping_data.get("simple_packing", {})
        self.assertEqual(sp.get("section_status"), "INCOMPLETE")

if __name__ == "__main__":
    unittest.main()
