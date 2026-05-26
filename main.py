import argparse
import requests
import sys
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def fetch_repos(token, org):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/orgs/{org}/repos"
    repos = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            console.print(f"[red]Error fetching repos: {response.status_code}[/red]")
            sys.exit(1)
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_items(token, repo, item_type):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{repo}/issues" if item_type == "issues" else f"https://api.github.com/repos/{repo}/pulls"
    params = {"state": "closed", "per_page": 100}
    items = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            console.print(f"[red]Error fetching {item_type}: {response.status_code}[/red]")
            break
        data = response.json()
        if not data:
            break
        items.extend(data)
        page += 1
    return items

def filter_stale(items, stale_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    stale = []
    for item in items:
        last_updated_str = item.get("closed_at") or item.get("updated_at")
        if not last_updated_str:
            continue
        if last_updated_str.endswith("Z"):
            last_updated_str = last_updated_str[:-1] + "+00:00"
        last_updated = datetime.fromisoformat(last_updated_str)
        if last_updated < cutoff:
            stale.append(item)
    return stale

def generate_report(repos, stale_items):
    report = f"# RepoHealth Report\n\n"
    report += f"## Stale Items ({len(stale_items)} found)\n\n"
    for repo in repos:
        repo_name = repo["name"]
        repo_stale = [i for i in stale_items if i["repository_url"].startswith(f"https://api.github.com/repos/{repo['owner']['login']}/{repo_name}")]
        if repo_stale:
            report += f"### {repo_name}\n\n"
            for item in repo_stale:
                title = item["title"]
                url = item["html_url"]
                report += f"- [{title}]({url})\n"
            report += "\n"
    return report

def main():
    parser = argparse.ArgumentParser(description="GitHub Repo Health CLI")
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--org", required=True, help="GitHub Organization or User")
    parser.add_argument("--stale-days", type=int, default=30, help="Days since last update to consider stale")
    args = parser.parse_args()

    console.print(f"[blue]Fetching repos for {args.org}...[/blue]")
    repos = fetch_repos(args.token, args.org)
    console.print(f"[green]Found {len(repos)} repos.[/green]")

    stale_items = []
    for repo in repos:
        console.print(f"[blue]Fetching issues for {repo['name']}...[/blue]")
        issues = fetch_items(args.token, repo["full_name"], "issues")
        stale_items.extend(issues)
        
        console.print(f"[blue]Fetching PRs for {repo['name']}...[/blue]")
        prs = fetch_items(args.token, repo["full_name"], "pulls")
        stale_items.extend(prs)

    console.print(f"[blue]Filtering stale items (>{args.stale_days} days)...[/blue]")
    stale_items = filter_stale(stale_items, args.stale_days)
    console.print(f"[green]Found {len(stale_items)} stale items.[/green]")

    report = generate_report(repos, stale_items)
    console.print(Markdown(report))

if __name__ == "__main__":
    main()
