import unittest
import responses
import requests
import datetime
import sys
import os

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')

from main import fetch_repos, fetch_issues_and_prs, filter_stale, generate_report, generate_script

class TestRepoHealth(unittest.TestCase):
    @responses.mock
    def test_criterion_1_auth(self):
        token = "test_token"
        org = "test-org"
        url = f"https://api.github.com/orgs/{org}/repos"
        responses.add(responses.GET, url, json=[], status=200, headers={"Link": ''})
        fetch_repos(token, org=org)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].headers['Authorization'], 'token test_token')

    @responses.mock
    def test_criterion_2_fetch_repos(self):
        token = "test_token"
        org = "test-org"
        url = f"https://api.github.com/orgs/{org}/repos"
        responses.add(responses.GET, url, json=[{"name": "repo1", "full_name": "test-org/repo1"}], status=200, headers={"Link": ''})
        repos = fetch_repos(token, org=org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "repo1")

    @responses.mock
    def test_criterion_3_fetch_issues_prs(self):
        token = "test_token"
        repos = [{"name": "repo1", "full_name": "test-org/repo1"}]
        url = f"https://api.github.com/repos/test-org/repo1/issues?state=open"
        responses.add(responses.GET, url, json=[{"id": 1, "title": "Issue", "type": "issue"}], status=200, headers={"Link": ''})
        items = fetch_issues_and_prs(token, repos)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Issue")
        self.assertEqual(items[0]["repo_name"], "test-org/repo1")

    def test_criterion_4_filter_stale(self):
        now = datetime.datetime(2024, 1, 1)
        items = [
            {"title": "Old", "updated_at": "2023-01-01T00:00:00Z", "type": "issue"},
            {"title": "New", "updated_at": "2024-01-01T00:00:00Z", "type": "issue"}
        ]
        stale = filter_stale(items, days=30, now=now)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["title"], "Old")

    def test_criterion_5_generate_report(self):
        stale_items = [{"title": "Test", "html_url": "http://test.com"}]
        report = generate_report(stale_items, org="test-org")
        self.assertIn("Total Stale Items: 1", report)
        self.assertIn("test-org", report)

    def test_criterion_6_generate_script(self):
        stale_items = [{"title": "Test", "html_url": "http://test.com", "repo_name": "test-org/repo1", "number": 1}]
        script = generate_script(stale_items, org="test-org")
        self.assertIn("#!/bin/bash", script)
        self.assertIn("test-org/repo1", script)
