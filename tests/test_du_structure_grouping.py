import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_du_structure_grouping import (
    build_grouping_entry,
    fingerprint_similarity,
    grouping_markdown,
    load_profile_artifact,
)


class TestDuStructureGrouping(unittest.TestCase):
    def test_fingerprint_similarity_uses_jaccard_overlap(self):
        left = {"a", "b", "c"}
        right = {"b", "c", "d"}

        score = fingerprint_similarity(left, right)

        self.assertAlmostEqual(score, 0.5)

    def test_build_grouping_entry_identifies_closest_neighbors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            alpha = root / "alpha"
            beta = root / "beta"
            gamma = root / "gamma"
            alpha.mkdir()
            beta.mkdir()
            gamma.mkdir()
            alpha_inventory = {
                "source": {"file_name": "alpha.xlsx"},
                "sheets": [{"sheet_name": "data", "columns": [
                    {"fingerprint": {"field_code": "a", "wbs_stage": "1", "task_name": "1", "display_header": "A"}},
                    {"fingerprint": {"field_code": "b", "wbs_stage": "1", "task_name": "1", "display_header": "B"}},
                    {"fingerprint": {"field_code": "c", "wbs_stage": "1", "task_name": "1", "display_header": "C"}},
                ]}],
            }
            beta_inventory = {
                "source": {"file_name": "beta.xlsx"},
                "sheets": [{"sheet_name": "data", "columns": [
                    {"fingerprint": {"field_code": "a", "wbs_stage": "1", "task_name": "1", "display_header": "A"}},
                    {"fingerprint": {"field_code": "b", "wbs_stage": "1", "task_name": "1", "display_header": "B"}},
                ]}],
            }
            gamma_inventory = {
                "source": {"file_name": "gamma.xlsx"},
                "sheets": [{"sheet_name": "data", "columns": [
                    {"fingerprint": {"field_code": "x", "wbs_stage": "1", "task_name": "1", "display_header": "X"}},
                ]}],
            }
            (alpha / "header_inventory.json").write_text(json.dumps(alpha_inventory), encoding="utf-8")
            (beta / "header_inventory.json").write_text(json.dumps(beta_inventory), encoding="utf-8")
            (gamma / "header_inventory.json").write_text(json.dumps(gamma_inventory), encoding="utf-8")
            (alpha / "header_hash.txt").write_text("hash-alpha", encoding="utf-8")
            (beta / "header_hash.txt").write_text("hash-beta", encoding="utf-8")
            (gamma / "header_hash.txt").write_text("hash-gamma", encoding="utf-8")

            artifacts = [load_profile_artifact(path) for path in [alpha, beta, gamma]]

            entry = build_grouping_entry(artifacts[0], artifacts)

            self.assertEqual(entry["source_file_name"], "alpha.xlsx")
            self.assertEqual(entry["closest_neighbors"][0]["source_file_name"], "beta.xlsx")
            self.assertAlmostEqual(entry["closest_neighbors"][0]["fingerprint_similarity"], 2 / 3)
            self.assertEqual(entry["grouping_signal"], "POSSIBLE_REUSE_REVIEW")

    def test_grouping_markdown_mentions_reuse_signal(self):
        registry = {
            "entries": [
                {
                    "source_file_name": "alpha.xlsx",
                    "du_model_name": "Alpha",
                    "observed_header_hash": "hash-alpha",
                    "fingerprint_count": 3,
                    "grouping_signal": "POSSIBLE_REUSE_REVIEW",
                    "grouping_reason": "Closest neighbor shares most four-layer fingerprints.",
                    "closest_neighbors": [
                        {
                            "source_file_name": "beta.xlsx",
                            "du_model_name": "Beta",
                            "observed_header_hash": "hash-beta",
                            "fingerprint_similarity": 0.75,
                            "shared_fingerprint_count": 3,
                            "union_fingerprint_count": 4,
                        }
                    ],
                }
            ]
        }

        markdown = grouping_markdown(registry)

        self.assertIn("POSSIBLE_REUSE_REVIEW", markdown)
        self.assertIn("beta.xlsx", markdown)
        self.assertIn("0.750", markdown)


if __name__ == "__main__":
    unittest.main()
