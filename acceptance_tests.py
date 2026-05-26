import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestRepoHealth(unittest.TestCase):
    @patch('main.requests')
    def test_fetch_repos(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "repo1", "owner": {"login": "test-org"}}]
        
        mock_empty = MagicMock(status_code=200, json=MagicMock(return_value=[]))
        
        mock_requests.get.side_effect = [
            mock_response,
            mock_empty
        ]
        
        repos = main.fetch_repos("token", "test-org")
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'repo1')

    @patch('main.requests')
    def test_fetch_issues(self, mock_requests):
        repo = {"id": 1, "name": "repo1", "owner": {"login": "test-org"}}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 100, "title": "Stale Issue", "updated_at": "2023-01-01T00:00:00Z"}]
        
        mock_empty = MagicMock(status_code=200, json=MagicMock(return_value=[]))
        
        mock_requests.get.side_effect = [
            mock_response,
            mock_empty
        ]
        
        issues = main.fetch_issues("token", [repo])
        self.assertEqual(len(issues), 1)

    def test_filter_stale(self):
        issue = {"id": 100, "title": "Stale Issue", "updated_at": "2020-01-01T00:00:00Z"}
        stale = main.filter_stale([issue], stale_days=30)
        self.assertEqual(len(stale), 1)

        new_issue = {"id": 101, "title": "New Issue", "updated_at": "2025-01-01T00:00:00Z"}
        result = main.filter_stale([issue, new_issue], stale_days=30)
        self.assertEqual(len(result), 1)

    def test_generate_report(self):
        issues = [{"id": 100, "title": "Stale Issue", "html_url": "http://test.com", "state": "open", "updated_at": "2020-01-01T00:00:00Z"}]
        report = main.generate_report(issues)
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]['title'], 'Stale Issue')

if __name__ == '__main__':
    unittest.main()
