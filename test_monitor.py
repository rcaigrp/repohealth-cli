import unittest
import responses
import os
from datetime import datetime, timedelta
from monitor import fetch_repos, filter_stale, calculate_density

os.environ["GITHUB_TOKEN"] = "mock-token"

class TestMonitor(unittest.TestCase):
    @responses.activate
    def test_fetch_repos(self):
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/test-org/repos",
            json=[{"full_name": "test-org/repo1"}],
        )
        repos = fetch_repos(org="test-org")
        self.assertEqual(len(repos), 1)

    @responses.activate
    def test_fetch_repos_empty(self):
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/empty-org/repos",
            json=[],
        )
        repos = fetch_repos(org="empty-org")
        self.assertEqual(len(repos), 0)

    def test_filter_stale(self):
        old_date = (datetime.utcnow() - timedelta(days=31)).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        items = [
            {"updated_at": old_date, "created_at": old_date, "comments": 0},
            {"updated_at": new_date, "created_at": new_date, "comments": 5},
        ]
        stale = filter_stale(items, stale_days=30)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["updated_at"], old_date)

    def test_density_calc(self):
        old_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        item = {"created_at": old_date, "comments": 5}
        density = calculate_density(item)
        self.assertAlmostEqual(density, 0.5, places=1)

if __name__ == "__main__":
    unittest.main()
