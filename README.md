# RepoHealth CLI

A Python CLI tool for tracking repository health, issue age, and PR activity across a GitHub organization or user account.

## Goal
Track PR age, issue status, and tech debt across a GitHub organization/user, outputting a formatted Markdown/ASCII report, with optional shell script generation for stale items.

## Acceptance Criteria
1. Authenticate via GitHub token (env var or CLI arg).
2. Fetch all repos for a specified org/user using `requests` and the GitHub REST API v3.
3. Fetch issues and PRs across repos.
4. Filter items stale > 30 days based on `updated_at`.
5. Generate a formatted Markdown/ASCII report using `rich` (or string).
6. Optionally generate a shell script to batch-close or label stale items.

## Usage
```bash
python main.py --org my-org --stale-days 30 --output markdown
```

## Test Commands
```bash
pip install requests rich responses pytest
pytest /workspace/projects/RepoHealth-CLI/acceptance_tests.py -v
```
