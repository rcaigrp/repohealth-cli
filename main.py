import datetime
import requests

def fetch_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    repos = []
    page = 1
    while True:
        params = {"page": page, "per_page": 100}
        try:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching repos: {e}")
            break
    return repos

def fetch_items(token, repo):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"state": "open", "sort": "updated", "direction": "desc"}
    try:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError:
        return []

def filter_stale(items, stale_days, now=None):
    if now is None:
        now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=stale_days)
    stale = []
    for item in items:
        updated = item["updated_at"]
        if updated.endswith("Z"):
            updated = updated.replace("Z", "+00:00")
        else:
            updated = updated.replace("T", " ").replace("Z", " ")
        try:
            updated_dt = datetime.datetime.fromisoformat(updated)
        except ValueError:
            continue
        if updated_dt < cutoff:
            stale.append(item)
    return stale

def generate_report(stale_items, output_format):
    if output_format == "markdown":
        report = "Stale Items Report\n\n"
        for item in stale_items:
            report += f"- {item['title']} ({item['html_url']})\n"
        return report
    return ""
