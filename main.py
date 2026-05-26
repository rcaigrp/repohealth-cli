import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import datetime
import tempfile


def fetch_json(url, token):
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        return []


def get_repos(org, token):
    url = f'https://api.github.com/orgs/{org}/repos'
    return fetch_json(url, token)


def get_issues_and_prs(org, token):
    repos = get_repos(org, token)
    items = []
    for repo in repos:
        repo_name = repo['name']
        issues_url = f"https://api.github.com/repos/{org}/{repo_name}/issues"
        issues = fetch_json(issues_url, token)
        for issue in issues:
            items.append({
                'type': 'issue',
                'repo': repo_name,
                'title': issue['title'],
                'updated_at': issue['updated_at'],
                'status': issue['state']
            })
        prs_url = f"https://api.github.com/repos/{org}/{repo_name}/pulls"
        prs = fetch_json(prs_url, token)
        for pr in prs:
            items.append({
                'type': 'pull_request',
                'repo': repo_name,
                'title': pr['title'],
                'updated_at': pr['updated_at'],
                'status': pr['state']
            })
    return items


def filter_stale(items, stale_days):
    threshold = datetime.datetime.now() - datetime.timedelta(days=stale_days)
    stale = []
    for item in items:
        try:
            updated = item['updated_at']
            if updated.endswith('Z'):
                updated = updated[:-1] + '+00:00'
            updated_dt = datetime.datetime.fromisoformat(updated)
            if updated_dt < threshold:
                stale.append(item)
        except Exception:
            continue
    return stale


def generate_report(stale_items, output_format='markdown'):
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Type")
    table.add_column("Repo")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Updated")
    
    for item in stale_items:
        table.add_row(
            item['type'],
            item['repo'],
            item['title'],
            item['status'],
            item['updated_at']
        )
    
    console.print(table)
    return table


def main():
    parser = argparse.ArgumentParser(description='Repo Health CLI')
    parser.add_argument('--token', required=True, help='GitHub API Token')
    parser.add_argument('--org', required=True, help='Organization name')
    parser.add_argument('--stale-days', type=int, default=30, help='Days to consider stale')
    args = parser.parse_args()
    
    print(f"Fetching data for {args.org}...")
    items = get_issues_and_prs(args.org, args.token)
    print(f"Found {len(items)} items.")
    
    stale = filter_stale(items, args.stale_days)
    print(f"Found {len(stale)} stale items.")
    
    generate_report(stale)


if __name__ == '__main__':
    main()