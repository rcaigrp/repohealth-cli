import argparse
import os
from monitor import fetch_repos, filter_stale, fetch_prs_issues
from report import generate_table, generate_markdown, generate_script

def main():
    parser = argparse.ArgumentParser(description="RepoHealth CLI")
    parser.add_argument("--org", help="GitHub organization name")
    parser.add_argument("--user", help="GitHub user name")
    parser.add_argument("--stale-days", type=int, default=30, help="Days threshold for stale items")
    parser.add_argument("--output-format", choices=["table", "markdown"], default="table")
    parser.add_argument("--generate-script", action="store_true", help="Generate bash script for batch closing")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN env var required")

    repos = fetch_repos(org=args.org, user=args.user)
    items = []
    if repos:
        items = fetch_prs_issues(repos)
    
    stale_items = filter_stale(items, args.stale_days)
    
    if args.output_format == "table":
        generate_table(stale_items)
    else:
        generate_markdown(stale_items)
        
    if args.generate_script:
        generate_script(stale_items)

if __name__ == "__main__":
    main()
