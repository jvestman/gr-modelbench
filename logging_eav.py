import csv
from config import LOG_FILE

def log_generation_eav(entity_id: str, data: dict):
    file_exists = LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["entity", "attribute", "value"])
        for k, v in data.items():
            writer.writerow([entity_id, k, v])
