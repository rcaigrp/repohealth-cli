import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return token

def fetch_repos(org=None, user=None):
    token = get_token()
    if org:
        url = f"https://api.github.com/orgs/{org}/repos"
    elif user:
        url = f"https://api.github.com/users/{user}/repos"
    else:
        raise ValueError("Must specify either --org or --user")
    
    repos = []
    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    while True:
        params = {"page": page, "per_page": 100}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
        if resp.headers.get("X-RateLimit-Remaining") == "0":
            break
    return repos

def fetch_prs_issues(repos):
    token = get_token()
    items = []
    headers = {"Authorization": f"Bearer {token}"}
    
    for repo in repos:
        repo_name = repo["full_name"]
        url = f"https://api.github.com/repos/{repo_name}/issues"
        params = {"state": "open", "per_page": 100}
        page = 1
        while True:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 404:
                break
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            items.extend(data)
            page += 1
            if resp.headers.get("X-RateLimit-Remaining") == "0":
                break
    return items

def filter_stale(items, stale_days=30):
    now = datetime.utcnow()
    threshold = now - timedelta(days=stale_days)
    stale = []
    for item in items:
        try:
            updated = datetime.strptime(item["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            if updated < threshold:
                stale.append(item)
        except ValueError:
            continue
    return stale

def calculate_density(item):
    comments = item.get("comments", 0)
    days = (datetime.utcnow() - datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")).days
    if days == 0:
        return 0
    return round(comments / days, 2)
