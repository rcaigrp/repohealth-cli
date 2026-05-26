import argparse
import requests
from datetime import datetime, timedelta, timezone
import sys

def fetch_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}"}
    repos = []
    page = 1
    while True:
        params = {"page": page, "per_page": 100}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_issues_and_prs(token, repos):
    items = []
    for repo in repos:
        url = f"https://api.github.com/repos/{repo['full_name']}/issues"
        headers = {"Authorization": f"token {token}"}
        page = 1
        while True:
            params = {"page": page, "per_page": 100, "state": "open"}
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for item in data:
                item['repo'] = repo['full_name']
                items.append(item)
            page += 1
    return items

def filter_stale(items, days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = []
    for item in items:
        updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        if updated_at < cutoff:
            item['stale'] = True
            stale.append(item)
    return stale

def generate_report(stale_items, output_format='markdown'):
    if output_format == 'markdown':
        report = "# Repo Health Report\n\n"
        report += f"Found {len(stale_items)} stale items.\n\n"
        for item in stale_items:
            report += f"- [{item['title']}]({item['html_url']}) ({item['repo']})\n"
        return report
    return ""

def generate_script(stale_items):
    script = "#!/bin/bash\n# Repo Health Stale Items Script\n\n"
    for item in stale_items:
        repo = item['repo'].replace('/', '-')
        script += f"# Close issue {item['title']} in {repo}\n"
        script += f"gh issue close {item['html_url'].split('/')[-1]} --repo {repo} --json title={item['title']} --json body='Closing stale issue.'\n"
    return script

def main():
    parser = argparse.ArgumentParser(description="Repo Health CLI")
    parser.add_argument("--org", required=True, help="GitHub organization")
    parser.add_argument("--token", required=True, help="GitHub token")
    parser.add_argument("--stale-days", type=int, default=30, help="Days to consider stale")
    parser.add_argument("--output", default="markdown", help="Output format")
    parser.add_argument("--script", action="store_true", help="Generate shell script")
    args = parser.parse_args()

    repos = fetch_repos(args.token, args.org)
    items = fetch_issues_and_prs(args.token, repos)
    stale = filter_stale(items, args.stale_days)
    
    if args.script:
        print(generate_script(stale))
    else:
        print(generate_report(stale, args.output))

if __name__ == "__main__":
    main()
