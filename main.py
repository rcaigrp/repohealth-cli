import requests
import sys
import os
from datetime import datetime
from rich.console import Console

console = Console()

def authenticate(token):
    if not token:
        console.print("[red]Error: No token provided. Use --token or set GITHUB_TOKEN.[/red]")
        sys.exit(1)
    return token

def fetch_repos(token, org, max_pages=10):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    repos = []
    page = 1
    while True:
        params = {"page": page, "per_page": 100}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            console.print(f"[red]Failed to fetch repos: {response.status_code}[/red]")
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
        if page > max_pages:
            break
    return repos

def fetch_issues(token, repos, max_pages=10):
    issues = []
    for repo in repos:
        owner_login = repo.get('owner', {}).get('login')
        if not owner_login:
            owner_login = repo.get('owner')
        repo_name = repo['name']
        url = f"https://api.github.com/repos/{owner_login}/{repo_name}/issues"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"state": "open", "per_page": 100}
        page = 1
        while True:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            if not data:
                break
            issues.extend(data)
            page += 1
            if page > max_pages:
                break
    return issues

def filter_stale(issues, stale_days=30):
    cutoff = datetime.now() - datetime.timedelta(days=stale_days)
    stale = []
    for issue in issues:
        try:
            updated = datetime.strptime(issue['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            if updated < cutoff:
                stale.append(issue)
        except Exception:
            continue
    return stale

def generate_report(issues):
    report = []
    for issue in issues:
        report.append({
            "title": issue.get('title'),
            "status": issue.get('state'),
            "updated": issue.get('updated_at')
        })
    return report

if __name__ == "__main__":
    token = os.environ.get('GITHUB_TOKEN')
    authenticate(token)
    org = "test-org"
    repos = fetch_repos(token, org)
    issues = fetch_issues(token, repos)
    stale = filter_stale(issues)
    report = generate_report(stale)
    console.print(f"[green]Found {len(stale)} stale issues.[/green]")
    console.print(report)
