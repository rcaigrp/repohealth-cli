import unittest
import responses
import requests
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import fetch_repos, fetch_items, filter_stale, generate_report

class TestRepoHealthCLI(unittest.TestCase):
    @responses.activate
    def test_fetch_repos(self):
        org = "test-org"
        url = f"https://api.github.com/orgs/{org}/repos"
        responses.add(
            responses.GET,
            url,
            json=[{"name": "repo1", "owner": {"login": "test-org"}, "full_name": "test-org/repo1", "repository_url": "https://api.github.com/repos/test-org/repo1"}],
            status=200
        )
        responses.add(
            responses.GET,
            url,
            json=[],
            status=200
        )
        token = "test-token"
        repos = fetch_repos(token, org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "repo1")

    @responses.activate
    def test_fetch_issues(self):
        repo = "test-org/repo1"
        url = f"https://api.github.com/repos/{repo}/issues"
        responses.add(
            responses.GET,
            url,
            json=[{"title": "Issue 1", "closed_at": "2023-01-01T00:00:00Z", "repository_url": f"https://api.github.com/repos/{repo}", "html_url": "https://github.com/test-org/repo1/issues/1"}],
            status=200
        )
        responses.add(
            responses.GET,
            url,
            json=[],
            status=200
        )
        token = "test-token"
        issues = fetch_items(token, repo, "issues")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["title"], "Issue 1")

    @responses.activate
    def test_fetch_pulls(self):
        repo = "test-org/repo1"
        url = f"https://api.github.com/repos/{repo}/pulls"
        responses.add(
            responses.GET,
            url,
            json=[{"title": "PR 1", "closed_at": "2023-01-01T00:00:00Z", "repository_url": f"https://api.github.com/repos/{repo}", "html_url": "https://github.com/test-org/repo1/pull/1"}],
            status=200
        )
        responses.add(
            responses.GET,
            url,
            json=[],
            status=200
        )
        token = "test-token"
        prs = fetch_items(token, repo, "pulls")
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["title"], "PR 1")

    def test_filter_stale(self):
        items = [
            {"title": "Stale Issue", "closed_at": "2020-01-01T00:00:00Z", "repository_url": "https://api.github.com/repos/test-org/repo1", "html_url": "https://github.com/test-org/repo1/issues/1"},
            {"title": "Fresh Issue", "closed_at": datetime.now(timezone.utc).isoformat(), "repository_url": "https://api.github.com/repos/test-org/repo1", "html_url": "https://github.com/test-org/repo1/issues/2"}
        ]
        stale_items = filter_stale(items, 30)
        self.assertEqual(len(stale_items), 1)
        self.assertEqual(stale_items[0]["title"], "Stale Issue")

    def test_generate_report(self):
        repos = [{"name": "repo1", "owner": {"login": "test-org"}, "full_name": "test-org/repo1", "repository_url": "https://api.github.com/repos/test-org/repo1"}]
        stale_items = [
            {"title": "Stale Issue", "repository_url": "https://api.github.com/repos/test-org/repo1", "html_url": "https://github.com/test-org/repo1/issues/1"}
        ]
        report = generate_report(repos, stale_items)
        self.assertIn("# RepoHealth Report", report)
        self.assertIn("Stale Issue", report)

if __name__ == "__main__":
    unittest.main()
