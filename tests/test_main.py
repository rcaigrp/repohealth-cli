import pytest
import responses
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')
from main import fetch_repos, fetch_issues, filter_stale, generate_report, generate_script

class TestRepoHealth:
    @responses.activate
    def test_fetch_repos(self):
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/test-org/repos?page=1&per_page=100',
            json=[{'name': 'repo1'}, {'name': 'repo2'}],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/test-org/repos?page=2&per_page=100',
            json=[],
            status=200
        )
        
        token = 'fake-token'
        org = 'test-org'
        repos = fetch_repos(token, org)
        assert len(repos) == 2
        assert repos[0]['name'] == 'repo1'

    @responses.activate
    def test_fetch_issues(self):
        responses.add(
            responses.GET,
            'https://api.github.com/repos/repo1/issues?page=1&per_page=100&state=open',
            json=[{'title': 'Issue 1', 'updated_at': '2020-01-01T00:00:00Z'}],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/repos/repo1/issues?page=2&per_page=100&state=open',
            json=[],
            status=200
        )
        token = 'fake-token'
        repo = 'repo1'
        issues = fetch_issues(token, repo)
        assert len(issues) == 1
        assert issues[0]['title'] == 'Issue 1'

    def test_filter_stale(self):
        items = [
            {'title': 'Old', 'updated_at': '2020-01-01T00:00:00Z'},
            {'title': 'New', 'updated_at': datetime.utcnow().isoformat() + 'Z'}
        ]
        stale = filter_stale(items, days=30)
        assert len(stale) == 1
        assert stale[0]['title'] == 'Old'

    def test_generate_report(self):
        items = [
            {'title': 'Test Issue', 'html_url': 'http://test.com'}
        ]
        report = generate_report(items)
        assert "# Stale Items Report" in report
        assert "Test Issue" in report

    def test_generate_script(self):
        items = [
            {'title': 'Test Issue', 'html_url': 'http://test.com'}
        ]
        script = generate_script(items)
        assert "#!/bin/bash" in script
        assert "http://test.com" in script
