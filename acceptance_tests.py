import pytest
import responses
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')
import main

@pytest.fixture
def stale_item():
    # 31 days ago
    date = datetime.now() - timedelta(days=31)
    return {
        "title": "Stale Issue",
        "updated_at": date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "html_url": "https://api.github.com/repos/test-org/test-repo/issues/2"
    }

@pytest.fixture
def recent_item():
    return {
        "title": "Recent Issue",
        "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "html_url": "https://api.github.com/repos/test-org/test-repo/issues/3"
    }

class TestRepoHealthCLI:
    
    @responses.activate
    def test_criterion_1_auth(self):
        """Test authentication via token."""
        responses.add(
            responses.GET,
            "https://api.github.com",
            body="{}",
            status=200
        )
        assert main.authenticate("fake") == True
        
        responses.add(
            responses.GET,
            "https://api.github.com",
            body="{}",
            status=401
        )
        assert main.authenticate("fake") == False

    @responses.activate
    def test_criterion_2_fetch_repos(self):
        """Test fetching all repos for an org."""
        responses.add(
            responses.GET,
            "https://api.github.com/orgs/test-org/repos",
            body=json.dumps([{"name": "repo1", "id": 1}]),
            status=200
        )
        repos = main.fetch_repos("token", "test-org")
        assert len(repos) == 1
        assert repos[0]["name"] == "repo1"

    @responses.activate
    def test_criterion_3_fetch_issues_and_prs(self):
        """Test fetching issues and PRs."""
        # Mock issues
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/repo1/issues",
            body=json.dumps([{"title": "Bug", "updated_at": "2023-01-01T00:00:00Z", "state": "open"}]),
            status=200
        )
        # Mock PRs
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/repo1/pulls",
            body=json.dumps([{"title": "Feat", "updated_at": "2023-01-01T00:00:00Z", "state": "open"}]),
            status=200
        )
        items = main.fetch_items("token", "repo1", "test-org")
        assert len(items) == 2
        assert items[0]['type'] == 'Issue'
        assert items[1]['type'] == 'PR'

    @responses.activate
    def test_criterion_4_filter_stale(self):
        """Test filtering items stale > 30 days."""
        items = [recent_item(), stale_item()]
        result = main.filter_stale(items, days=30)
        assert len(result) == 1
        assert result[0]['title'] == "Stale Issue"

    @responses.activate
    def test_criterion_5_generate_report(self):
        """Test generating a formatted Markdown report."""
        items = [{"title": "Issue 1", "html_url": "http://example.com"}]
        report = main.generate_report(items)
        assert "# Stale Issues and PRs" in report
        assert "Issue 1" in report

    @responses.activate
    def test_criterion_6_generate_script(self):
        """Test generating a shell script."""
        items = [{"title": "Issue 1", "html_url": "https://api.github.com/repos/test-org/test-repo/issues/1"}]
        script = main.generate_script(items)
        assert "#!/bin/bash" in script
        assert "test-repo#1" in script
