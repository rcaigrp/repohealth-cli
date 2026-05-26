import pytest
import json
import responses
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

def test_criterion_1_authenticate_via_token():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: []
        client = main.GitHubClient("my-token", "org")
        client._get("repos")
        mock_get.assert_called_once_with(
            "https://api.github.com/repos",
            headers={"Authorization": "token my-token"},
            params=None
        )

def test_criterion_2_fetch_repos():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://api.github.com/orgs/test-org/repos",
            body=json.dumps([{"name": "repo1"}]),
            status=200
        )
        client = main.GitHubClient("token", "test-org")
        repos = client.fetch_repos()
        assert len(repos) == 1
        assert repos[0]["name"] == "repo1"

def test_criterion_3_fetch_issues_and_prs():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://api.github.com/repos/test-org/repo1/issues",
            body=json.dumps([{"title": "Issue 1"}]),
            status=200
        )
        rsps.add(
            responses.GET,
            "https://api.github.com/repos/test-org/repo1/pulls",
            body=json.dumps([{"title": "PR 1"}]),
            status=200
        )
        client = main.GitHubClient("token", "test-org")
        issues = client.fetch_issues("repo1")
        prs = client.fetch_prs("repo1")
        assert len(issues) == 1
        assert len(prs) == 1

def test_criterion_4_filter_stale():
    old_date = (datetime.utcnow() - timedelta(days=60)).isoformat()
    new_date = datetime.utcnow().isoformat()
    items = [
        {"updated_at": old_date},
        {"updated_at": new_date}
    ]
    stale = main.filter_stale(items, stale_days=30)
    assert len(stale) == 1
    assert stale[0]["updated_at"] == old_date

def test_criterion_5_generate_report():
    stale = [{"updated_at": "2023-01-01T00:00:00Z", "title": "Test", "repository_url": "https://api.github.com/repos/org/repo"}]
    table = main.generate_report(stale)
    assert isinstance(table, main.rich.table.Table)

def test_criterion_6_generate_shell_script():
    stale = [{"updated_at": "2023-01-01T00:00:00Z", "repository_url": "https://api.github.com/repos/org/repo", "number": 1}]
    with patch("main.open", unittest.mock.mock_open()) as mock_open:
        main.generate_shell_script(stale, "test.sh")
        assert mock_open.called
