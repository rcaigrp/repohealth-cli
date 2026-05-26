import argparse
import requests
import datetime
import os
import sys

def get_token():
    parser = argparse.ArgumentParser(description="RepoHealth CLI")
    parser.add_argument('--token', help='GitHub API token')
    parser.add_argument('--org', help='Organization name')
    parser.add_argument('--stale_days', type=int, default=30, help='Days before considering item stale')
    parser.add_argument('--output', choices=['markdown', 'ascii'], default='markdown', help='Output format')
    args = parser.parse_args()
    
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: No GitHub token provided. Set GITHUB_TOKEN env var or use --token.")
        sys.exit(1)
    return token, args

def fetch_repos(token, org=None):
    if org:
        url = f"https://api.github.com/orgs/{org}/repos"
    else:
        url = "https://api.github.com/user/repos"
    
    headers = {"Authorization": f"token {token}"}
    repos = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_issues_and_prs(token, repos):
    items = []
    for repo in repos:
        owner = repo['full_name'].split('/')[0]
        name = repo['full_name'].split('/')[1]
        
        # Fetch Issues
        url = f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=100"
        headers = {"Authorization": f"token {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for issue in response.json():
                items.append({
                    'type': 'issue',
                    'repo': repo['full_name'],
                    'number': issue['number'],
                    'title': issue['title'],
                    'html_url': issue['html_url'],
                    'updated_at': issue['updated_at'],
                    'state': issue['state']
                })
        
        # Fetch PRs
        url = f"https://api.github.com/repos/{owner}/{name}/pulls?state=open&per_page=100"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for pr in response.json():
                items.append({
                    'type': 'pull_request',
                    'repo': repo['full_name'],
                    'number': pr['number'],
                    'title': pr['title'],
                    'html_url': pr['html_url'],
                    'updated_at': pr['updated_at'],
                    'state': pr['state']
                })
    return items

if __name__ == "__main__":
    token, args = get_token()
    repos = fetch_repos(token, args.org)
    print(f"Found {len(repos)} repos.")
    items = fetch_issues_and_prs(token, repos)
    print(f"Found {len(items)} items.")
