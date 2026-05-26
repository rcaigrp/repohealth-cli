# RepoHealth CLI

A Python CLI tool to monitor GitHub organization health by fetching repos, issues, and pull requests.

## Features
- Fetches all repos for a given organization.
- Retrieves issues and pull requests.
- Filters items based on staleness (e.g., items not updated in 30 days).
- Generates a formatted markdown report using `rich`.

## Usage
```bash
python main.py --token YOUR_TOKEN --org YOUR_ORG --stale-days 30
```

## Testing
Run tests with:
```bash
pytest acceptance_tests.py -v
```