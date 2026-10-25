import os
import uuid
import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VideoJob, Violation, FineRule, StatusLog
from app.config import WORKER_SECRET_KEY, UPLOAD_DIR, AI_WORKER_MODE
from app.services.storage import get_storage_service

router = APIRouter(prefix="/api/worker", tags=["worker"])

# In-memory tracking of worker heartbeat
last_worker_heartbeat: Optional[datetime.datetime] = None

def record_heartbeat():
    """Records a live heartbeat from either the embedded worker or an external worker."""
    global last_worker_heartbeat
    last_worker_heartbeat = datetime.datetime.utcnow()

def verify_worker_token(x_worker_token: Optional[str] = Header(None)):
    """Verifies that the request comes from an authorized AI Inference Worker."""
    if not x_worker_token or x_worker_token != WORKER_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Worker-Token header."
        )
    record_heartbeat()
    return True


class JobProgressUpdate(BaseModel):
    progress: int
    vehicles_detected: int = 0
    violations_found: int = 0
    total_frames: Optional[int] = None


class JobCompletePayload(BaseModel):
    status: str # "completed" or "failed"
    error: Optional[str] = None
    vehicles_detected: int = 0
    violations_found: int = 0


@router.get("/status")
def get_worker_status():
    """Public/Admin endpoint to check AI Inference Worker connectivity."""
    global last_worker_heartbeat
    is_online = False
    seconds_ago = None
    if last_worker_heartbeat:
        diff = (datetime.datetime.utcnow() - last_worker_heartbeat).total_seconds()
        seconds_ago = int(diff)
        is_online = diff < 60

    return {
        "mode": AI_WORKER_MODE,
        "worker_online": is_online,
        "last_heartbeat_seconds_ago": seconds_ago,
        "message": (
            ("Embedded AI worker active" if AI_WORKER_MODE == "embedded" else "Worker online & connected")
            if is_online
            else "Waiting for worker to connect"
        )
    }


@router.get("/jobs/pending")
def get_pending_job(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker polls for the next queued video job."""
    job = db.query(VideoJob).filter(VideoJob.status == "queued").order_by(VideoJob.created_at.asc()).first()
    if not job:
        return {"has_job": False, "job": None}

    # Find the video file on disk
    video_files = list(UPLOAD_DIR.glob(f"*_{job.filename}"))
    if not video_files:
        # Check if direct filename exists
        direct = UPLOAD_DIR / job.filename
        if direct.exists():
            video_files = [direct]

    has_file = len(video_files) > 0
    return {
        "has_job": True,
        "job": {
            "id": job.id,
            "filename": job.filename,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "has_file": has_file
        }
    }


@router.get("/jobs/{job_id}/video")
def download_job_video(
    job_id: int,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker downloads video binary for inference."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    video_files = list(UPLOAD_DIR.glob(f"*_{job.filename}"))
    if not video_files:
        direct = UPLOAD_DIR / job.filename
        if direct.exists():
            video_files = [direct]

    if not video_files or not video_files[0].exists():
        raise HTTPException(status_code=404, detail="Video file not found on server")

    video_path = video_files[0]
    return FileResponse(
        path=str(video_path),
        filename=job.filename,
        media_type="video/mp4"
    )


@router.post("/jobs/{job_id}/start")
def start_job(
    job_id: int,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker marks that it has begun processing."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "processing"
    job.progress = 5
    db.commit()
    return {"status": "ok", "job_id": job.id}


@router.post("/jobs/{job_id}/progress")
def update_job_progress(
    job_id: int,
    payload: JobProgressUpdate,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker updates progress percentage and live counters."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.progress = payload.progress
    job.vehicles_detected = payload.vehicles_detected
    job.violations_found = payload.violations_found
    if payload.total_frames:
        job.total_frames = payload.total_frames

    db.commit()
    return {"status": "ok"}


@router.post("/jobs/{job_id}/violation")
def record_worker_violation(
    job_id: int,
    violation_type: str = Form(...),
    plate_number: str = Form(...),
    confidence: float = Form(0.85),
    fine_amount: Optional[float] = Form(None),
    location: str = Form("Sector 4 Junction - Pole CCTV #04"),
    notes: Optional[str] = Form(None),
    time_offset_sec: float = Form(0.0),
    evidence_file: Optional[UploadFile] = File(None),
    plate_crop_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker submits a detected violation with evidence HUD frame and plate crop."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Resolve fine amount from fine rules if not provided
    if fine_amount is None:
        rule = db.query(FineRule).filter(FineRule.violation_type == violation_type).first()
        fine_amount = rule.amount if rule else 1000.0

    storage = get_storage_service()

    # Save evidence file
    evidence_url = None
    if evidence_file and evidence_file.filename:
        ev_bytes = evidence_file.file.read()
        evidence_url = storage.save_image(ev_bytes, f"ev_{job_id}_{uuid.uuid4().hex[:6]}.jpg")

    # Save plate crop file
    plate_crop_url = None
    if plate_crop_file and plate_crop_file.filename:
        pl_bytes = plate_crop_file.file.read()
        plate_crop_url = storage.save_image(pl_bytes, f"plate_{job_id}_{uuid.uuid4().hex[:6]}.jpg")

    # Generate unique fine ref
    date_str = datetime.datetime.utcnow().strftime("%Y%m%d")
    while True:
        fine_ref = f"FN-{date_str}-{uuid.uuid4().hex[:4].upper()}"
        if not db.query(Violation).filter(Violation.fine_ref == fine_ref).first():
            break

    occ_time = job.created_at + datetime.timedelta(seconds=time_offset_sec)

    violation = Violation(
        fine_ref=fine_ref,
        plate_number=plate_number.strip().upper(),
        violation_type=violation_type,
        location=location,
        occurred_at=occ_time,
        fine_amount=float(fine_amount),
        status="Pending",
        source="AI",
        confidence=confidence,
        needs_review=False,
        evidence_url=evidence_url,
        plate_crop_url=plate_crop_url,
        video_job_id=job.id,
        notes=notes
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)

    # Initial status log
    log = StatusLog(
        violation_id=violation.id,
        old_status="None",
        new_status="Pending",
        notes=f"AI detection confirmed by Worker. Type: {violation_type}"
    )
    db.add(log)

    # Update job violation counter
    job.violations_found = db.query(Violation).filter(Violation.video_job_id == job.id).count()
    db.commit()

    return {"status": "ok", "violation_id": violation.id, "fine_ref": fine_ref}


@router.post("/jobs/{job_id}/complete")
def complete_job(
    job_id: int,
    payload: JobCompletePayload,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_worker_token)
):
    """Worker finalizes job status."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = payload.status
    job.progress = 100 if payload.status == "completed" else job.progress
    job.vehicles_detected = payload.vehicles_detected
    job.violations_found = payload.violations_found
    job.finished_at = datetime.datetime.utcnow()
    if payload.error:
        job.error = payload.error

    db.commit()

    # Clean up uploaded video file from Render disk to save space
    try:
        video_files = list(UPLOAD_DIR.glob(f"*_{job.filename}"))
        for vf in video_files:
            if vf.exists():
                os.remove(vf)
    except Exception:
        pass

    return {"status": "ok", "job_id": job.id, "final_status": job.status}
