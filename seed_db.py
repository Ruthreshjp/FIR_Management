import sys
import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
import json
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
if not uri:
    print("Error: MONGODB_URI not set.")
    sys.exit(1)

client = MongoClient(uri)
db = client.autofir
firs = db.firs

print("Clearing existing dummy data...")
firs.delete_many({})

now = datetime.now(timezone.utc)

dummy_data = [
    {
        "fir_number": "FIR/2026/0719090001",
        "status": "Draft",
        "created_at": (now - timedelta(days=2)).isoformat(),
        "complainant_name": "Ramesh Kumar",
        "complainant_phone": "9876543210",
        "incident_location": "Anna Nagar, Chennai",
        "complaint_text": "My neighbor stole my bike.",
        "sections": [
            {"act": "BNS", "section_number": "303", "offense": "Theft", "title": "Theft"}
        ],
        "draft": "### 1. Complainant Details\nRamesh Kumar"
    },
    {
        "fir_number": "FIR/2026/0719090002",
        "status": "In Review",
        "created_at": (now - timedelta(hours=12)).isoformat(),
        "complainant_name": "Priya Sharma",
        "complainant_phone": "9123456789",
        "incident_location": "T Nagar, Chennai",
        "complaint_text": "I was attacked by two unknown men who snatched my gold chain.",
        "sections": [
            {"act": "BNS", "section_number": "309", "offense": "Robbery", "title": "Robbery"},
            {"act": "BNS", "section_number": "115", "offense": "Voluntarily causing hurt", "title": "Voluntarily causing hurt"}
        ],
        "draft": "### 1. Complainant Details\nPriya Sharma"
    },
    {
        "fir_number": "FIR/2026/0719090003",
        "status": "Filed",
        "created_at": (now - timedelta(minutes=45)).isoformat(),
        "complainant_name": "Karthik Raj",
        "complainant_phone": "9988776655",
        "incident_location": "Marina Beach, Chennai",
        "complaint_text": "Someone broke into my car and stole my laptop.",
        "sections": [
            {"act": "BNS", "section_number": "303", "offense": "Theft", "title": "Theft"}
        ],
        "draft": "### 1. Complainant Details\nKarthik Raj"
    }
]

print("Inserting dummy FIRs...")
firs.insert_many(dummy_data)
print("Dummy data seeded successfully!")
