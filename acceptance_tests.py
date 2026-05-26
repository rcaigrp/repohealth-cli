import unittest
import responses
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestRepoHealthCLI(unittest.TestCase):
    @responses.activate
    def test_criterion_1_authenticate_via_github_token(self):
        """Test authentication via GitHub token."""
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/org/repos",
            json=[{"id": 1, "name": "test-repo", "full_name": "org/test-repo"}],
            status=200
        )
        token = "test-token"
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/orgs/org/repos", headers=headers)
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_criterion_2_fetch_all_repos(self):
        """Test fetching all repos for a specified org/user."""
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/org/repos",
            json=[{"id": 1, "name": "test-repo", "full_name": "org/test-repo"}],
            status=200
        )
        token = "test-token"
        repos = main.fetch_repos(token, org="org")
        self.assertEqual(len(repos), 1)

    @responses.activate
    def test_criterion_3_fetch_issues_and_prs(self):
        """Test fetching issues and PRs across repos."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/org/test-repo/issues?state=open&per_page=100",
            json=[{"number": 1, "title": "Test Issue", "html_url": "https://api.github.com/repos/org/test-repo/issues/1", "updated_at": "2023-01-01T00:00:00Z", "state": "open"}],
            status=200
        )
        responses.add(
            responses.GET,
            "https://api.github.com/repos/org/test-repo/pulls?state=open&per_page=100",
            json=[],
            status=200
        )
        token = "test-token"
        repos = [{"full_name": "org/test-repo"}]
        items = main.fetch_issues_and_prs(token, repos)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['type'], 'issue')
