import pytest
import unittest.mock as mock
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main


class TestRepoHealth:
    @mock.patch('main.requests')
    @mock.patch('main.datetime')
    def test_filter_stale_items(self, mock_dt, mock_requests):
        mock_dt.now.return_value = datetime.datetime(2024, 1, 1)
        mock_dt.timedelta = datetime.timedelta

        mock_response = mock.MagicMock()
        mock_response.json.return_value = [
            {"updated_at": "2023-01-01T00:00:00Z"},
            {"updated_at": "2024-01-01T00:00:00Z"}
        ]
        mock_requests.get.return_value = mock_response

        result = main.filter_stale_items("test", "test", days=30)

        assert len(result) == 1
        assert result[0] == {"updated_at": "2023-01-01T00:00:00Z"}
