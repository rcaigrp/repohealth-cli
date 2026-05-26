import argparse
import os
import requests
import json
import datetime
from rich.console import Console
from rich.table import Table

def parse_args():
    parser = argparse.ArgumentParser(description='RepoHealth CLI')
    parser.add_argument('--org', required=True, help='GitHub organization or user')
    parser.add_argument('--token', help='GitHub token (or use GITHUB_TOKEN env var)')
    parser.add_argument('--stale-days', type=int, default=30, help='Days to consider stale')
    parser.add_argument('--output', choices=['markdown', 'rich', 'json'], default='rich', help='Output format')
    parser.add_argument('--script', action='store_true', help='Generate shell script for stale items')
    parser.add_argument('--output-file', help='Output file path')
    return parser.parse_args()

def get_auth_token(token_arg):
    return token_arg or os.environ.get('GITHUB_TOKEN')

def fetch_repos(org, token):
    url = f'https://api.github.com/orgs/{org}/repos'
    repos = []
    headers = {'Authorization': f'token {token}'}
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise Exception(f'Failed to fetch repos: {resp.status_code}')
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_issues_and_prs(repos, token):
    items = []
    headers = {'Authorization': f'token {token}'}
    for repo in repos:
        repo_name = repo['full_name']
        url = f'https://api.github.com/repos/{repo_name}/issues'
        page = 1
        while True:
            params = {'state': 'open', 'per_page': 100, 'page': page}
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for item in data:
                item['repo'] = repo_name
                items.append(item)
            page += 1
        url = f'https://api.github.com/repos/{repo_name}/pulls'
        page = 1
        while True:
            params = {'state': 'open', 'per_page': 100, 'page': page}
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for item in data:
                item['repo'] = repo_name
                item['type'] = 'PR'
                items.append(item)
            page += 1
    return items

def filter_stale(items, stale_days):
    now = datetime.datetime.utcnow()
    stale = []
    for item in items:
        updated_at = item.get('updated_at')
        if updated_at:
            if updated_at.endswith('Z'):
                updated_at = updated_at[:-1]
            try:
                last_updated = datetime.datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                continue
            days_since = (now - last_updated).days
            if days_since > stale_days:
                stale.append(item)
    return stale

def generate_report(stale_items, output_format):
    if output_format == 'markdown':
        md = '# Stale Issues and PRs\n\n'
        md += '| Repo | Type | Title | Updated |\n'
        md += '|---|---|---|---|\n'
        for item in stale_items:
            title = item.get('title', '')
            updated = item.get('updated_at', 'N/A')
            repo = item.get('repo', '')
            item_type = item.get('type', 'Issue')
            md += f'| {repo} | {item_type} | {title} | {updated} |\n'
        return md
    elif output_format == 'json':
        return json.dumps(stale_items, indent=2)
    else:
        console = Console()
        table = Table(show_header=True, header_style='bold cyan')
        table.add_column('Repo', style='dim')
        table.add_column('Type')
        table.add_column('Title')
        table.add_column('Updated')
        for item in stale_items:
            table.add_row(item.get('repo', ''), item.get('type', 'Issue'), item.get('title', ''), item.get('updated_at', ''))
        console.print(table)
        return None

def generate_script(stale_items):
    script = '#!/bin/bash\n\n'
    for item in stale_items:
        repo = item.get('repo', '').replace('/', '-')
        if 'number' in item:
            num = item['number']
            script += f'gh issue close {repo}#{num} -m "Closing stale item"\n'
        elif 'id' in item:
            script += f'gh issue close {repo}#{item["id"]} -m "Closing stale item"\n'
    script += '\necho "Done"\n'
    return script

def main():
    args = parse_args()
    token = get_auth_token(args.token)
    if not token:
        print('Error: No GitHub token provided. Use --token or set GITHUB_TOKEN.')
        return
    repos = fetch_repos(args.org, token)
    items = fetch_issues_and_prs(repos, token)
    stale = filter_stale(items, args.stale_days)
    if args.output_file:
        with open(args.output_file, 'w') as f:
            if args.output == 'markdown':
                f.write(generate_report(stale, 'markdown'))
            elif args.output == 'json':
                f.write(generate_report(stale, 'json'))
            else:
                console = Console()
                table = Table(show_header=True, header_style='bold cyan')
                table.add_column('Repo')
                table.add_column('Type')
                table.add_column('Title')
                table.add_column('Updated')
                for item in stale:
                    table.add_row(item.get('repo', ''), item.get('type', 'Issue'), item.get('title', ''), item.get('updated_at', ''))
                console.print(table, file=f)
    else:
        if args.output == 'markdown' or args.output == 'json':
            print(generate_report(stale, args.output))
        else:
            generate_report(stale, 'rich')
    if args.script:
        print(generate_script(stale))

if __name__ == '__main__':
    main()
