import argparse
import requests
import datetime
import os
import sys

def fetch_repos(org, token):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    return resp.json()

def fetch_issues_repos(repos, token):
    items = []
    for repo in repos:
        repo_name = repo['full_name']
        url = f"https://api.github.com/repos/{repo_name}/issues?state=open"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers)
        for issue in resp.json():
            issue['repo'] = repo_name
            items.append(issue)
        url = f"https://api.github.com/repos/{repo_name}/pulls?state=open"
        resp = requests.get(url, headers=headers)
        for pr in resp.json():
            pr['repo'] = repo_name
            pr['type'] = 'PR'
            items.append(pr)
    return items

def filter_stale(items, stale_days):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=stale_days)
    stale = []
    for item in items:
        updated = item['updated_at']
        try:
            updated_dt = datetime.datetime.fromisoformat(updated.replace('Z', '+00:00'))
            if updated_dt < cutoff:
                stale.append(item)
        except Exception:
            pass
    return stale

def generate_report(stale_items, output_format='markdown'):
    report = f"RepoHealth Report\n"
    report += f"=================\n"
    report += f"Stale Items: {len(stale_items)}\n\n"
    for item in stale_items:
        report += f"- {item['title']} ({item['repo']})\n"
    return report

def generate_script(stale_items, action='close'):
    script = "#!/bin/bash\n"
    script += f"# Batch {action} script for stale items\n\n"
    for item in stale_items:
        repo = item['repo']
        script += f"# curl -X PATCH -H 'Authorization: Bearer $GITHUB_TOKEN' https://api.github.com/repos/{repo}/issues/NUMBER -d '{{\"state\": \"{action}\"}}'\n"
    return script

def main():
    parser = argparse.ArgumentParser(description='Repo Health Checker')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    parser.add_argument('--token', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--stale-days', type=int, default=30, help='Days to consider stale')
    parser.add_argument('--output', default='report.md', help='Output file')
    args = parser.parse_args()

    repos = fetch_repos(args.org, args.token)
    items = fetch_issues_repos(repos, args.token)
    stale = filter_stale(items, args.stale_days)
    
    report = generate_report(stale)
    with open(args.output, 'w') as f:
        f.write(report)
    print(f"Report generated: {args.output}")

if __name__ == "__main__":
    main()
