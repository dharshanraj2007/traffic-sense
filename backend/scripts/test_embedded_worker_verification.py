import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD

def run_worker_verification():
    print("======================================================================")
    print("STARTING EMBEDDED WORKER VERIFICATION TEST WITH REAL VIDEO")
    print("======================================================================")

    with TestClient(app) as client:
        # 1. Login to obtain JWT
        login_resp = client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("[PASSED] Authenticated admin session obtained.")

        # Give the worker thread 2 seconds to initialize and register first heartbeat
        time.sleep(2.0)

        # 2. Verify worker status & heartbeat
        status_resp = client.get("/api/worker/status", headers=auth_headers)
        assert status_resp.status_code == 200, f"Failed status check: {status_resp.text}"
        status_data = status_resp.json()
        print(f"[STATUS] Initial Worker Status: {status_data}")

        assert status_data["worker_online"] is True, "Expected worker_online=True"
        assert status_data["last_heartbeat_seconds_ago"] is not None, "Expected heartbeat timestamp"
        assert status_data["last_heartbeat_seconds_ago"] <= 10, f"Heartbeat too old: {status_data['last_heartbeat_seconds_ago']}s"
        print("[PASSED] Worker is online and emitting active heartbeats.")

        # 3. Submit real video file
        sample_path = BASE_DIR / "samples" / "sample_motorcycle_traffic.mp4"
        assert sample_path.exists(), f"Sample video not found at {sample_path}"

        print(f"[UPLOAD] Submitting real video '{sample_path.name}' ({sample_path.stat().st_size} bytes)...")
        with open(sample_path, "rb") as vf:
            upload_resp = client.post(
                "/api/videos/analyze",
                headers=auth_headers,
                files={"file": (sample_path.name, vf, "video/mp4")}
            )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        job_id = upload_data["job_id"]
        print(f"[PASSED] Job #{job_id} submitted. Initial response: {upload_data['message']}")

        # 4. Monitor job lifecycle transitions: QUEUED -> PROCESSING -> COMPLETED
        print(f"[MONITOR] Tracking Job #{job_id} progress...")
        saw_processing = False
        saw_progress_increase = False
        final_job = None

        start_time = time.time()
        while time.time() - start_time < 60: # 60s timeout
            job_resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
            assert job_resp.status_code == 200, f"Could not fetch job: {job_resp.text}"
            job_info = job_resp.json()
            status = job_info["status"]
            progress = job_info["progress"]
            vehicles = job_info["vehicles_detected"]
            violations = job_info["violations_found"]

            print(f" -> Job #{job_id} | Status: {status.upper():10s} | Progress: {progress:3d}% | Vehicles: {vehicles} | Violations: {violations}")

            if status == "processing":
                saw_processing = True

            if progress > 0 and status in ["processing", "completed"]:
                saw_progress_increase = True

            if status in ["completed", "failed"]:
                final_job = job_info
                break

            time.sleep(2.0)

        assert final_job is not None, "Job timed out before finishing."
        assert saw_processing or final_job["status"] == "completed", "Job never transitioned through processing"
        assert saw_progress_increase or final_job["status"] == "completed", "Job progress never increased"
        assert final_job["status"] == "completed", f"Job failed with error: {final_job.get('error')}"
        assert final_job["progress"] == 100, f"Expected 100% progress, got {final_job['progress']}%"
        print(f"[PASSED] Job #{job_id} completed with status 'completed' and 100% progress!")

        # 5. Verify Violations created
        v_ids = final_job.get("violation_ids", [])
        print(f"[VIOLATIONS] Found {len(v_ids)} violations associated with Job #{job_id}.")
        for vid in v_ids:
            v_detail = client.get(f"/api/violations/{vid}", headers=auth_headers).json()
            print(f" -> Violation #{vid}: {v_detail.get('violation_type')} | Plate: {v_detail.get('plate_number')} | Challan: {v_detail.get('fine_ref')}")

        # 6. Verify Worker remains online and operational after processing
        post_status = client.get("/api/worker/status", headers=auth_headers).json()
        print(f"[STATUS] Post-processing Worker Status: {post_status}")
        assert post_status["worker_online"] is True, "Worker went offline after processing"
        assert post_status["last_heartbeat_seconds_ago"] is not None and post_status["last_heartbeat_seconds_ago"] <= 10
        print("[PASSED] Worker remains operational and actively heartbeating after job completion.")

        # 7. Check for duplicate workers or locked state
        from app.services.detector import is_processing_active
        assert is_processing_active is False, "Expected is_processing_active to reset to False"
        print("[PASSED] Concurrency locks reset cleanly. Ready for next job.")

    print("\n======================================================================")
    print("ALL WORKER VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    run_worker_verification()
