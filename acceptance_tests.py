import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestRepoHealthCLI(unittest.TestCase):
    @patch('main.requests')
    def test_fetch_repos(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"full_name": "test-org/repo1"}]
        mock_requests.get.return_value = mock_response
        
        result = main.fetch_repos("fake-token", "test-org")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["full_name"], "test-org/repo1")

    @patch('main.requests')
    def test_fetch_issues(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"updated_at": "2020-01-01T00:00:00Z", "title": "Old Issue"}]
        mock_requests.get.return_value = mock_response
        
        result = main.fetch_issues("fake-token", "test-org/repo1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Old Issue")

    @patch('main.requests')
    def test_fetch_prs(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"updated_at": "2020-01-01T00:00:00Z", "title": "Old PR"}]
        mock_requests.get.return_value = mock_response
        
        result = main.fetch_prs("fake-token", "test-org/repo1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Old PR")

    def test_filter_stale(self):
        items = [{"updated_at": "2020-01-01T00:00:00Z", "title": "Stale"}]
        result = main.filter_stale(items, 30)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Stale")

    def test_generate_report(self):
        items = [{"type": "Issue", "repo": "test", "title": "Test", "updated_at": "2020-01-01"}]
        result = main.generate_report(items)
        self.assertIn("Test", result)
        self.assertIn("2020-01-01", result)

    def test_generate_script(self):
        items = [{"title": "Test"}]
        result = main.generate_script(items)
        self.assertIn("Test", result)
