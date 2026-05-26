import unittest
import responses
import requests
import json
import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestRepoHealth(unittest.TestCase):
    @responses.activate
    def test_criterion_1_auth(self):
        from main import GitHubClient
        token = "fake_token"
        client = GitHubClient(token)
        self.assertEqual(client.token, token)
        self.assertIn('Bearer fake_token', client.session.headers.get('Authorization', ''))

    @responses.activate
    def test_criterion_2_fetch_repos(self):
        from main import GitHubClient
        org = "org1"
        token = "fake_token"
        url = f'https://api.github.com/orgs/{org}/repos'
        responses.add(responses.GET, url, json=[{"full_name": "org1/repo1"}])
        responses.add(responses.GET, url, json=[])
        
        client = GitHubClient(token)
        repos = client.get_repos(org=org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['full_name'], "org1/repo1")

    @responses.activate
    def test_criterion_3_fetch_issues_prs(self):
        from main import GitHubClient
        repo = "org1/repo1"
        token = "fake_token"
        issues_url = f'https://api.github.com/repos/{repo}/issues'
        prs_url = f'https://api.github.com/repos/{repo}/pulls'
        
        responses.add(responses.GET, issues_url, json=[{"title": "Issue 1"}])
        responses.add(responses.GET, issues_url, json=[])
        
        responses.add(responses.GET, prs_url, json=[{"title": "PR 1"}])
        responses.add(responses.GET, prs_url, json=[])
        
        client = GitHubClient(token)
        issues = client.get_issues(repo)
        prs = client.get_prs(repo)
        self.assertEqual(len(issues), 1)
        self.assertEqual(len(prs), 1)

    @responses.activate
    def test_criterion_4_filter_stale(self):
        from main import GitHubClient
        token = "fake_token"
        client = GitHubClient(token)
        
        stale_item = {"title": "Stale", "updated_at": "2020-01-01T00:00:00Z"}
        fresh_item = {"title": "Fresh", "updated_at": "2023-01-01T00:00:00Z"}
        
        issues = [stale_item, fresh_item]
        active = client.filter_stale_issues(issues, days_threshold=30)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['title'], "Fresh")

    @responses.activate
    def test_criterion_5_export_json(self):
        from main import GitHubClient
        token = "fake_token"
        client = GitHubClient(token)
        
        data = {"issues": [{"title": "Test"}]}
        filename = "test_report.json"
        exported_file = client.export_json(data, filename)
        
        self.assertTrue(os.path.exists(exported_file))
        with open(exported_file, 'r') as f:
            content = json.load(f)
        self.assertEqual(content['issues'][0]['title'], "Test")
        os.remove(exported_file)

    @responses.activate
    def test_criterion_6_export_csv(self):
        from main import GitHubClient
        token = "fake_token"
        client = GitHubClient(token)
        
        data = [{"title": "Test"}]
        filename = "test_report.csv"
        exported_file = client.export_csv(data, filename)
        
        self.assertTrue(os.path.exists(exported_file))
        with open(exported_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(rows[0]['title'], "Test")
        os.remove(exported_file)

if __name__ == '__main__':
    unittest.main()
