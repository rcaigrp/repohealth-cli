import os
import sys
import json
import requests
import datetime
import argparse


def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)
    return token


def fetch_repos(token, org=None, user=None):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/orgs/{org}/repos" if org else f"https://api.github.com/users/{user}/repos"
    repos = []
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching repos: {resp.status_code} {resp.text}")
            return []
        data = resp.json()
        repos.extend(data)
        if "next" in resp.headers.get("Link", ""):
            import re
            match = re.search(r"<([^ ]+)>; rel=\"next\"", resp.headers["Link"])
            if match:
                url = match.group(1)
            else:
                url = None
        else:
            url = None
    return repos


def fetch_issues_and_prs(token, repos):
    headers = {"Authorization": f"token {token}"}
    items = []
    for repo in repos:
        url = f"https://api.github.com/repos/{repo['full_name']}/issues"
        while url:
            resp = requests.get(url, headers=headers, params={"state": "open"})
            if resp.status_code != 200:
                print(f"Error fetching issues for {repo['full_name']}: {resp.status_code}")
                break
            data = resp.json()
            for item in data:
                item["repo_name"] = repo["full_name"]
                items.append(item)
            if "next" in resp.headers.get("Link", ""):
                import re
                match = re.search(r"<([^ ]+)>; rel=\"next\"", resp.headers["Link"])
                if match:
                    url = match.group(1)
                else:
                    url = None
            else:
                url = None
    return items


def filter_stale(items, days=30):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = datetime.timedelta(days=days)
    stale = []
    for item in items:
        updated = datetime.datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
        if now - updated > delta:
            stale.append(item)
    return stale


def generate_report(stale_items, output_format="markdown"):
    if output_format == "markdown":
        report = "# Stale Issues and PRs\n\n"
        for item in stale_items:
            report += f"- {item['title']} ({item['repo_name']})\n"
        return report
    else:
        report = "+------------------------+------------------+\n"
        report += "| Item                   | Repo             |\n"
        report += "+------------------------+------------------+\n"
        for item in stale_items:
            report += f"| {item['title']:<24s} | {item['repo_name']:<16s} |\n"
        report += "+------------------------+------------------+\n"
        return report


def generate_script(stale_items, action="close"):
    script = "#!/bin/bash\n\n"
    script += "# Environment variable GITHUB_TOKEN must be set\n"
    script += "if [ -z \"$GITHUB_TOKEN\" ]; then echo 'Set GITHUB_TOKEN'; exit 1; fi\n\n"
    for item in stale_items:
        repo = item['repo_name']
        url = f"https://api.github.com/repos/{repo}/issues/{item['number']}"
        if action == "close":
            script += f'curl -X PATCH "{url}" \\\n  -H "Authorization: token $GITHUB_TOKEN" \\\n  -H "Accept: application/vnd.github.v3+json" \\\n  -d \'{{"state": "closed"}}\'\n\n'
        elif action == "label":
            script += f'curl -X PATCH "{url}" \\\n  -H "Authorization: token $GITHUB_TOKEN" \\\n  -H "Accept: application/vnd.github.v3+json" \\\n  -d \'{{"labels": ["stale"]}}\'\n\n'
    return script


def main():
    parser = argparse.ArgumentParser(description="RepoHealth CLI")
    parser.add_argument("--org", help="GitHub organization")
    parser.add_argument("--user", help="GitHub user")
    parser.add_argument("--stale-days", type=int, default=30, help="Days to consider stale")
    parser.add_argument("--output", default="markdown", help="Output format")
    parser.add_argument("--script-format", default="close", help="Script format: close, label")
    args = parser.parse_args()

    token = get_token()
    repos = fetch_repos(token, org=args.org, user=args.user)
    items = fetch_issues_and_prs(token, repos)
    stale = filter_stale(items, args.stale_days)

    report = generate_report(stale, args.output)
    print(report)

    if args.script_format:
        script = generate_script(stale, args.script_format)
        print(script)


if __name__ == "__main__":
    main()
