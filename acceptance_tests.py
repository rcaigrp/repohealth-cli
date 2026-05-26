import unittest
import responses
from unittest.mock import patch, MagicMock
import sys
import os
import datetime

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')
import main

class TestRepoHealth(unittest.TestCase):
    def setUp(self):
        self.org = "test-org"
        self.token = "test-token"
        self.stale_days = 30

    @responses.activate
    def test_criterion_1_auth(self):
        token = main.get_token(None)
        self.assertIsNone(token)

        with patch.dict(os.environ, {"GITHUB_TOKEN": "mock-token"}):
            token = main.get_token(None)
            self.assertEqual(token, "mock-token")

    @responses.activate
    def test_criterion_2_fetch_repos(self):
        responses.add(
            responses.GET,
            f"https://api.github.com/orgs/{self.org}/repos",
            json=[{"full_name": "test-org/repo1", "id": 1}],
            status=200
        )
        repos = main.fetch_repos(self.token, self.org)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["full_name"], "test-org/repo1")

    @responses.activate
    def test_criterion_3_fetch_items(self):
        responses.add(
            responses.GET,
            f"https://api.github.com/repos/{self.org}/repo1/issues?state=open&per_page=100",
            json=[{"id": 1, "title": "Test Issue", "updated_at": "2023-01-01T00:00:00Z", "state": "open"}],
            status=200
        )
        items = main.fetch_items(self.token, [{"full_name": "test-org/repo1", "id": 1}])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Test Issue")

    def test_criterion_4_filter_stale(self):
        with patch('main.datetime') as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2023, 2, 1)
            mock_dt.timedelta = datetime.timedelta
            
            def fake_strptime(s, fmt):
                return datetime.datetime.strptime(s.split('T')[0], '%Y-%m-%d')
            mock_dt.datetime.strptime = fake_strptime
            
            items = [
                {"updated_at": "2023-01-01T00:00:00Z", "title": "Old"},
                {"updated_at": "2023-02-01T00:00:00Z", "title": "New"}
            ]
            
            # Cutoff is Jan 2. Mock strptime returns Jan 1 for any date.
            # Jan 1 < Jan 2 -> Stale.
            # Both items will be stale if strptime is mocked to return Jan 1.
            # But we want only "Old" to be stale.
            # This mock strategy is flawed if strptime always returns Jan 1.
            # Let's fix the mock to return the actual parsed date.
            def fake_strptime(s, fmt):
                return datetime.datetime.strptime(s.split('T')[0], '%Y-%m-%d')
            mock_dt.datetime.strptime = fake_strptime
            
            stale = main.filter_stale(items, 30)
            self.assertEqual(len(stale), 1)
            self.assertEqual(stale[0]["title"], "Old")