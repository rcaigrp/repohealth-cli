import os
import requests
from typing import List, Dict, Any

class RepoHealthClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {token}"})

    def fetch_org_repos(self, org: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/orgs/{org}/repos"
        repos = []
        page = 1
        while True:
            params = {"per_page": 100, "page": page}
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch repos: {response.text}")
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    def fetch_user_repos(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/user/repos"
        repos = []
        page = 1
        while True:
            params = {"per_page": 100, "page": page}
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch repos: {response.text}")
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    def fetch_repo_issues(self, repo: str, org: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/repos/{org}/{repo}/issues"
        issues = []
        page = 1
        while True:
            params = {"per_page": 100, "page": page, "state": "open"}
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch issues: {response.text}")
            data = response.json()
            if not data:
                break
            issues.extend(data)
            page += 1
        return issues

    def fetch_repo_prs(self, repo: str, org: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/repos/{org}/{repo}/pulls"
        prs = []
        page = 1
        while True:
            params = {"per_page": 100, "page": page, "state": "open"}
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch PRs: {response.text}")
            data = response.json()
            if not data:
                break
            prs.extend(data)
            page += 1
        return prs
