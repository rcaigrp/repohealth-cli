import pytest
import datetime
import responses
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

class TestMain:
    @responses.activate
    def test_fetch_repos(self):
        url = "https://api.github.com/orgs/test-org/repos"
        responses.add(
            responses.GET,
            url,
            json=[{"full_name": "repo1"}, {"full_name": "repo2"}],
            status=200
        )
        repos = main.fetch_repos("token", "test-org")
        assert len(repos) == 2
        assert repos[0]["full_name"] == "repo1"

    @responses.activate
    def test_fetch_items(self):
        url = "https://api.github.com/repos/test-org/test-repo/issues"
        responses.add(
            responses.GET,
            url,
            json=[{"title": "Issue 1", "html_url": "http://example.com/1"}],
            status=200
        )
        items = main.fetch_items("token", "test-org/test-repo")
        assert len(items) == 1
        assert items[0]["title"] == "Issue 1"

    def test_filter_stale(self):
        now = datetime.datetime(2023, 10, 10)
        items = [
            {"title": "Old", "updated_at": "2023-09-01T00:00:00Z", "html_url": "http://example.com/1"},
            {"title": "New", "updated_at": "2023-10-09T00:00:00Z", "html_url": "http://example.com/2"}
        ]
        stale = main.filter_stale(items, 30, now=now)
        assert len(stale) == 1
        assert stale[0]["title"] == "Old"

    def test_generate_report(self):
        items = [
            {"title": "Stale 1", "html_url": "http://example.com/1"}
        ]
        report = main.generate_report(items, "markdown")
        assert "Stale Items Report" in report
        assert "- Stale 1" in report
