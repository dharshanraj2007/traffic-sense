# Traffic Sense — Smart Traffic Violation Detection & Fine Management System

> **UN SDG 11 Alignment:** Sustainable Cities & Communities (Target 11.2: Safe, Accessible & Sustainable Urban Transport Systems)  
> **Team:** Chitra S &bull; Linsha LJ  
> **Architecture:** Monorepo with React 19 Frontend (`/frontend`) and FastAPI AI Backend (`/backend`)

---

## 1. Product Summary

**Traffic Sense** is an automated traffic enforcement and surveillance web platform. Traffic authorities upload camera video feeds, and the backend:
1. Detects and tracks vehicles (motorcycles, cars, buses, trucks, pedestrians) using **Ultralytics YOLOv8** and **ByteTrack**.
2. Identifies motorcycle riders operating without safety helmets across temporal frames.
3. Performs license plate localization and **EasyOCR** text extraction with Indian plate heuristics (`^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$`).
4. Automatically generates e-challans with reference identifiers (e.g. `FN-YYYYMMDD-XXXX`), calculates fines, and archives encrypted photographic evidence.
5. Provides an administrative control center with fine management, status reconciliation (Pending &rarr; Paid / Cancelled), and exportable PDF/CSV enforcement dossiers.
6. Offers a public citizen portal for looking up fines by license plate number and simulated online fee settlement.

---

## 2. Monorepo Architecture

```
traffic-sense/
├── backend/
│   ├── app/
│   │   ├── routes/             # API Endpoints (auth, dashboard, violations, videos, rules, reports, public)
│   │   ├── services/           # AI Pipeline (detector.py), Storage (storage.py), Reports (reports.py)
│   │   ├── auth.py             # JWT generation, verification, and bcrypt hashing
│   │   ├── config.py           # Environment variables & directory resolution
│   │   ├── database.py         # SQLAlchemy engine & session lifecycle
│   │   ├── models.py           # Database ORM models (Admin, Violation, VideoJob, FineRule, StatusLog)
│   │   ├── schemas.py          # Pydantic request/response validation schemas
│   │   └── main.py             # FastAPI entrypoint, CORS, lifespan seeding, static mounts
│   ├── samples/                # Sample test videos (sample_motorcycle_traffic.mp4)
│   ├── scripts/
│   │   ├── download_models.py  # Model weights pre-loader (YOLOv8, Helmet, Plate, EasyOCR)
│   │   ├── generate_sample_video.py # Synthetic sample traffic clip generator
│   │   └── seed_demo.py        # Seeds ~15 realistic violations with simulated evidence frames
│   ├── weights/                # Local cache directory for .pt neural weights
│   ├── Dockerfile              # Production Render deployment container
│   ├── requirements.txt        # Python backend dependencies
│   └── .env.example            # Backend environment variables template
├── frontend/
│   ├── src/
│   │   ├── api/client.ts       # Axios instance with JWT interceptor & Render cold-start retry
│   │   ├── components/         # Navbar, AdminLayout sidebar & mobile drawer
│   │   ├── context/AuthContext.tsx # Admin auth state & token persistence
│   │   ├── pages/              # HomePage, CheckFinePage, LoginPage, DashboardPage,
│   │   │                       # AnalyzeVideoPage, FinesPage, ManualEntryPage, ReportsPage, SettingsPage
│   │   ├── types/index.ts      # TypeScript domain interfaces
│   │   ├── App.tsx             # React Router routing configuration
│   │   └── index.css           # Tailwind CSS v4 & custom glassmorphism styles
│   ├── vercel.json             # Vercel SPA routing rewrite
│   ├── vite.config.ts          # Vite configuration with Tailwind and dev backend proxy
│   └── package.json            # Node dependencies
├── render.yaml                 # Render blueprint for Docker web service deployment
└── README.md                   # Documentation & execution guide
```

---

## 3. Quickstart: Running Locally

### Prerequisites
- **Python 3.11+** installed
- **Node.js v18+** & **npm** installed

### Step 1: Start Backend

1. Navigate to `/backend`:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Pre-download the AI model weights and seed demo violations:
   ```bash
   python scripts/download_models.py
   python scripts/seed_demo.py
   ```
4. Start the FastAPI Uvicorn server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - API Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/api/health`

### Step 2: Start Frontend

1. In a separate terminal, navigate to `/frontend`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Launch Vite development server:
   ```bash
   npm run dev
   ```
   - Web App URL: `http://localhost:5173`

---

## 4. Default Admin Credentials

| Attribute | Default Value | Notes |
|---|---|---|
| **Email** | `admin@trafficsense.gov` | Seeded automatically on startup |
| **Password** | `Admin@123456` | Click "Auto-Fill Demo Admin Credentials" on login page |

---

## 5. Testing the AI Video Pipeline

1. Log into the Admin Portal (`/login`) using the credentials above.
2. Navigate to **Video Analysis** (`/admin/analyze`).
3. Select and upload the sample video:
   - File location: `backend/samples/sample_motorcycle_traffic.mp4`
4. The system will dispatch the job and poll live telemetry (progress percentage, vehicles tracked, and violations detected).
5. When completed, click on any detected violation to inspect the bounding boxes, helmet non-compliance confidence, and extracted plate number!

---

## 6. Environment Variables

### Backend (`/backend/.env`)
| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./traffic_sense.db` |
| `JWT_SECRET` | Secret key for JWT signing | `traffic_sense_jwt_secret_key_2026_super_secure` |
| `ADMIN_EMAIL` | Seeded default admin email | `admin@trafficsense.gov` |
| `ADMIN_PASSWORD` | Seeded default admin password | `Admin@123456` |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |
| `STORAGE_BACKEND` | Storage provider (`local` / `cloudinary` / `supabase`) | `local` |
| `FRAME_STRIDE` | Frame sampling rate | `3` |
| `MAX_VIDEO_MB` | Maximum video upload size in MB | `50` |
| `MAX_VIDEO_SECONDS` | Maximum allowed video length | `90` |

### Frontend (`/frontend/.env`)
| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | Base API URL | Empty string in local dev (uses Vite proxy) |

---

## 7. Production Deployment Guide

### Backend (Render as Docker Web Service)
1. Push repo to GitHub.
2. In Render dashboard, click **New > Blueprint** and select the repository (using `render.yaml`).
3. Or create a **Web Service** with:
   - Environment: `Docker`
   - Docker context: `./backend`
   - Dockerfile path: `./backend/Dockerfile`
   - Health check path: `/api/health`
4. Configure environment variables (`DATABASE_URL`, `JWT_SECRET`, `FRONTEND_ORIGIN`, `ADMIN_PASSWORD`).

### Frontend (Vercel)
1. In Vercel dashboard, import the repository.
2. Set Root Directory to `frontend`.
3. Set Environment Variable:
   - `VITE_API_URL`: Your deployed Render backend URL (e.g. `https://traffic-sense-api.onrender.com`).
4. Deploy! `vercel.json` will automatically route all SPA requests to `index.html`.
