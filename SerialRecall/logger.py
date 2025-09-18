# CSV logger with append and header creation
import os
import csv
from datetime import datetime
from typing import Dict, Any

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def append_row_csv(filepath: str, row: Dict[str, Any]):
    ensure_dir(os.path.dirname(filepath))
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def timestamp():
    return datetime.utcnow().isoformat()
