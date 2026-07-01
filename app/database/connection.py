import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

class Database:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        self.client = None
        self.db = None
        self.firs = None
        self.personnel = None

        if not uri:
            print("Warning: MONGODB_URI environment variable is missing. Database features disabled.")
            return
        
        try:
            self.client = MongoClient(
                uri, 
                serverSelectionTimeoutMS=5000,
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsCAFile=certifi.where()
            )
            # Force a call to check if the connection is successful
            self.client.admin.command('ping')
            self.db = self.client.autofir
            self.firs = self.db.firs
            self.personnel = self.db.personnel
        except Exception as e:
            print(f"Failed to connect to MongoDB Atlas. Error: {e}")
            self.client = None
            self.db = None
            self.firs = None
            self.personnel = None

    def insert_fir(self, fir_record: dict) -> str:
        """Inserts a new FIR record and returns its ID."""
        result = self.firs.insert_one(fir_record)
        return str(result.inserted_id)

    def get_all_firs(self) -> list:
        """Retrieves all FIR records, sorted by newest first. Falls back to sample data if DB is offline."""
        if self.client is None:
            import json
            sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_firs.json")
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        cursor = self.firs.find().sort("created_at", -1)
        # Convert ObjectId to string for easy serialization
        records = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            records.append(doc)
        return records

    def update_fir(self, fir_number: str, update_fields: dict) -> bool:
        """Updates an existing FIR record by its FIR number."""
        result = self.firs.update_one(
            {"fir_number": fir_number},
            {"$set": update_fields}
        )
        return result.modified_count > 0
