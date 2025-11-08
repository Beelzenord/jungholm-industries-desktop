"""Configuration for Gateway App"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Supabase configuration
# These should be set as environment variables or in a .env file
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# App configuration
APP_NAME = "jungholm industries"
APP_VERSION = "1.0.0"

# Storage keys
TOKEN_STORAGE_KEY = "jungholm_gateway_token"
REFRESH_TOKEN_STORAGE_KEY = "jungholm_gateway_refresh_token"
USER_ID_STORAGE_KEY = "jungholm_gateway_user_id"

# Offline queue settings
OFFLINE_QUEUE_FILE = Path.home() / ".jungholm_gateway" / "offline_queue.json"
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 2  # Exponential backoff: 2^attempt seconds

