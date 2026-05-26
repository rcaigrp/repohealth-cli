import os
import sys
import requests
import datetime

def get_token(args_token):
    return args_token or os.environ.get("GITHUB_TOKEN")

def fetch_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}"}
    repos = []
    while url:
        response = requests.get(url, headers=headers, params={"per_page": 100})
        response.raise_for_status()
        repos.extend(response.json())
        if "next" not in response.links:
            break
        url = response.links["next"]["url"]
    return repos

def fetch_items(token, repos):
    items = []
    for repo in repos:
        repo_name = repo["full_name"]
        url = f"https://api.github.com/repos/{repo_name}/issues?state=open&per_page=100"
        headers = {"Authorization": f"token {token}"}
        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            for item in data:
                items.append({
                    "repo": repo_name,
                    "id": item["id"],
                    "type": "PR" if item.get("pull_request") else "Issue",
                    "title": item["title"],
                    "updated_at": item["updated_at"],
                    "state": item["state"]
                })
            if "next" not in response.links:
                break
            url = response.links["next"]["url"]
    return items

def filter_stale(items, stale_days):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=stale_days)
    stale = []
    for item in items:
        try:
            updated = datetime.datetime.strptime(item['updated_at'].split('T')[0], '%Y-%m-%d')
            if updated < cutoff:
                stale.append(item)
        except Exception:
            pass
    return stale