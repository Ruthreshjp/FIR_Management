import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# App Configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = "autofir"

# Email Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Blockchain (Polygon Amoy Testnet) Configuration
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "")
POLYGON_PRIVATE_KEY = os.getenv("POLYGON_PRIVATE_KEY", "")
POLYGON_CONTRACT_ADDRESS = os.getenv("POLYGON_CONTRACT_ADDRESS", "")

# Directory configurations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCAL_DB_FILE = os.path.join(DATA_DIR, "fir_db.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
