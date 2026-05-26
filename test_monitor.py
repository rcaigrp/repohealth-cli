import unittest
import responses
import requests
import json
from datetime import datetime, timedelta
import sys
import os
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestGitHubClient(unittest.TestCase):
    @responses.activate
    def test_fetch_repos(self):
        url = "https://api.github.com/orgs/test/repos"
        responses.add(
            responses.GET,
            url,
            body=json.dumps([{"name": "repo1", "id": 1}]),
            status=200
        )
        client = main.GitHubClient("fake-token", org="test")
        repos = client.fetch_repos()
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'repo1')

    @responses.activate
    def test_fetch_issues_and_prs(self):
        url = "https://api.github.com/repos/test/repo1/issues"
        responses.add(
            responses.GET,
            url,
            body=json.dumps([{"number": 1, "title": "Test Issue"}]),
            status=200
        )
        client = main.GitHubClient("fake-token", org="test")
        items = client.fetch_issues_and_prs("repo1")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Test Issue')

    @unittest.mock.patch('main.datetime')
    def test_filter_stale(self, mock_dt):
        now = datetime(2023, 1, 15, 0, 0, 0)
        mock_dt.utcnow.return_value = now
        mock_dt.strptime = datetime.strptime

        client = main.GitHubClient("fake-token")
        items = [
            {"updated_at": "2023-01-01T00:00:00Z", "title": "Old Issue", "state": "open", "id": 1},
            {"updated_at": "2023-01-10T00:00:00Z", "title": "Recent Issue", "state": "open", "id": 2}
        ]
        stale = client.filter_stale(items, days=10)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['title'], 'Old Issue')

    @unittest.mock.patch('main.generate_shell_script')
    def test_generate_report(self, mock_script):
        with unittest.mock.patch('main.Console') as mock_console:
            console = mock_console.return_value
            stale_items = [{"title": "Test", "state": "open", "updated_at": "2023-01-01T00:00:00Z"}]
            repos = [{"name": "repo1"}]
            main.generate_report(stale_items, repos)
            console.print.assert_called()

    @unittest.mock.patch('builtins.open')
    @unittest.mock.patch('builtins.print')
    def test_generate_shell_script(self, mock_print, mock_open):
        mock_open.return_value.__enter__.return_value.write = unittest.mock.MagicMock()
        stale_items = [{"number": 1, "repository": {"owner": {"login": "test"}, "name": "repo1"}}]
        main.generate_shell_script(stale_items, output_file='test.sh')
        mock_open.assert_called_once_with('test.sh', 'w')
        mock_print.assert_called()

class TestMain(unittest.TestCase):
    @unittest.mock.patch('main.GitHubClient')
    @unittest.mock.patch('main.generate_report')
    @unittest.mock.patch('main.generate_shell_script')
    def test_main(self, mock_script, mock_report, mock_client):
        mock_client_instance = unittest.mock.MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_repos.return_value = [{"name": "repo1"}]
        mock_client_instance.fetch_issues_and_prs.return_value = [{"number": 1, "updated_at": "2023-01-01T00:00:00Z"}]
        mock_client_instance.filter_stale.return_value = [{"number": 1, "updated_at": "2023-01-01T00:00:00Z"}]
        
        with unittest.mock.patch('sys.argv', ['main.py', '--token', 'test']):
            main.main()
            mock_report.assert_called()

if __name__ == '__main__':
    unittest.main()
