import pytest
import json
import datetime
from unittest.mock import MagicMock, patch
from main import fetch_repos, fetch_issues, filter_stale, generate_report, generate_script

class TestRepoHealth:
    @patch('urllib.request.urlopen')
    def test_fetch_repos(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([{"name": "repo1", "id": 1}]).encode('utf-8')
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_response
        mock_ctx.__exit__.return_value = None
        
        mock_urlopen.return_value = mock_ctx
        
        token = "test_token"
        org = "test_org"
        
        repos = fetch_repos(token, org)
        assert len(repos) == 1
        assert repos[0]['name'] == 'repo1'

    @patch('urllib.request.urlopen')
    def test_fetch_issues(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([{"id": 1, "updated_at": "2023-01-01T00:00:00Z"}]).encode('utf-8')
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_response
        mock_ctx.__exit__.return_value = None
        
        mock_urlopen.return_value = mock_ctx
        
        token = "test_token"
        repo = "repo1"
        
        issues = fetch_issues(token, repo)
        assert len(issues) == 1

    @patch('datetime.datetime')
    def test_filter_stale(self, MockDatetime):
        MockDatetime.now.return_value = datetime.datetime(2024, 1, 15)
        MockDatetime.fromisoformat.return_value = datetime.datetime(2023, 1, 1)
        
        items = [{"updated_at": "2023-01-01T00:00:00Z"}]
        stale = filter_stale(items, 30)
        assert len(stale) == 1

    def test_generate_report(self):
        items = [{"id": 1}]
        report = generate_report(items)
        assert "Stale Items Report" in report

    def test_generate_script(self):
        items = [{"id": 1}]
        script = generate_script(items)
        assert "#!/bin/bash" in script
