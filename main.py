import argparse
import json
import requests
import csv
import io
import os
from datetime import datetime, timedelta

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {token}'})
        self.session.headers.update({'Accept': 'application/vnd.github.v3+json'})

    def get_repos(self, org=None, user=None):
        if org:
            url = f'https://api.github.com/orgs/{org}/repos'
        elif user:
            url = f'https://api.github.com/users/{user}/repos'
        else:
            raise ValueError("Must provide org or user")
        
        repos = []
        page = 1
        while True:
            params = {'per_page': 100, 'page': page}
            try:
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch repos: {response.text}")
                data = response.json()
                if not data:
                    break
                repos.extend(data)
                page += 1
            except Exception as e:
                raise e
        return repos

    def get_issues(self, repo_full_name):
        url = f'https://api.github.com/repos/{repo_full_name}/issues'
        issues = []
        page = 1
        while True:
            params = {'per_page': 100, 'page': page, 'state': 'open', 'sort': 'updated', 'direction': 'desc'}
            try:
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch issues: {response.text}")
                data = response.json()
                if not data:
                    break
                issues.extend(data)
                page += 1
            except Exception as e:
                raise e
        return issues

    def get_prs(self, repo_full_name):
        url = f'https://api.github.com/repos/{repo_full_name}/pulls'
        prs = []
        page = 1
        while True:
            params = {'per_page': 100, 'page': page, 'state': 'closed', 'sort': 'updated', 'direction': 'desc'}
            try:
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch PRs: {response.text}")
                data = response.json()
                if not data:
                    break
                prs.extend(data)
                page += 1
            except Exception as e:
                raise e
        return prs

    def filter_stale_issues(self, issues, days_threshold=30):
        """Filter out issues older than days_threshold."""
        cutoff = datetime.utcnow() - timedelta(days=days_threshold)
        active = []
        for i in issues:
            try:
                updated = i.get('updated_at', '').replace('Z', '+00:00').replace('z', '+00:00')
                if updated:
                    parsed = datetime.fromisoformat(updated)
                    if parsed > cutoff:
                        active.append(i)
            except Exception:
                continue
        return active

    def export_json(self, data, filename='report.json'):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return filename

    def export_csv(self, data, filename='report.csv'):
        if not data:
            return filename
        
        keys = data[0].keys() if isinstance(data[0], dict) else [k for k in data[0]]
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return filename

def main():
    parser = argparse.ArgumentParser(description='Repo Health CLI')
    parser.add_argument('--token', help='GitHub API Token')
    parser.add_argument('--org', help='Organization name')
    parser.add_argument('--user', help='GitHub username')
    parser.add_argument('--repo', help='Repository full name')
    parser.add_argument('--export', help='Export filename')
    
    args = parser.parse_args()
    
    if not args.token:
        print("Error: Token is required")
        return
    
    client = GitHubClient(args.token)
    
    if args.org or args.user:
        repos = client.get_repos(org=args.org, user=args.user)
        print(f"Found {len(repos)} repositories.")
        for repo in repos:
            print(f"- {repo['full_name']}")
    
    if args.repo:
        issues = client.get_issues(args.repo)
        prs = client.get_prs(args.repo)
        print(f"Repo: {args.repo}")
        print(f"Open Issues: {len(issues)}")
        print(f"Closed PRs: {len(prs)}")
        
        active_issues = client.filter_stale_issues(issues)
        print(f"Active Issues: {len(active_issues)}")
        
        if args.export:
            data = {"issues": issues, "prs": prs}
            if args.export.endswith('.json'):
                client.export_json(data, args.export)
            elif args.export.endswith('.csv'):
                flat_issues = [{"title": i['title'], "updated_at": i['updated_at']} for i in issues]
                client.export_csv(flat_issues, args.export)
            print(f"Exported to {args.export}")

if __name__ == '__main__':
    main()
