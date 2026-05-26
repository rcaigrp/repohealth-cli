import unittest
import responses
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_health_cli import RepoHealthClient

class TestRepoHealthCLI(unittest.TestCase):
    def setUp(self):
        self.client = RepoHealthClient(token="test_token")

    @responses.activate
    def test_fetch_org_repos(self):
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/test_org/repos",
            json=[{"name": "repo1"}, {"name": "repo2"}],
            status=200
        )
        # Mock second page to stop pagination loop
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/test_org/repos",
            json=[],
            status=200
        )
        repos = self.client.fetch_org_repos("test_org")
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0]["name"], "repo1")

    @responses.activate
    def test_fetch_repo_issues(self):
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_org/repo1/issues",
            json=[{"number": 1, "title": "Bug"}],
            status=200
        )
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_org/repo1/issues",
            json=[],
            status=200
        )
        issues = self.client.fetch_repo_issues("repo1", "test_org")
        self.assertEqual(len(issues), 1)

    @responses.activate
    def test_fetch_repo_prs(self):
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_org/repo1/pulls",
            json=[{"number": 1, "title": "Feature"}],
            status=200
        )
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_org/repo1/pulls",
            json=[],
            status=200
        )
        prs = self.client.fetch_repo_prs("repo1", "test_org")
        self.assertEqual(len(prs), 1)

    @responses.activate
    def test_auth_error(self):
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/test_org/repos",
            json={"message": "Unauthorized"},
            status=401
        )
        with self.assertRaises(Exception):
            self.client.fetch_org_repos("test_org")

    @responses.activate
    def test_fetch_user_repos(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user/repos",
            json=[{"name": "user_repo"}],
            status=200
        )
        responses.add(
            responses.GET,
            "https://api.github.com/user/repos",
            json=[],
            status=200
        )
        repos = self.client.fetch_user_repos()
        self.assertEqual(len(repos), 1)
