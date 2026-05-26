import requests
import argparse
import json
from datetime import datetime, timedelta
import sys

def get_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    return resp.json()

def get_items(token, repo):
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=100"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    return resp.json()

def filter_stale(items, now=None, days=30):
    if now is None:
        from datetime import datetime
        now = datetime.now()
    cutoff = now - timedelta(days=days)
    stale = []
    for item in items:
        updated_at_str = item.get('updated_at')
        if updated_at_str:
            updated_at_str = updated_at_str.replace('Z', '+00:00')
            updated_at = datetime.fromisoformat(updated_at_str)
            if updated_at < cutoff:
                stale.append(item)
    return stale

def generate_report(stale_items, repo_name):
    report = f"Stale items in {repo_name}:\n"
    report += "-" * 40 + "\n"
    for item in stale_items:
        title = item.get('title', 'N/A')
        url = item.get('html_url', 'N/A')
        report += f"- [{title}]({url})\n"
    report += "-" * 40 + "\n"
    return report

def main():
    parser = argparse.ArgumentParser(description="RepoHealth CLI")
    parser.add_argument("--org", required=True, help="GitHub Organization")
    parser.add_argument("--token", default="fake", help="GitHub Token")
    parser.add_argument("--stale-days", type=int, default=30, help="Days threshold")
    parser.add_argument("--output", default="markdown", help="Output format")
    args = parser.parse_args()
    
    repos = get_repos(args.token, args.org)
    
    all_stale = []
    for repo in repos:
        repo_name = repo.get('name')
        items = get_items(args.token, repo_name)
        stale = filter_stale(items, now=None, days=args.stale_days)
        all_stale.append((repo_name, stale))
        
    if args.output == "markdown":
        print("Report Generated (Markdown)")
    else:
        print("Report Generated (ASCII)")

if __name__ == "__main__":
    main()
