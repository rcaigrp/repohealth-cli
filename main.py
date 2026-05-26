import requests
import json
from datetime import datetime, timedelta, timezone

class GitHubClient:
    def __init__(self, token, base_url="https://api.github.com"):
        self.token = token
        self.base_url = base_url

    def fetch_repos(self, org_or_user):
        url = f"{self.base_url}/orgs/{org_or_user}/repos"
        resp = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        resp.raise_for_status()
        return resp.json()

    def fetch_issues_and_prs(self, repo):
        issues_url = f"{self.base_url}/repos/{repo}/issues"
        prs_url = f"{self.base_url}/repos/{repo}/pulls"
        resp_issues = requests.get(issues_url, headers={"Authorization": f"Bearer {self.token}"})
        resp_issues.raise_for_status()
        resp_prs = requests.get(prs_url, headers={"Authorization": f"Bearer {self.token}"})
        resp_prs.raise_for_status()
        return resp_issues.json(), resp_prs.json()

def filter_stale(items, stale_days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    stale = []
    for item in items:
        try:
            updated = datetime.fromisoformat(item.get('updated_at', '').replace('Z', '+00:00'))
            if updated < cutoff:
                stale.append(item)
        except (ValueError, AttributeError):
            continue
    return stale

def generate_report(data):
    return json.dumps(data, indent=2)

def generate_shell_script(report_data):
    return f"#!/bin/bash\necho '{report_data}'"
