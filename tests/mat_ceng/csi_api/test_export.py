# tests/test_export.py

import csv
from pathlib import Path
from mat_ceng.csi_api.core.exporter import export_to_csv

def test_export_dict_to_csv(tmp_path):
    data = [
        {"Name": "A", "Value": 1},
        {"Name": "B", "Value": 2}
    ]
    filepath = tmp_path / "output.csv"
    result = export_to_csv(data, filepath)

    assert Path(result).exists()
    with open(result, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["Name"] == "A"
        assert rows[0]["Value"] == "1"

def test_export_list_to_csv(tmp_path):
    data = [["A", 1], ["B", 2]]
    filepath = tmp_path / "output2.csv"
    result = export_to_csv(data, filepath, headers=["Name", "Value"])

    with open(result, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0] == ["Name", "Value"]
        assert rows[1] == ["A", "1"]