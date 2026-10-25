import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    FRONTEND_ORIGIN, ADMIN_EMAIL, ADMIN_PASSWORD,
    UPLOAD_DIR, EVIDENCE_DIR, BASE_DIR, AI_WORKER_MODE, STORAGE_BACKEND
)
from app.database import Base, engine, SessionLocal
from app.models import Admin, FineRule, VideoJob
from app.auth import get_password_hash
from app.routes import (
    auth, dashboard, violations, videos, fine_rules, reports, public, worker
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Admin
        admin = db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first()
        if not admin:
            print(f"Seeding default admin: {ADMIN_EMAIL}")
            new_admin = Admin(
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD)
            )
            db.add(new_admin)
            db.commit()

        # 2. Seed Default Fine Rules
        default_rules = [
            ("Helmet Violation", 1000.0),
            ("Over Speeding", 2000.0),
            ("Red Light Violation", 1000.0),
            ("Triple Riding", 1000.0),
            ("Wrong Side Driving", 1500.0)
        ]
        for v_type, amt in default_rules:
            existing = db.query(FineRule).filter(FineRule.violation_type == v_type).first()
            if not existing:
                db.add(FineRule(violation_type=v_type, amount=amt, active=True))
        db.commit()

        # 3. Mark stuck jobs as failed on restart
        stuck_jobs = db.query(VideoJob).filter(VideoJob.status.in_(["processing"])).all()
        for j in stuck_jobs:
            j.status = "failed"
            j.error = "Server was restarted during processing."
        if stuck_jobs:
            db.commit()

        # 4. Start Embedded AI Worker
        from app.services.worker_service import start_embedded_worker, stop_embedded_worker
        start_embedded_worker()

        print(f"Server ready! AI Worker Mode: {AI_WORKER_MODE} (Memory optimized)")

    finally:
        db.close()

    yield
    print("Application shutdown initiated...")
    from app.services.worker_service import stop_embedded_worker
    stop_embedded_worker()
    print("Application shutdown complete.")

app = FastAPI(
    title="Traffic Sense API",
    description="Smart Traffic Violation Detection & Fine Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
base_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:4173",
    "https://traffic-sense-frontend.onrender.com",
]

allowed_origins_set = set(base_origins)
if FRONTEND_ORIGIN and FRONTEND_ORIGIN != "*":
    for origin_item in FRONTEND_ORIGIN.split(","):
        cleaned = origin_item.strip().strip("'\"").rstrip("/")
        if cleaned:
            allowed_origins_set.add(cleaned)

allowed_origins = list(allowed_origins_set)

# Match Render and Vercel domains; allow any origin if wildcard is configured
origin_regex = (
    r"https?://.*"
    if FRONTEND_ORIGIN == "*"
    else r"https://.*(\.onrender\.com|\.vercel\.app)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length", "X-Total-Count"],
    max_age=86400,
)

# Mount evidence and uploads static files
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

# Lightweight Health Check Route (< 5ms response, uses 0 MB extra RAM)
@app.get("/api/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "service": "traffic-sense-api",
        "models_loaded": True,
        "ai_worker_mode": AI_WORKER_MODE,
        "storage_backend": STORAGE_BACKEND
    }

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(violations.router)
app.include_router(videos.router)
app.include_router(fine_rules.router)
app.include_router(reports.router)
app.include_router(public.router)
app.include_router(worker.router)
