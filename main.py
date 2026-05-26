import argparse
import requests
import json
import sys
import os
from datetime import datetime, timedelta
from datetime import timezone as tz

def authenticate(token):
    url = "https://api.github.com"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
        return resp.status_code == 200
    except Exception:
        return False

def fetch_repos(token, org=None, user=None):
    url = f"https://api.github.com/orgs/{org}/repos" if org else f"https://api.github.com/users/{user}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    repos = []
    params = {"per_page": 100}
    
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return repos
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        if 'next' in resp.links:
            url = resp.links['next']['url']
        else:
            break
    return repos

def fetch_items(token, repo_name, owner):
    items = []
    # Fetch Issues
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"state": "open", "per_page": 100}
    
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        for item in data:
            item['type'] = 'Issue'
        items.extend(data)
        if 'next' in resp.links:
            url = resp.links['next']['url']
        else:
            break
            
    # Fetch PRs
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
    params = {"state": "open", "per_page": 100}
    
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        for item in data:
            item['type'] = 'PR'
        items.extend(data)
        if 'next' in resp.links:
            url = resp.links['next']['url']
        else:
            break
    return items

def filter_stale(items, days=30):
    now = datetime.now(tz.utc)
    stale = []
    for item in items:
        try:
            updated = item['updated_at']
            if updated.endswith('Z'):
                updated = updated[:-1] + '+00:00'
            dt = datetime.fromisoformat(updated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.utc)
            delta = now - dt
            if delta.days > days:
                stale.append(item)
        except (KeyError, ValueError):
            continue
    return stale

def generate_report(items):
    report = "# Stale Issues and PRs\n\n"
    for item in items:
        title = item.get('title', 'No Title')
        url = item.get('html_url', '')
        updated = item.get('updated_at', 'Unknown')
        report += f"- [{title}]({url}) (Updated: {updated})\n"
    return report

def generate_script(items):
    script = "#!/bin/bash\n"
    for item in items:
        url = item.get('html_url', '')
        parts = url.split('/')
        repo = parts[-4]
        number = parts[-1]
        script += f'echo "Closing {repo}#{number}"\n'
    return script
