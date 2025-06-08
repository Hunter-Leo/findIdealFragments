import sys
sys.path.append('.')
from src.find_ideal_segments.io.utils.jsonl2csv import jsonl2csv

if __name__ == "__main__":
    jsonl2csv(
        "result.jsonl",
        "result.csv",
    )
