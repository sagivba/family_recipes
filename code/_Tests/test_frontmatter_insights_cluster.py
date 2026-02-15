import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.cluster import cluster_keys, cluster_values


class TestCluster(unittest.TestCase):
    def test_key_and_value_clustering(self):
        rows = [
            {"filepath": "a.md", "parse_ok": True, "frontmatter": {"category": "Soup", "origin": "Yemen", "tags": ["fast"]}},
            {"filepath": "b.md", "parse_ok": True, "frontmatter": {"categry": "Soups", "origin": "Yemeni", "tags": ["fast"]}},
        ]

        key_clusters = cluster_keys(rows, threshold=0.85)
        self.assertTrue(any(set(c["members"]) >= {"category", "categry"} for c in key_clusters))

        value_clusters = cluster_values(rows, threshold=0.8)
        self.assertIn("origin", value_clusters)
        self.assertGreaterEqual(len(value_clusters["origin"]), 1)


if __name__ == "__main__":
    unittest.main()
