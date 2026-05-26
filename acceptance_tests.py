import pytest
import responses
import requests
from datetime import datetime, timedelta, timezone
import sys
import os
import io
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

TOKEN = "test-token"
ORG = "test-org"

@responses.activate
def test_criterion_1_auth():
    url = f"https://api.github.com/orgs/{ORG}/repos"
    responses.add(responses.GET, url, json=[{"full_name": f"{ORG}/repo1", "id": 1}], status=200)
    responses.add(responses.GET, url, json=[], status=200)
    repos = main.fetch_repos(TOKEN, ORG)
    assert len(repos) == 1

@responses.activate
def test_criterion_2_fetch_repos():
    url = f"https://api.github.com/orgs/{ORG}/repos"
    responses.add(responses.GET, url, json=[{"full_name": f"{ORG}/repo1", "id": 1}], status=200)
    responses.add(responses.GET, url, json=[], status=200)
    repos = main.fetch_repos(TOKEN, ORG)
    assert repos[0]["full_name"] == f"{ORG}/repo1"

@responses.activate
def test_criterion_3_fetch_issues_and_prs():
    repo_url = f"https://api.github.com/orgs/{ORG}/repos"
    responses.add(responses.GET, repo_url, json=[{"full_name": f"{ORG}/repo1", "id": 1}], status=200)
    responses.add(responses.GET, repo_url, json=[], status=200)
    
    issues_url = f"https://api.github.com/repos/{ORG}/repo1/issues"
    responses.add(responses.GET, issues_url, json=[{"title": "Issue 1", "updated_at": "2020-01-01T00:00:00Z", "html_url": "http://ex.com"}], status=200)
    responses.add(responses.GET, issues_url, json=[], status=200)
    
    items = main.fetch_issues_and_prs(TOKEN, [{"full_name": f"{ORG}/repo1", "id": 1}])
    assert len(items) == 1
    assert items[0]["title"] == "Issue 1"

@responses.activate
def test_criterion_4_filter_stale():
    items = [{"title": "Old Issue", "updated_at": "2020-01-01T00:00:00Z", "repo": "org/repo1", "html_url": "http://ex.com"}]
    stale = main.filter_stale(items, days=30)
    assert len(stale) == 1
    assert stale[0]['stale'] == True

@responses.activate
def test_criterion_5_generate_report():
    items = [{"title": "Issue 1", "updated_at": "2020-01-01T00:00:00Z", "repo": "org/repo1", "html_url": "http://ex.com"}]
    report = main.generate_report(items, "markdown")
    assert "Issue 1" in report
    assert "org/repo1" in report

@responses.activate
def test_criterion_6_generate_script():
    items = [{"title": "Issue 1", "updated_at": "2020-01-01T00:00:00Z", "repo": "org/repo1", "html_url": "http://ex.com"}]
    script = main.generate_script(items)
    assert "#!/bin/bash" in script
    assert "gh issue close" in script
