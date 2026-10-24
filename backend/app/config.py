import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic_sense.db")

# JWT & Security
JWT_SECRET = os.getenv("JWT_SECRET", "traffic_sense_jwt_secret_key_2026_super_secure")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours

# Default Admin credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@trafficsense.gov")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123456")

# CORS
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Storage backend (local | cloudinary | supabase)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
UPLOAD_DIR = BASE_DIR / "uploads"
EVIDENCE_DIR = UPLOAD_DIR / "evidence"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Cloudinary / Supabase config
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "evidence")

# AI Model Configuration
WEIGHTS_DIR = BASE_DIR / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

HELMET_MODEL_PATH = os.getenv("HELMET_MODEL_PATH", str(WEIGHTS_DIR / "helmet_yolov8.pt"))
if not os.path.isabs(HELMET_MODEL_PATH):
    HELMET_MODEL_PATH = str(BASE_DIR / HELMET_MODEL_PATH)

PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", str(WEIGHTS_DIR / "plate_yolov8.pt"))
if not os.path.isabs(PLATE_MODEL_PATH):
    PLATE_MODEL_PATH = str(BASE_DIR / PLATE_MODEL_PATH)

FRAME_STRIDE = int(os.getenv("FRAME_STRIDE", "3"))
MAX_VIDEO_MB = int(os.getenv("MAX_VIDEO_MB", "50"))
MAX_VIDEO_SECONDS = int(os.getenv("MAX_VIDEO_SECONDS", "90"))
