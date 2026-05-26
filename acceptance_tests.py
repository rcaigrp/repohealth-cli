import unittest
import unittest.mock as mock
import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestRepoHealth(unittest.TestCase):
    @mock.patch('main.requests')
    def test_fetch_repos(self, mock_requests):
        mock_requests.get.return_value.json.return_value = [{'full_name': 'org/repo1'}]
        repos = main.fetch_repos('my-org', 'token')
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['full_name'], 'org/repo1')

    @mock.patch('main.requests')
    def test_fetch_issues_and_prs(self, mock_requests):
        def side_effect(*args, **kwargs):
            url = args[0]
            if 'orgs/' in url:
                mock_resp = mock.Mock()
                mock_resp.json.return_value = [{'full_name': 'org/repo1'}]
                return mock_resp
            elif 'issues' in url:
                mock_resp = mock.Mock()
                mock_resp.json.return_value = [{'title': 'Issue 1', 'updated_at': '2020-01-01T00:00:00Z'}]
                return mock_resp
            elif 'pulls' in url:
                mock_resp = mock.Mock()
                mock_resp.json.return_value = [{'title': 'PR 1', 'updated_at': '2020-01-01T00:00:00Z'}]
                return mock_resp
            return mock.Mock()

        mock_requests.get.side_effect = side_effect
        
        items = main.fetch_issues_repos([{'full_name': 'org/repo1'}], 'token')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['title'], 'Issue 1')
        self.assertEqual(items[1]['title'], 'PR 1')

    @mock.patch('main.requests')
    def test_filter_stale(self, mock_requests):
        items = [
            {'title': 'Old Issue', 'updated_at': '2020-01-01T00:00:00Z'},
            {'title': 'New Issue', 'updated_at': '2023-01-01T00:00:00Z'}
        ]
        stale = main.filter_stale(items, 30)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['title'], 'Old Issue')

    def test_generate_report(self):
        stale_items = [{'title': 'Test', 'repo': 'org/repo'}]
        report = main.generate_report(stale_items)
        self.assertIn('Test', report)
        self.assertIn('org/repo', report)

    def test_generate_script(self):
        stale_items = [{'title': 'Test', 'repo': 'org/repo'}]
        script = main.generate_script(stale_items, action='close')
        self.assertIn('close', script)

if __name__ == '__main__':
    unittest.main()
