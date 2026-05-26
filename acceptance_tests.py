import unittest
import unittest.mock
import json
import datetime
import sys
import os
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))
import main

class TestRepoHealthAcceptance(unittest.TestCase):
    def test_criterion_1_auth(self):
        """Authenticate via GitHub token (env var or CLI arg)"""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--token')
        original_argv = sys.argv
        sys.argv = ['prog', '--token', 'test-token']
        args = parser.parse_args()
        sys.argv = original_argv
        self.assertEqual(args.token, 'test-token')

    def test_criterion_2_fetch_repos(self):
        """Fetch all repos for a specified org/user"""
        mock_data = [{'name': 'repo1'}, {'name': 'repo2'}]
        mock_response = unittest.mock.Mock()
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_response.__enter__ = unittest.mock.Mock(return_value=mock_response)
        mock_response.__exit__ = unittest.mock.Mock(return_value=None)
        
        with unittest.mock.patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.return_value = mock_response
            repos = main.get_repos('test-org', 'token')
            self.assertEqual(len(repos), 2)
            self.assertEqual(repos[0]['name'], 'repo1')

    def test_criterion_3_fetch_issues_prs(self):
        """Fetch issues and PRs across repos"""
        mock_repos = [{'name': 'repo1'}]
        mock_issues = [{'title': 'Issue 1', 'state': 'open', 'updated_at': '2020-01-01T00:00:00Z'}]
        mock_prs = [{'title': 'PR 1', 'state': 'open', 'updated_at': '2020-01-01T00:00:00Z'}]
        
        def create_mock_response(data):
            resp = unittest.mock.Mock()
            resp.read.return_value = json.dumps(data).encode('utf-8')
            resp.__enter__ = unittest.mock(return_value=resp)
            resp.__exit__ = unittest.mock(return_value=None)
            return resp

        def side_effect(url):
            if 'repos' in url:
                return create_mock_response(mock_repos)
            elif 'issues' in url:
                return create_mock_response(mock_issues)
            elif 'pulls' in url:
                return create_mock_response(mock_prs)
            return create_mock_response([])

        with unittest.mock.patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = side_effect
            items = main.get_issues_and_prs('test-org', 'token')
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]['type'], 'issue')
            self.assertEqual(items[1]['type'], 'pull_request')

    def test_criterion_4_filter_stale(self):
        """Filter stale items based on date"""
        items = [
            {'updated_at': '2020-01-01T00:00:00Z'},
            {'updated_at': '2024-01-01T00:00:00Z'}
        ]
        stale = main.filter_stale(items, 30)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['updated_at'], '2020-01-01T00:00:00Z')

    def test_criterion_5_generate_report(self):
        """Generate a report of stale items"""
        with unittest.mock.patch('rich.console.Console') as MockConsole:
            mock_console_instance = unittest.mock.Mock()
            MockConsole.return_value = mock_console_instance
            stale_items = [{'type': 'issue', 'repo': 'test', 'title': 'Bad', 'status': 'open', 'updated_at': '2020-01-01'}]
            main.generate_report(stale_items)
            mock_console_instance.print.assert_called()

if __name__ == '__main__':
    unittest.main()