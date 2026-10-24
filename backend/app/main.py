import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    FRONTEND_ORIGIN, ADMIN_EMAIL, ADMIN_PASSWORD,
    UPLOAD_DIR, EVIDENCE_DIR, BASE_DIR
)
from app.database import Base, engine, SessionLocal
from app.models import Admin, FineRule, VideoJob
from app.auth import get_password_hash
from app.services.detector import AIModelManager
from app.routes import (
    auth, dashboard, violations, videos, fine_rules, reports, public
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
        stuck_jobs = db.query(VideoJob).filter(VideoJob.status.in_(["processing", "queued"])).all()
        for j in stuck_jobs:
            j.status = "failed"
            j.error = "Server was restarted during processing."
        if stuck_jobs:
            db.commit()

        # 4. Preload AI models
        print("Checking AI Models on startup...")
        AIModelManager.get_instance()

    finally:
        db.close()

    yield
    # Shutdown logic if any
    print("Application shutdown complete.")

app = FastAPI(
    title="Traffic Sense API",
    description="Smart Traffic Violation Detection & Fine Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_ORIGIN == "*" else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount evidence and uploads static files
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

# Health Check Route
@app.get("/api/health", tags=["system"])
def health_check():
    ai_mgr = AIModelManager.get_instance()
    return {
        "status": "ok",
        "models_loaded": ai_mgr.models_loaded
    }

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(violations.router)
app.include_router(videos.router)
app.include_router(fine_rules.router)
app.include_router(reports.router)
app.include_router(public.router)
