import json
from datetime import datetime

def calculate_duration(start_str, end_str, fmt='%Y-%m-%d %H:%M'):
    start = datetime.strptime(start_str, fmt)
    end = datetime.strptime(end_str, fmt)
    delta = end - start
    return delta.total_seconds() / 3600

def parse_entries(entries_json):
    return json.loads(entries_json)

def format_duration(hours):
    if hours < 0:
        return '0.00'
    return f'{hours:.2f}'