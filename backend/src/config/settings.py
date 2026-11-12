import os
from pathlib import Path
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pipe-local.sqlite3")
LOCAL_TEST = os.getenv("LOCAL_TEST", "false").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "local-demo-secret-replace-in-production")
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "/tmp/pipe-priority-artifacts"))
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SEED_DEMO = os.getenv("SEED_DEMO", "true").lower() == "true"
