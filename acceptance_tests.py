import unittest
import os
import sys
import responses
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as main_module

class TestRepoHealth(unittest.TestCase):
    def setUp(self):
        self.token = "test_token"
        self.org = "test-org"
        self.stale_days = 30
        self.repos = [
            {
                "id": 1,
                "name": "test-repo",
                "owner": {"login": self.org},
                "full_name": f"{self.org}/test-repo"
            }
        ]
        self.items = [
            {
                "id": 1,
                "title": "Stale Issue",
                "updated_at": "2023-01-01T00:00:00Z",
                "number": 1,
                "repo": f"{self.org}/test-repo"
            },
            {
                "id": 2,
                "title": "Recent Issue",
                "updated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "number": 2,
                "repo": f"{self.org}/test-repo"
            }
        ]

    @responses.activate
    def test_fetch_repos(self):
        responses.add(responses.GET, f'https://api.github.com/orgs/{self.org}/repos', json=self.repos)
        fetched = main_module.fetch_repos(self.token, self.org)
        self.assertEqual(len(fetched), 1)
        self.assertEqual(fetched[0]['name'], 'test-repo')

    @responses.activate
    def test_fetch_issues_and_prs(self):
        url = f"https://api.github.com/repos/{self.org}/test-repo/issues"
        responses.add(responses.GET, url, json=self.items)
        fetched = main_module.fetch_issues_and_prs(self.token, self.repos)
        self.assertEqual(len(fetched), 2)

    def test_filter_stale(self):
        cutoff = datetime.utcnow() - timedelta(days=self.stale_days)
        stale = main_module.filter_stale(self.items, self.stale_days)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['title'], 'Stale Issue')

    def test_generate_report_markdown(self):
        report = main_module.generate_report(self.items, 'markdown')
        self.assertIn("# RepoHealth Report", report)
        self.assertIn("Stale Items", report)

    def test_generate_script_close(self):
        script = main_module.generate_script(self.items, 'close', self.token)
        self.assertIn("#!/bin/bash", script)
        self.assertIn("closed", script)

    def test_generate_script_label(self):
        script = main_module.generate_script(self.items, 'label', self.token)
        self.assertIn("#!/bin/bash", script)
        self.assertIn("stale", script)

if __name__ == '__main__':
    unittest.main()
