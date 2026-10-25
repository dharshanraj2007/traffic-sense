import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import VideoJob, Admin, Violation
from app.schemas import VideoJobOut, VideoAnalyzeResponse
from app.auth import get_current_admin
from app.config import UPLOAD_DIR, MAX_VIDEO_MB, AI_WORKER_MODE

router = APIRouter(prefix="", tags=["videos"])

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov"}

@router.post("/api/videos/analyze", response_model=VideoAnalyzeResponse)
def analyze_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Check single-job queue if running embedded
    if AI_WORKER_MODE == "embedded":
        from app.services.detector import is_processing_active
        if is_processing_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The AI processing engine is currently busy analyzing another video. Please wait until it completes."
            )

    # Save to temp file and validate size
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    temp_path = UPLOAD_DIR / unique_filename

    max_bytes = MAX_VIDEO_MB * 1024 * 1024

    try:
        total_bytes = 0
        with open(temp_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024): # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    buffer.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Video file exceeds the {MAX_VIDEO_MB} MB limit. Please upload a shorter or compressed clip."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to receive video file: {str(e)}")

    # Create job in database
    job = VideoJob(
        filename=file.filename,
        status="queued",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Spawn background processing if embedded mode
    if AI_WORKER_MODE == "embedded":
        from app.services.detector import start_video_processing_thread
        start_video_processing_thread(job.id, str(temp_path), SessionLocal)
        msg = "Video uploaded successfully. AI processing started."
    else:
        msg = "Video uploaded successfully. AI analysis queued for worker."

    return VideoAnalyzeResponse(
        job_id=job.id,
        message=msg,
        filename=file.filename
    )


@router.get("/api/jobs/{job_id}", response_model=VideoJobOut)
@router.get("/api/videos/jobs/{job_id}", response_model=VideoJobOut)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    violations = db.query(Violation.id).filter(Violation.video_job_id == job_id).all()
    violation_ids = [v[0] for v in violations]

    res = VideoJobOut.model_validate(job)
    res.violation_ids = violation_ids
    return res


@router.get("/api/jobs", response_model=list[VideoJobOut])
def list_video_jobs(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    jobs = db.query(VideoJob).order_by(VideoJob.created_at.desc()).limit(20).all()
    out = []
    for j in jobs:
        v_ids = [v[0] for v in db.query(Violation.id).filter(Violation.video_job_id == j.id).all()]
        job_out = VideoJobOut.model_validate(j)
        job_out.violation_ids = v_ids
        out.append(job_out)
    return out
