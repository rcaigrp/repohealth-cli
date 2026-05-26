import argparse
import requests
import sys
from datetime import datetime, timedelta, timezone
import rich
from rich.console import Console

console = Console()

def get_repos(token, org=None, username=None):
    if org:
        url = f"https://api.github.com/orgs/{org}/repos"
    elif username:
        url = f"https://api.github.com/users/{username}/repos"
    else:
        raise ValueError("Provide either --org or --username")
    
    headers = {"Authorization": f"Bearer {token}"}
    repos = []
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
        if resp.status_code != 200:
            console.print(f"[red]Failed to fetch repos: {resp.status_code}[/red]")
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_issues_and_prs(token, repos):
    items = []
    for repo in repos:
        owner = repo['owner']['login']
        name = repo['name']
        url = f"https://api.github.com/repos/{owner}/{name}/issues"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, params={"state": "open", "per_page": 100})
        if resp.status_code == 200:
            items.extend(resp.json())
    return items

def filter_stale(items, days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = []
    for item in items:
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        if updated < cutoff:
            stale.append(item)
    return stale

def generate_report(stale_items, output_format='markdown'):
    console = Console()
    console.print("# Stale Issues & PRs Report")
    console.print(f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"Total stale items: {len(stale_items)}\n")
    for item in stale_items:
        console.print(f"- [{item['title']}]({item['html_url']})")
