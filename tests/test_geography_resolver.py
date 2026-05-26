#!/usr/bin/env python3
"""
tests/test_geography_resolver.py
---------------------------------
Unit tests for the GeographyResolver helper module.
"""

import sys
import os
import unittest
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

    def test_resolve_route_bucket_west_malaysia(self):
        """Verify state and region resolution for West Malaysia."""
        # Confirmed Inland Transportation
        row = {
            "customer site code": "TEST01",
            "region": "Southern",
            "Province/State": "Johor"
        }
        res = self.resolver.resolve_route_bucket(row, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["bucket"], "Johor")
        self.assertEqual(res["reason_code"], "SUCCESS")

        # Missing state
        row_missing_state = {
            "customer site code": "TEST02",
            "region": "Southern"
        }
        res = self.resolver.resolve_route_bucket(row_missing_state, "inbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "MISSING_STATE")

        # Unknown state
        row_unknown_state = {
            "customer site code": "TEST03",
            "region": "Southern",
            "Province/State": "Atlantis"
        }
        res = self.resolver.resolve_route_bucket(row_unknown_state, "inbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "UNKNOWN_STATE")

    def test_resolve_route_bucket_unresolved_simple_packing(self):
        """Verify that unresolved Simple Packing buckets fail closed."""
        # Perlis in North Region
        row_perlis = {
            "customer site code": "TEST04",
            "region": "Northern",
            "Province/State": "Perlis"
        }
        res = self.resolver.resolve_route_bucket(row_perlis, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "NORTH_REGION_UNRESOLVED")

        # Pahang in East Region
        row_pahang = {
            "customer site code": "TEST05",
            "region": "Eastern",
            "Province/State": "Pahang"
        }
        res = self.resolver.resolve_route_bucket(row_pahang, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "EAST_REGION_UNRESOLVED")

    def test_resolve_route_bucket_east_malaysia(self):
        """Verify that East Malaysia coordinate checks fail closed as stubs/unresolved."""
        # Sabah site with coordinates
        row_sabah = {
            "customer site code": "TEST06",
            "region": "Sabah",
            "Latitude (North Plus South Minus)": 5.9,
            "Longitude (East Plus West Minus)": 116.0
        }
        res = self.resolver.resolve_route_bucket(row_sabah, "inbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "COORDINATE_RESOLUTION_UNSUPPORTED")

        # Sarawak Lawas site
        row_lawas = {
            "customer site code": "TEST07",
            "region": "Sarawak",
            "Province/State": "Lawas"
        }
        res = self.resolver.resolve_route_bucket(row_lawas, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertEqual(res["reason_code"], "LAWAS_UNRESOLVED")

    def test_resolve_material_code_confirmed(self):
        """Verify that confirmed material codes resolve successfully."""
        # West Malaysia Inland Transportation
        row_johor = {
            "customer site code": "TEST08",
            "region": "Southern",
            "Province/State": "Johor"
        }
        res = self.resolver.resolve_material_code(row_johor, "inbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000214932")
        self.assertEqual(res["warehouse"], "KV warehouse")

        # West Malaysia Simple Packing
        row_ns = {
            "customer site code": "TEST09",
            "region": "Central",
            "Province/State": "Sembilan"
        }
        res = self.resolver.resolve_material_code(row_ns, "outbound_route")
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["material_code"], "350000589263")
        self.assertEqual(res["warehouse"], "KV warehouse")

    def test_resolve_material_code_fail_closed(self):
        """Verify that unconfirmed/unresolved routes return review required with material code None."""
        row_perlis = {
            "customer site code": "TEST10",
            "region": "Northern",
            "Province/State": "Perlis"
        }
        res = self.resolver.resolve_material_code(row_perlis, "outbound_route")
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertIsNone(res["material_code"])
        self.assertEqual(res["reason_code"], "NORTH_REGION_UNRESOLVED")

if __name__ == "__main__":
    unittest.main()
