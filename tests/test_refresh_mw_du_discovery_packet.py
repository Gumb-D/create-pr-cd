import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from refresh_mw_du_discovery_packet import refresh_discovery_packet


class TestRefreshMwDuDiscoveryPacket(unittest.TestCase):
    def test_refresh_runs_builders_and_guards_in_order(self):
        calls = []

        def mark(name):
            def _inner(*args, **kwargs):
                calls.append(name)
            return _inner

        with (
            patch("refresh_mw_du_discovery_packet.write_registry_outputs", mark("discovery")),
            patch("refresh_mw_du_discovery_packet.write_shortlist_outputs", mark("shortlist")),
            patch("refresh_mw_du_discovery_packet.write_review_outputs", mark("unresolved")),
            patch("refresh_mw_du_discovery_packet.write_grouping_outputs", mark("grouping")),
            patch("refresh_mw_du_discovery_packet.write_bridge_outputs", mark("bridge")),
            patch("refresh_mw_du_discovery_packet.write_pair_outputs", mark("pair")),
            patch("refresh_mw_du_discovery_packet.write_readiness_outputs", mark("readiness")),
            patch("refresh_mw_du_discovery_packet.write_action_queue_outputs", mark("action_queue")),
            patch("refresh_mw_du_discovery_packet.write_review_matrix_outputs", mark("review_matrix")),
            patch("refresh_mw_du_discovery_packet.write_coverage_outputs", mark("coverage")),
            patch("refresh_mw_du_discovery_packet.write_transition_outputs", mark("transition")),
            patch("refresh_mw_du_discovery_packet.write_deprecation_outputs", mark("deprecation")),
            patch("refresh_mw_du_discovery_packet.write_traceability_outputs", mark("traceability")),
            patch("refresh_mw_du_discovery_packet.write_rollback_outputs", mark("rollback")),
            patch("refresh_mw_du_discovery_packet.validate_profiles_against_transition_registry", mark("status_guard")),
            patch("refresh_mw_du_discovery_packet.validate_live_discovery_packets", mark("packet_guard")),
        ):
            refresh_discovery_packet()

        self.assertEqual(
            calls,
            [
                "discovery",
                "shortlist",
                "unresolved",
                "grouping",
                "bridge",
                "pair",
                "readiness",
                "action_queue",
                "review_matrix",
                "coverage",
                "transition",
                "deprecation",
                "rollback",
                "traceability",
                "status_guard",
                "packet_guard",
            ],
        )


if __name__ == "__main__":
    unittest.main()
