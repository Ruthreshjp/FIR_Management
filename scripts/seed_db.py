"""
One-time script to seed the MongoDB database with sample FIR data.
Run: python scripts/seed_db.py
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

from app.database.connection import Database

def main():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_firs.json")
    
    if not os.path.exists(data_path):
        print(f"ERROR: Seed file not found at {data_path}")
        sys.exit(1)
    
    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    db = Database()
    inserted = 0
    for record in records:
        try:
            db.insert_fir(record)
            inserted += 1
        except Exception as e:
            print(f"  Skipped: {e}")
    
    print(f"Done. Inserted {inserted}/{len(records)} seed records.")

if __name__ == "__main__":
    main()
