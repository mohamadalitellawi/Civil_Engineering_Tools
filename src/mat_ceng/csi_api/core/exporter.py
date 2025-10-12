# src/csi_api/core/exporter.py

import csv
from pathlib import Path
from datetime import datetime

def export_to_csv(data, filepath, headers=None):
    """
    Export list of dicts or list of lists to CSV.
    
    Args:
         list of dicts (preferred) or list of lists
        filepath: output CSV path
        headers: optional list of column names (required if data is list of lists)
    """
    if not data:
        raise ValueError("No data to export")

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if isinstance(data[0], dict):
            # Dict-based export
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            # List-based export
            if not headers:
                raise ValueError("Headers required for list-of-lists data")
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)

    return str(filepath)
