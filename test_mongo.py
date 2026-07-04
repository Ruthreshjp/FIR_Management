import os
from dotenv import load_dotenv
load_dotenv()
from pymongo import MongoClient
import traceback

uri = os.getenv("MONGODB_URI")
print("URI:", uri)
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Standard connection successful!")
except Exception as e:
    print("Standard connection failed:")
    traceback.print_exc()

print("---")

try:
    import certifi
    client2 = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where()
    )
    client2.admin.command('ping')
    print("Certifi connection successful!")
except Exception as e:
    print("Certifi connection failed:")
    traceback.print_exc()
