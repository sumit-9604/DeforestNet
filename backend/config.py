import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent / '.env'

# Load environment variables from .env file if it exists
load_dotenv(dotenv_path=env_path, override=True)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./deforest_net.db")

# Operations Mode
SIMULATION_MODE_ENV = os.getenv("SIMULATION_MODE", "True").lower() in ("true", "1", "yes")
SETTINGS_FILE = Path("/Users/stone/DeforestNet/backend/storage/settings.json")

class AppConfigState:
    def __init__(self):
        self._simulation_mode = self._load_simulation_mode()

    def _load_simulation_mode(self) -> bool:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("simulation_mode", SIMULATION_MODE_ENV)
            except Exception:
                pass
        return SIMULATION_MODE_ENV

    @property
    def simulation_mode(self) -> bool:
        return self._simulation_mode

    @simulation_mode.setter
    def simulation_mode(self, val: bool):
        self._simulation_mode = val
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump({"simulation_mode": val}, f)
        except Exception:
            pass

state = AppConfigState()
SIMULATION_MODE = SIMULATION_MODE_ENV

# Continuous monitoring. Set AGENT_SCHEDULER_ENABLED=false to run checks manually only.
AGENT_SCHEDULER_ENABLED = os.getenv("AGENT_SCHEDULER_ENABLED", "True").lower() in ("true", "1", "yes")
AGENT_RUN_ON_STARTUP = os.getenv("AGENT_RUN_ON_STARTUP", "True").lower() in ("true", "1", "yes")
AGENT_HUMAN_OVERSIGHT = os.getenv("AGENT_HUMAN_OVERSIGHT", "True").lower() in ("true", "1", "yes")
AGENT_SCAN_INTERVAL_SECONDS = max(60, int(os.getenv("AGENT_SCAN_INTERVAL_SECONDS", "3600")))

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
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@deforestnet.org")

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
