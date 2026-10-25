import os
import gc
import time
import uuid
import datetime
import threading
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import VideoJob
from app.config import UPLOAD_DIR, BASE_DIR, AI_WORKER_MODE
from app.routes.worker import record_heartbeat
from app.services.detector import process_video_job, is_processing_active, video_processing_lock

# Threading controls for embedded worker
_worker_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_worker_lock = threading.Lock()


def find_job_video_file(job_id: int, filename: str) -> Optional[Path]:
    """Finds the stored video file for a queued job on disk."""
    # 1. Direct job_id prefix
    matches = list(UPLOAD_DIR.glob(f"job_{job_id}_*"))
    if matches and matches[0].exists():
        return matches[0]

    # 2. General filename match in uploads
    matches = list(UPLOAD_DIR.glob(f"*_{filename}"))
    if matches and matches[0].exists():
        return matches[0]

    # 3. Direct filename match in uploads
    direct = UPLOAD_DIR / filename
    if direct.exists():
        return direct

    # 4. Check samples directory for test files
    sample = BASE_DIR / "samples" / filename
    if sample.exists():
        return sample

    return None


def _embedded_worker_loop():
    """Continuous queue polling loop running inside FastAPI lifespan."""
    print("Embedded AI Worker loop started. Polling for queued video jobs...")

    while not _stop_event.is_set():
        try:
            # Emit live heartbeat every iteration
            record_heartbeat()

            # Process queued jobs if no active processing is in flight
            if not is_processing_active:
                db: Session = SessionLocal()
                try:
                    # Find next queued job ordered by creation time
                    queued_job = (
                        db.query(VideoJob)
                        .filter(VideoJob.status == "queued")
                        .order_by(VideoJob.created_at.asc())
                        .first()
                    )

                    if queued_job:
                        job_id = queued_job.id
                        filename = queued_job.filename
                        print(f"[Embedded Worker] Found queued job #{job_id} ('{filename}'). Initiating processing...")

                        video_path = find_job_video_file(job_id, filename)

                        if not video_path or not video_path.exists():
                            print(f"[Embedded Worker] Video file for job #{job_id} ('{filename}') not found on server.")
                            queued_job.status = "failed"
                            queued_job.error = f"Video file for '{filename}' not found on server."
                            queued_job.finished_at = datetime.datetime.utcnow()
                            db.commit()
                        else:
                            # Mark job as processing with initial progress
                            queued_job.status = "processing"
                            queued_job.progress = 5
                            db.commit()

                            # Process the video job synchronously on this worker thread
                            # process_video_job manages model lifecycle and memory cleanup
                            process_video_job(job_id, str(video_path), SessionLocal)
                            print(f"[Embedded Worker] Finished processing job #{job_id}.")
                finally:
                    db.close()

        except Exception as e:
            print(f"[Embedded Worker] Loop exception: {e}")

        # Sleep briefly between poll cycles while remaining responsive to shutdown
        _stop_event.wait(3.0)

    print("Embedded AI Worker loop exited cleanly.")


def start_embedded_worker():
    """Starts the embedded worker thread if not already running."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return

        _stop_event.clear()
        _worker_thread = threading.Thread(
            target=_embedded_worker_loop,
            name="TrafficSense-EmbeddedWorker",
            daemon=True
        )
        _worker_thread.start()
        record_heartbeat()
        print("Embedded AI Worker service registered and running.")


def stop_embedded_worker():
    """Signals the embedded worker thread to terminate."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            print("Stopping Embedded AI Worker service...")
            _stop_event.set()
            _worker_thread.join(timeout=5.0)
            _worker_thread = None
            print("Embedded AI Worker service stopped.")
