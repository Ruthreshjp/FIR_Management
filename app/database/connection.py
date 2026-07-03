import os
import traceback

# Load .env manually if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Database:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")

        # Startup diagnostic
        if uri:
            print(f"[DB] MongoDB URI loaded: YES (length={len(uri)})")
        else:
            print("[DB] ERROR: MONGODB_URI is not set in .env")

        self.client = None
        self.db = None
        self.firs = None
        self.personnel = None

        if not uri:
            raise ValueError("MONGODB_URI environment variable is missing. Database cannot connect.")

        try:
            import certifi
            from pymongo import MongoClient

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
            print("[DB] MongoDB Atlas connected successfully!")
        except Exception as e:
            print(f"[DB] Failed to connect to MongoDB Atlas.")
            print(f"[DB] Full error: {traceback.format_exc()}")
            raise ConnectionError(f"Could not connect to MongoDB Atlas: {str(e)}")

    # ── Public API ──────────────────────────────────────
    def insert_fir(self, fir_record: dict) -> str:
        """Inserts a new FIR record strictly into MongoDB."""
        if self.firs is None:
            raise ConnectionError("Database collection not initialized.")
            
        try:
            result = self.firs.insert_one(fir_record)
            print(f"[DB] FIR saved to MongoDB: {fir_record.get('fir_number', 'unknown')}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"[DB] MongoDB insert failed: {e}")
            raise e

    def get_all_firs(self) -> list:
        """Retrieves all FIR records from MongoDB."""
        if self.firs is None:
            raise ConnectionError("Database collection not initialized.")
            
        try:
            cursor = self.firs.find().sort("created_at", -1)
            records = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                records.append(doc)
            return records
        except Exception as e:
            print(f"[DB] MongoDB query failed: {e}")
            raise e

    def update_fir(self, fir_number: str, update_fields: dict) -> bool:
        """Updates an existing FIR record in MongoDB."""
        if self.firs is None:
            raise ConnectionError("Database collection not initialized.")
            
        try:
            result = self.firs.update_one(
                {"fir_number": fir_number},
                {"$set": update_fields}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[DB] MongoDB update failed: {e}")
            raise e
