import sys
import requests
from datetime import datetime, timedelta

def fetch_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers, params={"page": 1, "per_page": 100})
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")
    return response.json()

def fetch_issues(token, repo):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers, params={"state": "all", "per_page": 100})
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")
    return response.json()

def fetch_prs(token, repo):
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers, params={"state": "all", "per_page": 100})
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")
    return response.json()

def filter_stale(items, days):
    cutoff = datetime.now() - timedelta(days=days)
    stale = []
    for item in items:
        try:
            updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            if updated < cutoff:
                stale.append(item)
        except Exception:
            continue
    return stale

def generate_report(stale_items):
    report = "Stale Items Report\n"
    for item in stale_items:
        report += f"- {item.get('type', 'Issue')} {item.get('repo', '')}: {item.get('title', '')} (Last updated: {item.get('updated_at', '')})\n"
    return report

def generate_script(stale_items):
    lines = ["#!/bin/bash"]
    for item in stale_items:
        lines.append(f"echo 'Closing {item.get('title', '')}'")
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    token = None
    org = None
    days = 30
    
    if '--token' in args:
        token = args[args.index('--token') + 1]
    if '--org' in args:
        org = args[args.index('--org') + 1]
    if '--days' in args:
        days = int(args[args.index('--days') + 1])
        
    print(f"Token: {token}, Org: {org}, Days: {days}")

if __name__ == "__main__":
    main()
