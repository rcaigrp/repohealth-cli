import requests
import datetime

def filter_stale_items(owner, repo, days):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    response = requests.get(url)
    items = response.json()
    
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days)
    
    stale_items = []
    for item in items:
        updated_at = item.get("updated_at")
        if updated_at:
            date_str = updated_at.replace("Z", "")
            item_date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            if item_date < cutoff:
                stale_items.append(item)
                
    return stale_items
