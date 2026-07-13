import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./forest_guard.db")

# Operations Mode
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "True").lower() in ("true", "1", "yes")

# LLM Configurations
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # Options: 'gemini', 'claude', 'mock'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# Satellite APIs
SENTINEL_HUB_CLIENT_ID = os.getenv("SENTINEL_HUB_CLIENT_ID", "")
SENTINEL_HUB_CLIENT_SECRET = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "")
PLANET_API_KEY = os.getenv("PLANET_API_KEY", "")

# Notification Configurations
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@forestguard.org")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "forest-guard-super-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Directory for storing generated reports and imagery
STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
REPORTS_DIR = Path(STORAGE_DIR) / "reports"
IMAGERY_DIR = Path(STORAGE_DIR) / "imagery"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGERY_DIR.mkdir(parents=True, exist_ok=True)
