import urllib.request
import urllib.error
import json
import datetime
import argparse
import sys

def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def get_auth_token():
    return "mock_token"

def fetch_repos(token, org):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    return fetch_json(url, headers)

def fetch_issues(token, repo):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"Bearer {token}"}
    return fetch_json(url, headers)

def filter_stale(items, stale_days):
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=stale_days)
    stale = []
    for item in items:
        if item.get('updated_at'):
            updated_str = item['updated_at'].replace('Z', '+00:00')
            try:
                last_updated = datetime.datetime.fromisoformat(updated_str)
                if last_updated < cutoff:
                    stale.append(item)
            except ValueError:
                continue
    return stale

def generate_report(stale_items):
    return f"## Stale Items Report\n\n{json.dumps(stale_items)}"

def generate_script(stale_items):
    return "#!/bin/bash\necho 'Batch closing items...'"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--org', required=True)
    parser.add_argument('--stale-days', type=int, default=30)
    parser.add_argument('--output', default='markdown')
    args = parser.parse_args()
    
    token = get_auth_token()
    repos = fetch_repos(token, args.org)
    all_items = []
    for repo in repos:
        issues = fetch_issues(token, repo['name'])
        all_items.extend(issues)
    
    stale = filter_stale(all_items, args.stale_days)
    
    if args.output == 'markdown':
        print(generate_report(stale))
    elif args.output == 'script':
        print(generate_script(stale))

if __name__ == '__main__':
    main()
