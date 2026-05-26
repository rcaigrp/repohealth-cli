import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import requests
import rich
from rich.console import Console
from rich.table import Table

console = Console()

class GitHubClient:
    def __init__(self, token, org):
        self.token = token
        self.org = org
        self.base_url = "https://api.github.com"

    def _get(self, endpoint, params=None):
        headers = {"Authorization": f"token {self.token}"}
        url = f"{self.base_url}/{endpoint}"
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp

    def fetch_repos(self):
        repos = []
        page = 1
        url = f"orgs/{self.org}/repos"
        while True:
            params = {"per_page": 100, "page": page}
            resp = self._get(url, params)
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
            if len(data) < 100:
                break
        return repos

    def fetch_issues(self, repo):
        issues = []
        page = 1
        url = f"repos/{self.org}/{repo}/issues"
        while True:
            params = {"per_page": 100, "page": page}
            resp = self._get(url, params)
            data = resp.json()
            if not data:
                break
            issues.extend(data)
            page += 1
            if len(data) < 100:
                break
        return issues

    def fetch_prs(self, repo):
        prs = []
        page = 1
        url = f"repos/{self.org}/{repo}/pulls"
        while True:
            params = {"per_page": 100, "page": page}
            resp = self._get(url, params)
            data = resp.json()
            if not data:
                break
            prs.extend(data)
            page += 1
            if len(data) < 100:
                break
        return prs

def filter_stale(items, stale_days=30, current_date=None):
    if current_date is None:
        current_date = datetime.utcnow().replace(tzinfo=None)
    threshold = current_date - timedelta(days=stale_days)
    stale = []
    for item in items:
        updated = item.get("updated_at") or item.get("closed_at") or item.get("created_at")
        if not updated:
            continue
        iso = updated.replace("Z", "+00:00")
        try:
            date = datetime.fromisoformat(iso)
            date = date.replace(tzinfo=None)
            if date < threshold:
                stale.append(item)
        except ValueError:
            continue
    return stale

def generate_report(stale_items, output_format="markdown"):
    table = Table(title="Stale Issues & PRs")
    table.add_column("Repo", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Updated At", style="red")
    table.add_column("State", style="magenta")

    for item in stale_items:
        repo = item.get("repository_url", "").split("/")[-1]
        title = item.get("title", "N/A")
        is_pr = "/pulls" in item.get("repository_url", "") or item.get("pull_request")
        item_type = "PR" if is_pr else "Issue"
        updated = item.get("updated_at", "N/A")
        state = item.get("state", "N/A")
        table.add_row(repo, title, item_type, updated, state)

    return table

def generate_shell_script(stale_items, output_file="batch_close.sh"):
    with open(output_file, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Batch close stale items\n")
        for item in stale_items:
            repo = item.get("repository_url", "").split("/")[-1]
            number = item.get("number", "")
            if item.get("pull_request"):
                f.write(f"# Close PR #{number} in {repo}\n")
                f.write(f"echo 'Closing PR #{number} in {repo}'\n")
            else:
                f.write(f"# Close Issue #{number} in {repo}\n")
                f.write(f"echo 'Closing Issue #{number} in {repo}'\n")
    console.print(f"[green]Shell script generated: {output_file}[/green]")

def main():
    parser = argparse.ArgumentParser(description="RepoHealth CLI - Track repository health, issue age, and PR activity.")
    parser.add_argument("--org", required=True, help="GitHub organization or user name")
    parser.add_argument("--token", help="GitHub API token (default: GITHUB_TOKEN env var)")
    parser.add_argument("--stale-days", type=int, default=30, help="Days since last update to consider stale (default: 30)")
    parser.add_argument("--output", default="markdown", help="Output format: markdown, json, table")
    parser.add_argument("--script", action="store_true", help="Generate shell script for batch operations")
    
    args = parser.parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        console.print("[red]Error: No GitHub token provided. Set GITHUB_TOKEN env var or use --token.[/red]")
        sys.exit(1)

    client = GitHubClient(token, args.org)
    console.print(f"[cyan]Fetching repos for {args.org}...[/cyan]")
    repos = client.fetch_repos()
    if not repos:
        console.print("[yellow]No repos found.[/yellow]")
        return

    console.print("[cyan]Fetching issues and PRs...[/cyan]")
    all_items = []
    for repo in repos:
        repo_name = repo["name"]
        issues = client.fetch_issues(repo_name)
        prs = client.fetch_prs(repo_name)
        for i in issues:
            i["repo"] = repo_name
        for p in prs:
            p["repo"] = repo_name
        all_items.extend(issues)
        all_items.extend(prs)

    console.print(f"[cyan]Total items fetched: {len(all_items)}[/cyan]")
    stale = filter_stale(all_items, args.stale_days)
    console.print(f"[yellow]Stale items (> {args.stale_days} days): {len(stale)}[/yellow]")

    if args.output == "markdown":
        console.print(generate_report(stale))
    elif args.output == "json":
        print(json.dumps(stale, indent=2))
    else:
        console.print(generate_report(stale))

    if args.script:
        generate_shell_script(stale)

if __name__ == "__main__":
    main()
