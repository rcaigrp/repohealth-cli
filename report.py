import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from monitor import calculate_density

console = Console()

def generate_table(items):
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repo")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Author")
    table.add_column("Days Open")
    table.add_column("Density")
    table.add_column("Link")
    
    for item in items:
        if "repository" in item:
            repo = item["repository"]["full_name"]
        else:
            repo = item.get("html_url", "").split("/")[4]
        num = item.get("number", item.get("id"))
        type_ = "PR" if item.get("pull_request") else "Issue"
        author = item.get("user", {}).get("login", "unknown")
        days = (datetime.utcnow() - datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")).days
        density = calculate_density(item)
        link = item.get("html_url", "#")
        table.add_row(str(repo), str(num), type_, author, str(days), str(density), link)
    console.print(table)

def generate_markdown(items):
    md = Markdown(f"# Stale Items Report\n\n{len(items)} items found.\n\n")
    console.print(md)

def generate_script(items):
    token = os.environ.get("GITHUB_TOKEN")
    script = "#!/bin/bash\n# Stale Items Cleanup Script\n\n"
    for item in items:
        script += f"curl -X PATCH -H 'Authorization: Bearer {token}' -H 'Content-Type: application/json' -d '{{\"state\":\"closed\"}}' '{item['html_url']}'\n"
    console.print(script)
