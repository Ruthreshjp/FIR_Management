import json
from app.database.connection import Database
from app.retrieval.chroma_store import initialize_chroma_store, collection
from datetime import datetime, timezone
import traceback

def run_test():
    try:
        print("1. Connecting to DB...")
        db = Database()
        print("2. Getting FIRs...")
        firs = db.get_all_firs()
        print(f"   Got {len(firs)} FIRs.")
        
        print("3. Checking JSON serialization of FIRs...")
        try:
            json.dumps(firs)
            print("   JSON serialization OK.")
        except Exception as e:
            print(f"   JSON serialization FAILED: {e}")
            raise e

        print("4. Calculating summary...")
        open_this_month = 0
        pending_review = 0
        now = datetime.now(timezone.utc)
        
        for f in firs:
            status = f.get('status', '').lower()
            if status in ('draft', 'in review', 'pending review'):
                pending_review += 1
                
            created_at = f.get('created_at')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if dt.year == now.year and dt.month == now.month:
                        open_this_month += 1
                except:
                    pass
        print(f"   open_this_month={open_this_month}, pending_review={pending_review}")

        print("5. Initializing ChromaDB...")
        initialize_chroma_store()
        
        print("6. Getting ChromaDB count...")
        total_sections = 0
        try:
            total_sections = collection.count()
            print(f"   Count: {total_sections}")
        except Exception as e:
            print(f"   Count FAILED: {e}")
            
        print("7. Final JSON serialization check...")
        summary = {
            "open_this_month": open_this_month,
            "pending_review": pending_review,
            "total_sections_indexed": total_sections
        }
        json.dumps({"firs": firs, "summary": summary})
        print("   All OK. No 500 error found.")
        
    except Exception as e:
        print(f"\nCRASH OCCURRED:\n{traceback.format_exc()}")

if __name__ == '__main__':
    run_test()
