import unittest
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestMain(unittest.TestCase):
    @unittest.mock.patch('main.datetime')
    def test_filter_stale(self, mock_dt):
        now = datetime.datetime(2023, 10, 10)
        mock_dt.datetime.now.return_value = now
        mock_dt.timedelta = datetime.timedelta
        
        items = [
            {"title": "Old Issue", "updated_at": "2023-09-01T00:00:00Z", "html_url": "http://example.com/1"},
            {"title": "New Issue", "updated_at": "2023-10-09T00:00:00Z", "html_url": "http://example.com/2"}
        ]
        stale = main.filter_stale(items, 30)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["title"], "Old Issue")

    @unittest.mock.patch('main.requests')
    def test_fetch_repos(self, mock_requests):
        mock_response = mock_requests.get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = [{"full_name": "repo1"}]
        
        repos = main.fetch_repos("token", "org")
        self.assertEqual(len(repos), 1)
        mock_requests.get.assert_called_once()

if __name__ == "__main__":
    unittest.main()
