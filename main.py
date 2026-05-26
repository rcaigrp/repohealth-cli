import argparse
import requests
import sys
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def fetch_repos(token, org):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/orgs/{org}/repos"
    repos = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200 or not resp.json():
            break
        repos.extend(resp.json())
        page += 1
    return repos

def fetch_issues(token, repo_name):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{repo_name}/issues"
    issues = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page, "state": "open"}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200 or not resp.json():
            break
        issues.extend(resp.json())
        page += 1
    return issues

def filter_stale(items, stale_days):
    cutoff = datetime.now() - timedelta(days=stale_days)
    stale = []
    for item in items:
        try:
            updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            if updated < cutoff:
                stale.append(item)
        except (KeyError, ValueError):
            continue
    return stale

def generate_report(stale_items):
    report = "RepoHealth Stale Report\n" + "="*30 + "\n"
    for item in stale_items:
        report += f"- {item['title']} (ID: {item['id']})\n"
        report += f"  Updated: {item['updated_at']}\n"
        report += f"  State: {item['state']}\n\n"
    return report

def main():
    parser = argparse.ArgumentParser(description='RepoHealth CLI')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    parser.add_argument('--stale-days', type=int, default=30, help='Days to consider stale')
    parser.add_argument('--token', required=True, help='GitHub Token')
    args = parser.parse_args()
    
    repos = fetch_repos(args.token, args.org)
    console.print(f"Found {len(repos)} repos.")
    
    stale_items = []
    for repo in repos:
        issues = fetch_issues(args.token, repo['name'])
        stale = filter_stale(issues, args.stale_days)
        stale_items.extend(stale)
        
    report = generate_report(stale_items)
    console.print(report)

if __name__ == '__main__':
    main()
