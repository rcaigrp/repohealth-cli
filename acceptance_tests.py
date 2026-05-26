import unittest
import responses
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestRepoHealth(unittest.TestCase):
    @responses.activate
    def test_criterion_1_authenticate_and_fetch_repos(self):
        token = "ghp_test"
        org = "test_org"
        url = f"https://api.github.com/orgs/{org}/repos"
        responses.add(responses.GET, url, json=[{"id": 1, "name": "repo1", "owner": {"login": "test_user"}}], status=200)
        repos = main.get_repos(token, org=org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'repo1')

    @responses.activate
    def test_criterion_2_fetch_issues_and_prs(self):
        token = "ghp_test"
        repos = [{"id": 1, "name": "repo1", "owner": {"login": "test_user"}}]
        url = "https://api.github.com/repos/test_user/repo1/issues"
        responses.add(responses.GET, url, json=[{"number": 1, "title": "Test Issue", "updated_at": "2023-01-01T00:00:00Z", "user": {"login": "user1"}, "html_url": "http://example.com", "repository": {"name": "repo1"}}], status=200)
        items = main.get_issues_and_prs(token, repos)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Test Issue')

    def test_criterion_3_filter_stale(self):
        old_date = datetime.now(timezone.utc) - timedelta(days=60)
        items = [{"updated_at": old_date.isoformat(), "title": "Old Issue", "user": {"login": "user1"}, "html_url": "http://example.com", "number": 1, "repository": {"name": "repo1"}}]
        stale = main.filter_stale(items, days=30)
        self.assertEqual(len(stale), 1)

    @patch('main.rich.console.Console')
    def test_criterion_4_generate_report(self, MockConsole):
        items = [{"title": "Test", "user": {"login": "u"}, "html_url": "http://ex.com", "number": 1, "repository": {"name": "repo1"}}]
        main.generate_report(items)
        MockConsole.return_value.print.assert_called()
