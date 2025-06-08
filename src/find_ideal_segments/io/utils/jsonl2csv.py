import csv
from ..jsonl import JsonlIO

def jsonl2csv(jsonl_path:str, csv_path:str):
    with JsonlIO(dict, jsonl_path) as jsonl, open(csv_path, 'w', newline='') as csvfile:
        initialized = False
        for item in jsonl:
            item = dict(item)
            if not initialized:
                writer = csv.DictWriter(csvfile, fieldnames=item.keys())
                writer.writeheader()
                initialized = True
            writer.writerow(item)