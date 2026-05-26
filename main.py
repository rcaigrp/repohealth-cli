import sys
import os
import requests
import argparse
from datetime import datetime, timedelta

def get_token(args):
    if args.token:
        return args.token
    return os.getenv('GH_TOKEN')

def fetch_repos(token, org):
    url = f'https://api.github.com/orgs/{org}/repos'
    headers = {'Authorization': f'Bearer {token}'}
    repos = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_issues(token, repo):
    url = f'https://api.github.com/repos/{repo}/issues'
    headers = {'Authorization': f'Bearer {token}'}
    issues = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100, 'state': 'open'}
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        if not data:
            break
        issues.extend(data)
        page += 1
    return issues

def filter_stale(items, days=30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    stale = []
    for item in items:
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        if updated < cutoff:
            stale.append(item)
    return stale

def generate_report(items):
    output = "# Stale Items Report\n\n"
    for item in items:
        output += f"- {item['title']} ({item['html_url']})\n"
    return output

def generate_script(items):
    script = "#!/bin/bash\n"
    for item in items:
        script += f"github close {item['html_url']}\n"
    return script

def main():
    parser = argparse.ArgumentParser(description='RepoHealth CLI')
    parser.add_argument('--org', required=True, help='GitHub organization')
    parser.add_argument('--token', help='GitHub token')
    parser.add_argument('--stale-days', type=int, default=30)
    parser.add_argument('--output', choices=['markdown', 'script'], default='markdown')
    
    args = parser.parse_args()
    
    token = get_token(args)
    if not token:
        print("Error: No token provided. Use --token or set GH_TOKEN env var.")
        sys.exit(1)
    
    repos = fetch_repos(token, args.org)
    all_items = []
    for repo in repos:
        issues = fetch_issues(token, repo['name'])
        all_items.extend(issues)
    
    stale_items = filter_stale(all_items, args.stale_days)
    
    if args.output == 'markdown':
        print(generate_report(stale_items))
    elif args.output == 'script':
        print(generate_script(stale_items))

if __name__ == '__main__':
    main()
