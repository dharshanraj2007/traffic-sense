# PRD: Smart Traffic Violation Detection & Fine Management System

**Audience:** Antigravity (AI coding agent). **Time budget:** 2 hours total. **Rule #1:** no model training. Use pretrained weights only.

## 0. Instructions to the agent (read first)

1. Build the whole project (frontend + backend) in ONE monorepo with `/frontend` and `/backend`.
2. Work in the phases in Section 10. Finish and commit Phase 1 fully before starting Phase 2. A working Phase 1 is the fallback if AI work runs late.
3. Do NOT train or fine-tune any model. Do NOT download large datasets.
4. Prefer simple, boring, reliable choices over clever ones. Every external call (model download, OCR, DB, storage) must have error handling and a fallback.
5. Test the model weight download URLs in Section 6 first. If one fails, use the listed fallback and keep going. Do not stop to ask.
6. Reference repos in Section 6 are for reading and borrowing ideas only. Do not fork them wholesale. Respect licenses (Ultralytics is AGPL-3.0).
7. Deliver a README with local run steps, env vars, and deploy steps.

## 1. Product summary

A web system where an admin uploads traffic video. The backend detects vehicles, finds motorcycle riders without helmets, reads the number plate, generates a fine automatically, stores the evidence image, and shows everything in an admin dashboard with fine payment status and reports.

**Scope decision:** Only **helmet violation** is required for AI detection. Do not build speeding, red light, or wrong lane. They are not in the requirements.

## 2. Goals and non-goals

**Goals**
- Phase 1 (basic site): home page with project info, admin login + dashboard, manual violation entry, fine management table, working database.
- Phase 2 (AI): vehicle detection, helmet violation detection, number plate recognition, automatic fine generation, evidence image storage, fine payment status management, violation history, report generation.
- Input is a traffic video file (mp4/avi/mov).
- Deployable: frontend on Vercel, backend on Render.

**Non-goals**
- Model training, real-time live CCTV streaming, real payment gateway, facial recognition, multi-tenant users, mobile app.

## 3. Users

- **Admin (traffic officer):** logs in, uploads video, reviews detections, edits/approves fines, marks paid, exports reports.
- **Visitor:** sees the public home page only. (Optional bonus: public "Check my fine" page by plate number.)

## 4. Tech stack (fixed, do not change)

| Layer | Choice |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS + React Router (or Next.js if faster; pick one and stay with it). Deploy to Vercel. |
| Backend | Python 3.11 + FastAPI + Uvicorn. Deploy to Render as a Docker web service. |
| AI | Ultralytics YOLOv8 (pretrained), EasyOCR, OpenCV (headless), CPU-only PyTorch. |
| Database | SQLAlchemy ORM. SQLite locally; PostgreSQL in production via `DATABASE_URL` (Neon or Supabase free tier recommended, because Render's disk is ephemeral). |
| Evidence storage | Abstract `StorageService` with two implementations: local disk (dev) and Cloudinary or Supabase Storage (prod), chosen by env var. |
| Auth | JWT (python-jose) + bcrypt (passlib). Single seeded admin from env vars. |
| Reports | CSV export + PDF export (reportlab or fpdf2). |

## 5. Functional requirements

### 5.1 Phase 1: Basic site

**F1. Home page (public).** Project title, problem statement, how it works (4 steps), features list, tech used, team names (Chitra S, Linsha LJ), SDG 11 badge, "Admin Login" button. Clean, responsive.

**F2. Admin login.** Email + password, JWT stored in memory plus localStorage, protected routes, logout. Admin seeded on startup from `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

**F3. Dashboard.** Cards: total violations, pending fines, paid fines, total fine amount collected. Charts: violations per day (line), by status (donut). Recent 10 violations table.

**F4. Manual violation entry.** Form: plate number, violation type (dropdown, default Helmet), location, date/time, fine amount (auto-filled from fine rules), optional evidence image upload, notes.

**F5. Fine management table.** Columns: ID, plate, type, date, location, amount, status (Pending, Paid, Cancelled), evidence thumbnail, source (Manual or AI). Search by plate, filter by status/date, pagination, row actions: view details, mark paid, cancel, edit, delete.

**F6. Database.** Tables in Section 8, created automatically on startup.

### 5.2 Phase 2: AI pipeline

**F7. Video upload.** Admin uploads a video on an "Analyze Video" page. Limits: max 50 MB, max 90 seconds, formats mp4/avi/mov. Reject others with a clear message. Backend returns a `job_id` immediately.

**F8. Async processing.** Processing runs in a background task. The UI polls `GET /api/jobs/{id}` every 2 seconds and shows status (queued, processing with progress %, done, failed) and a live count of violations found.

**F9. Vehicle detection.** COCO-pretrained `yolov8n.pt`. Classes used: person, car, motorcycle, bus, truck. Use `model.track(..., persist=True, tracker="bytetrack.yaml")` for track IDs. Output vehicle counts per job.

**F10. Helmet violation detection.** For each tracked motorcycle: find persons whose box overlaps the motorcycle (rider candidates). Run the helmet model on the rider's head region (top ~40% of the person box, or the full person crop). If the helmet model says "no helmet" with confidence >= 0.5 in at least 3 frames for the same motorcycle track, raise ONE violation for that track. Never raise duplicates for the same track ID.

**F11. Number plate recognition.** For a violating motorcycle, crop the vehicle region on each frame where it is visible. Run the plate detector, then EasyOCR on the plate crop (upscale 2x, grayscale, contrast enhance). Keep the best reading across frames (highest OCR confidence that matches the Indian plate regex). Normalize: uppercase, strip spaces and symbols, fix common confusions by position (0/O, 1/I, 5/S, 8/B). Regex: `^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$`. If no valid read, save plate as `UNREADABLE` and flag for manual review (admin can edit the plate in the UI).

**F12. Automatic fine generation.** On violation creation, look up the fine amount from `fine_rules` (default Helmet = Rs 1,000, editable, seeded at startup). Create the violation with status Pending, a fine reference like `FN-YYYYMMDD-XXXX`, and a timestamp (video time offset + upload time).

**F13. Evidence image storage.** Save an annotated frame (bounding boxes + label) and a plate crop for each violation via `StorageService`. Store URLs in the DB. Evidence must display in the fine table and detail view.

**F14. Fine payment status management.** Admin marks Pending to Paid (records `paid_at`, optional payment reference) or Cancelled. Simulated only, no real gateway. Status changes are logged.

**F15. Violation history and reports.** History page with filters (date range, status, plate, type). Export filtered results as CSV and PDF. Summary report: counts by day, by status, total fine, collected vs pending.

## 6. AI models and reference repositories (no training)

| Purpose | Source | Notes |
|---|---|---|
| Vehicle + person detection | `yolov8n.pt` from Ultralytics (auto-downloads on first use). Repo: https://github.com/ultralytics/ultralytics | COCO pretrained. Includes ByteTrack. |
| Helmet / no-helmet | Hugging Face model `sharathhhhh/safetyHelmet-detection-yolov8` (YOLOv8 .pt, classes Helmet / No Helmet). Download with `huggingface_hub.hf_hub_download` at Docker build time. | Verify the exact filename in the repo. Fallback 1: search Hugging Face / Roboflow Universe for another pretrained "helmet" YOLOv8 .pt with a "no helmet" class. Fallback 2: `killuminati1/construction-ppe-yolov8` on Hugging Face (has a No-Helmet class, but trained on construction sites, so lower accuracy on bikers). Make the weight path and class names configurable via env vars. |
| License plate detection | Weights `best.pt` from https://github.com/madalinabuzatu/yolov8-license-plate-detection/releases/download/v1.0/best.pt | Test the download at build time. Fallback: any pretrained YOLOv8 license plate .pt from Hugging Face or Roboflow Universe. Last resort: run EasyOCR on the lower half of the motorcycle crop. |
| OCR | EasyOCR. Repo: https://github.com/JaidedAI/EasyOCR | English only, `gpu=False`. Pre-download models in the Dockerfile so cold starts do not fetch them. |

**Reference repos (read for pipeline ideas, do not copy blindly):**
- https://github.com/computervisioneng/automatic-number-plate-recognition-python-yolov8 (vehicle detect, plate detect, EasyOCR pipeline; its plate model is NOT public, use the weights above)
- https://github.com/SakshamJr/Automatic-Vehicle-Number-Plate-Recognition
- https://github.com/fedei10/Car-Detection
- https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8 (helmet inference script pattern)

**Accuracy expectation:** pretrained models will be imperfect on Indian roads, night footage, and low resolution. Design the UI so every AI violation can be reviewed, edited, or cancelled by the admin. Provide a "Needs review" flag when the plate is unreadable or confidence is low.

## 7. Backend API

All `/api/*` routes except `/api/auth/login`, `/api/health`, and `/api/public/*` require `Authorization: Bearer <jwt>`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Returns `{status:"ok", models_loaded:bool}` for Render health check |
| POST | `/api/auth/login` | Email + password, returns JWT |
| GET | `/api/auth/me` | Current admin |
| GET | `/api/dashboard/stats` | Cards + chart data |
| GET/POST | `/api/violations` | List (filters, pagination) / manual create |
| GET/PUT/DELETE | `/api/violations/{id}` | Detail / edit / delete |
| PATCH | `/api/violations/{id}/status` | Pending, Paid, Cancelled (+ payment ref) |
| POST | `/api/videos/analyze` | Upload video, returns `job_id` |
| GET | `/api/jobs/{id}` | Status, progress, counts, violation IDs |
| GET, PUT | `/api/fine-rules`, `/api/fine-rules/{id}` | View/edit fine amounts |
| GET | `/api/reports/summary` | Summary numbers |
| GET | `/api/reports/export?format=csv or pdf` + filters | Download report |
| GET | `/api/public/fine/{plate}` | Optional public fine lookup |

## 8. Data model

- **admins**: id, email (unique), password_hash, created_at
- **fine_rules**: id, violation_type (unique), amount, active
- **violations**: id, fine_ref (unique), plate_number, violation_type, location, occurred_at, fine_amount, status (pending/paid/cancelled), source (manual/ai), confidence, needs_review (bool), evidence_url, plate_crop_url, video_job_id (nullable), notes, paid_at, payment_ref, created_at, updated_at
- **video_jobs**: id, filename, status, progress, total_frames, vehicles_detected, violations_found, error, created_at, finished_at
- **status_log**: id, violation_id, old_status, new_status, changed_at

## 9. Performance and reliability requirements

These matter most because the free Render tier is small (512 MB RAM, sleeps after inactivity).

- Use `yolov8n` only (nano). CPU-only PyTorch wheels. `opencv-python-headless`. Load all models ONCE at startup, never per request.
- Process every 3rd frame, and resize frames so the longest side is 960 px or less. Hard cap on video length and size as in F7.
- Process one job at a time (simple in-process queue). Return a clear "busy" message if another job is running.
- Write the uploaded video to a temp file, delete it after processing. Free memory (`gc.collect()`) between jobs.
- Wrap each frame's processing in try/except so one bad frame never kills a job. On job failure set status=failed with a readable error.
- Persist jobs and violations in the DB so a restart never loses results. Jobs stuck in "processing" on startup are marked failed.
- If RAM is exceeded on the free tier, document in the README that Render Starter (2 GB) is recommended, and keep the code unchanged.
- Frontend shows loading, empty, and error states everywhere. The API client retries once, and shows a "server is waking up" message on first-request delay (Render cold start).
- CORS: allow only the Vercel domain (env `FRONTEND_ORIGIN`) plus localhost in dev.
- Never commit secrets or weights. Provide `.env.example`. Weights are downloaded in the Docker build.
- Provide `/backend/scripts/seed_demo.py` that inserts ~15 realistic demo violations (with placeholder evidence images) so the dashboard looks populated for the demo even if AI is not perfect.

## 10. Build plan (2 hours)

**Phase 1 (0:00 to 0:40): basic site**
1. Scaffold monorepo, FastAPI app, SQLAlchemy models, auto table creation, admin seeding, JWT auth.
2. Violations CRUD, status endpoint, dashboard stats, fine rules.
3. Frontend: home page, login, dashboard, manual entry form, fine table with filters.
4. Commit and tag `phase-1-working`.

**Phase 2 (0:40 to 1:40): AI pipeline**
1. Model loader service with the weights in Section 6 (test downloads first).
2. Video analyze endpoint + background job + job polling UI.
3. Detection, tracking, helmet logic, plate OCR, dedup per track.
4. Evidence saving via `StorageService`, auto fine creation.
5. History filters, CSV and PDF reports.
6. Test on 2 or 3 short sample motorcycle videos and fix obvious failures.

**Phase 3 (1:40 to 2:00): deploy and harden**
1. Backend `Dockerfile` and `render.yaml`.
2. Frontend `vercel.json` (SPA rewrite) and `VITE_API_URL`.
3. README, `.env.example`, seed script, final smoke test against the deployed URLs.

## 11. Deployment spec

**Backend (Render, Docker web service)**
- Root dir `/backend`. Base image `python:3.11-slim`. Install `libgl1`, `libglib2.0-0`. Install `torch` and `torchvision` from the CPU index (`https://download.pytorch.org/whl/cpu`) BEFORE the other requirements.
- Dockerfile pre-downloads: yolov8n weights, helmet weights, plate weights, EasyOCR English models.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Health check path `/api/health`.
- Env vars: `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `FRONTEND_ORIGIN`, `STORAGE_BACKEND` (local|cloudinary|supabase), storage credentials, `HELMET_MODEL_PATH`, `PLATE_MODEL_PATH`, `FRAME_STRIDE=3`, `MAX_VIDEO_MB=50`, `MAX_VIDEO_SECONDS=90`.
- Include a `render.yaml` blueprint.

**Frontend (Vercel)**
- Root dir `/frontend`. Env var `VITE_API_URL` pointing to the Render URL. `vercel.json` rewrites all routes to `index.html`.

Do NOT run any ML on Vercel. It only hosts the static frontend.

## 12. Acceptance criteria

- [ ] Home page loads, is responsive, and has a working Admin Login link.
- [ ] Admin can log in, see the dashboard, add a manual violation, and see it in the fine table.
- [ ] Admin can mark a fine Paid or Cancelled, and the change appears in the table, dashboard counts, and status log.
- [ ] Uploading a valid sample video returns a job ID and the UI shows live progress.
- [ ] At least one helmetless rider in a sample video produces exactly one violation with an annotated evidence image, a plate reading (or UNREADABLE + needs review), and an auto-generated fine.
- [ ] Vehicle count is shown per job.
- [ ] History page filters work. CSV and PDF exports download and open correctly.
- [ ] Oversized or wrong-format uploads are rejected with a clear message.
- [ ] A server restart does not lose data.
- [ ] The backend deploys on Render and the frontend on Vercel using only the documented env vars and README steps.

## 13. Deliverables

Monorepo source, `README.md` (local setup, deploy steps, env vars, known limitations), `.env.example` for both apps, `Dockerfile`, `render.yaml`, `vercel.json`, seed script, and a short list of sample test videos to try (search for free dashcam or traffic clips of motorcycles; do not commit large video files).
