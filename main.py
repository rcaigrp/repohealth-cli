import argparse
import os
import requests
import datetime
import sys


def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required.")
        sys.exit(1)
    return token


def fetch_repos(token, org=None, user=None):
    headers = {"Authorization": f"token {token}"}
    base_url = f"https://api.github.com/orgs/{org}/repos" if org else f"https://api.github.com/users/{user}/repos"
    repos = []
    url = base_url
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        repos.extend(data)
        if 'next' not in response.links:
            break
        url = response.links['next']['url']
    return repos


def fetch_issues_and_prs(token, repos):
    items = []
    for repo in repos:
        url = f"https://api.github.com/repos/{repo['full_name']}/issues?state=open"
        headers = {"Authorization": f"token {token}"}
        while url:
            response = requests.get(url, headers=headers)
            data = response.json()
            for item in data:
                item['repo_name'] = repo['full_name']
                items.append(item)
            if 'next' not in response.links:
                break
            url = response.links['next']['url']
    return items


def filter_stale(items, days=30, now=None):
    if now is None:
        now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(days=days)
    stale = []
    for item in items:
        updated = datetime.datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        if updated < cutoff:
            stale.append(item)
    return stale


def generate_report(stale_items, org=None, user=None):
    report = f"# RepoHealth Report\n\n"
    if org:
        report += f"## Organization: {org}\n"
    elif user:
        report += f"## User: {user}\n"
    report += f"\nTotal Stale Items: {len(stale_items)}\n\n"
    for item in stale_items:
        report += f"- [{item['title']}](\"{item['html_url']}\")\n"
    return report


def generate_script(stale_items, org=None, user=None):
    script = "#!/bin/bash\n\n"
    if org:
        script += f"ORG=\"{org}\"\n"
    elif user:
        script += f"USER=\"{user}\"\n"
    script += 'TOKEN="${1:-$GITHUB_TOKEN}"\n\n'
    for item in stale_items:
        repo = item.get('repo_name')
        if not repo:
            continue
        number = item.get('number')
        if not number:
            continue
        script += f'curl -X POST -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github.v3+json" "https://api.github.com/repos/{repo}/issues/{number}/comments" -d \'{{"body": "This issue is stale."}}\'\n'
    return script
