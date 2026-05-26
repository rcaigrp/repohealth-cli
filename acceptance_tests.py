import unittest
import responses
import json
import sys
import os

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')
from main import GitHubClient, filter_stale, generate_report, generate_shell_script

class TestGitHubClient(unittest.TestCase):
    @responses.activate
    def test_fetch_repos(self):
        org = "test-org"
        responses.add(
            responses.GET,
            f"https://api.github.com/orgs/{org}/repos",
            body=json.dumps([{"name": "repo1", "updated_at": "2023-01-01T00:00:00Z"}]),
            status=200
        )
        client = GitHubClient("token123")
        repos = client.fetch_repos(org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'repo1')

    @responses.activate
    def test_fetch_issues_and_prs(self):
        repo = "test-repo"
        responses.add(responses.GET, f"https://api.github.com/repos/{repo}/issues", body=json.dumps([{"title": "Issue 1", "updated_at": "2023-01-01T00:00:00Z"}]), status=200)
        responses.add(responses.GET, f"https://api.github.com/repos/{repo}/pulls", body=json.dumps([{"title": "PR 1", "updated_at": "2023-01-01T00:00:00Z"}]), status=200)
        
        client = GitHubClient("token123")
        issues, prs = client.fetch_issues_and_prs(repo)
        self.assertEqual(len(issues), 1)
        self.assertEqual(len(prs), 1)

class TestFilterStale(unittest.TestCase):
    def test_filter_stale(self):
        items = [
            {"updated_at": "2020-01-01T00:00:00Z"},
            {"updated_at": "2023-01-01T00:00:00Z"}
        ]
        stale = filter_stale(items, stale_days=30)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['updated_at'], "2020-01-01T00:00:00Z")

class TestGenerateReport(unittest.TestCase):
    def test_generate_report(self):
        data = {"repo": "test"}
        result = generate_report(data)
        self.assertEqual(json.loads(result), data)

class TestGenerateShellScript(unittest.TestCase):
    def test_generate_shell_script(self):
        report = '{"repo": "test"}'
        result = generate_shell_script(report)
        self.assertIn("#!/bin/bash", result)
        self.assertIn(report, result)

if __name__ == '__main__':
    unittest.main()
