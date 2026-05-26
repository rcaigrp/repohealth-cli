import requests
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

class GitHubClient:
    def __init__(self, token, org=None, user=None):
        self.token = token
        self.org = org
        self.user = user
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def fetch_repos(self):
        url = f"{self.base_url}/orgs/{self.org}/repos" if self.org else f"{self.base_url}/users/{self.user}/repos"
        repos = []
        while url:
            response = self.session.get(url)
            response.raise_for_status()
            repos.extend(response.json())
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        return repos

    def fetch_issues_and_prs(self, repo_name):
        url = f"{self.base_url}/repos/{self.org}/{repo_name}/issues"
        items = []
        while url:
            response = self.session.get(url)
            response.raise_for_status()
            items.extend(response.json())
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        return items

    def filter_stale(self, items, days=30):
        cutoff = datetime.utcnow() - timedelta(days=days)
        stale = []
        for item in items:
            updated = datetime.strptime(item['updated_at'].replace('Z', '+00:00'), '%Y-%m-%dT%H:%M:%S%z')
            if updated < cutoff:
                stale.append(item)
        return stale

def generate_report(stale_items, repos):
    console = Console()
    console.print("[bold red]Stale Issues and PRs Report[/bold red]")
    console.print(f"Total Repos: {len(repos)}")
    console.print(f"Stale Items: {len(stale_items)}")
    console.print("-" * 50)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Updated")
    
    for item in stale_items:
        table.add_row(str(item.get('id', '')), item['title'], item['state'], item['updated_at'])
    
    console.print(table)

def generate_shell_script(stale_items, output_file='close_stale.sh'):
    with open(output_file, 'w') as f:
        f.write("#!/bin/bash\n")
        for item in stale_items:
            repo = item.get('repository', {})
            owner = repo.get('owner', {})
            login = owner.get('login', '')
            name = repo.get('name', '')
            f.write(f'curl -X PATCH -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" -d \'{{"state": "closed"}}\' "https://api.github.com/repos/{login}/{name}/issues/{item["number"]}"\n')
    print(f"Script generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="RepoHealth CLI")
    parser.add_argument('--token', required=True, help='GitHub Token')
    parser.add_argument('--org', help='Organization name')
    parser.add_argument('--user', help='User name')
    parser.add_argument('--stale-days', type=int, default=30, help='Stale days threshold')
    parser.add_argument('--output', default='markdown', help='Output format')
    parser.add_argument('--script', action='store_true', help='Generate shell script')
    
    args = parser.parse_args()
    
    client = GitHubClient(args.token, org=args.org, user=args.user)
    repos = client.fetch_repos()
    
    stale_items = []
    for repo in repos:
        items = client.fetch_issues_and_prs(repo['name'])
        stale = client.filter_stale(items, args.stale_days)
        stale_items.extend(stale)
    
    generate_report(stale_items, repos)
    
    if args.script:
        generate_shell_script(stale_items)

if __name__ == "__main__":
    main()
