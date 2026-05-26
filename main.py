import argparse
import os
import sys
import requests
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def fetch_repos(token, org):
    url = f'https://api.github.com/orgs/{org}/repos'
    headers = {'Authorization': f'token {token}'}
    repos = []
    page = 1
    while True:
        params = {'per_page': 100, 'page': page}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            console.print(f"[red]Failed to fetch repos: {resp.status_code}[/red]")
            sys.exit(1)
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_issues_and_prs(token, repos):
    items = []
    for repo in repos:
        owner = repo['owner']['login']
        name = repo['name']
        base_url = f"https://api.github.com/repos/{owner}/{name}/issues"
        headers = {'Authorization': f'token {token}'}
        page = 1
        while True:
            params = {'per_page': 100, 'page': page, 'state': 'all'}
            resp = requests.get(base_url, headers=headers, params=params)
            if resp.status_code != 200:
                console.print(f"[red]Failed to fetch issues for {owner}/{name}: {resp.status_code}[/red]")
                break
            data = resp.json()
            if not data:
                break
            for item in data:
                if 'title' in item:
                    item['repo'] = f"{owner}/{name}"
                    items.append(item)
            page += 1
    return items

def filter_stale(items, stale_days):
    cutoff = datetime.utcnow() - timedelta(days=stale_days)
    stale = []
    for item in items:
        if 'updated_at' not in item:
            continue
        updated_at = datetime.strptime(item['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if updated_at < cutoff:
            stale.append(item)
    return stale

def generate_report(stale_items, output_format='markdown'):
    report = []
    if output_format == 'markdown':
        report.append("# RepoHealth Report\n")
        report.append(f"## Stale Items ({len(stale_items)})\n")
        for item in stale_items:
            report.append(f"- **{item['title']}** ({item['repo']})\n")
    elif output_format == 'ascii':
        report.append("RepoHealth Report")
        report.append("=" * 20)
        report.append(f"Stale Items: {len(stale_items)}\n")
        for item in stale_items:
            report.append(f"- {item['title']} ({item['repo']})\n")
    return "\n".join(report)

def generate_script(stale_items, action='close', token=None):
    if not token:
        token = os.environ.get('GITHUB_TOKEN')
    script = "#!/bin/bash\n"
    for item in stale_items:
        url = f"https://api.github.com/repos/{item['repo']}/issues/{item['number']}"
        if action == 'close':
            script += f'curl -X PATCH {url} -H "Authorization: token {token}" -H "Content-Type: application/json" -d \'{{"state": "closed"}}\'\n'
        elif action == 'label':
            script += f'curl -X PATCH {url} -H "Authorization: token {token}" -H "Content-Type: application/json" -d \'{{"labels": ["stale"]}}\'\n'
    return script

def main():
    parser = argparse.ArgumentParser(description='RepoHealth CLI')
    parser.add_argument('--org', required=True, help='Organization or user name')
    parser.add_argument('--stale-days', type=int, default=30, help='Days to consider stale')
    parser.add_argument('--output', type=str, default='markdown', choices=['markdown', 'ascii'], help='Output format')
    parser.add_argument('--token', default=None, help='GitHub token')
    parser.add_argument('--action', type=str, default=None, help='Action for script generation')
    
    args = parser.parse_args()
    
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        console.print("[red]No GitHub token provided. Use --token or set GITHUB_TOKEN env var.[/red]")
        sys.exit(1)
        
    repos = fetch_repos(token, args.org)
    console.print(f"[green]Fetched {len(repos)} repos.[/green]")
    
    items = fetch_issues_and_prs(token, repos)
    console.print(f"[green]Fetched {len(items)} issues/PRs.[/green]")
    
    stale = filter_stale(items, args.stale_days)
    console.print(f"[yellow]Found {len(stale)} stale items.[/yellow]")
    
    report = generate_report(stale, args.output)
    console.print(report)
    
    if args.action:
        script = generate_script(stale, args.action, token)
        console.print(f"Generated script for {args.action} action.")
        console.print(script)

if __name__ == '__main__':
    main()
