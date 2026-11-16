# VisualIQ — Intelligent Surveillance Transcript & RAG Intelligence Platform

VisualIQ is an AI-powered CCTV intelligence platform that analyzes video, generates searchable incident transcripts, and answers natural-language questions with timestamped insights.

[![Version](https://img.shields.io/badge/version-2.0.0-0fa37f.svg)](https://github.com/saikumar/visualiq)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/VLM-Gemini%202.5%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq%20Fallback-Llama%204%20Scout-F55036.svg)](https://groq.com)
[![Compliance](https://img.shields.io/badge/DPDP%20Act%202023-Compliant-10b981.svg)](#privacy--compliance)

> **Enterprise V2.0 Implementation**  
> **Team Lead:** Saikumar (Backend + DevOps + E2E)  
> **Frontend:** Yashwanth (React 19 + TypeScript + Vite)  
> **LLM / AI Pipeline:** Varun (Gemini 2.5 Flash + Groq Llama 4 + ChromaDB)  
> **Database & Storage:** Prem (Supabase PostgreSQL + Vector Store + RLS)  

---

## 01. Executive Overview

**VisualIQ** is a pure software-as-a-service (SaaS) AI surveillance intelligence platform. It interfaces with pre-installed CCTV cameras (Hikvision, Dahua, CP Plus, RTSP feeds) in residential gated communities and commercial facilities.

Instead of requiring human security guards to watch 1,440 minutes of video per camera daily:
1. **VisualIQ extracts keyframes** using uniform sampling (1 frame per 5 seconds, `fps=0.2`) combined with **dynamic motion-burst frame detection**.
2. **Analyzes frames with Vision AI (Gemini 2.5 Flash)** passing **temporal context** (history of recent frames) to accurately detect loitering, perimeter breaches, and anomalies without facial identification (strict DPDP Act 2023 compliance).
3. **Synthesizes timestamped narrative surveillance logs** covering morning, afternoon, and night shifts.
4. **Indexes logs in vector embeddings (ChromaDB & Supabase RPC)**.
5. **Provides natural language RAG intelligence** enabling managers and residents to ask questions in plain English (*"Were there any strangers or unusual activities last night?"*) and receive accurate answers with timestamp citations in under 3 seconds.

---

## 02. Architecture & Pipeline Diagram

```
                             VisualIQ V2.0 System Architecture
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                            CLIENT LAYER (React 19 + TypeScript)                │
  │     [Dashboard & Timeline]     [Footage Ingest]     [RAG Intelligence Q&A]      │
  │     - Anomaly Alert Panel      - Drag & Drop MP4    - Plain English Queries     │
  │     - Camera Filter Selector   - Pipeline Stepper   - Timestamp Citations       │
  └────────────────────────┬──────────────────────────────────┬─────────────────────┘
                           │ Axios + Bearer JWT               │
                           ▼                                  ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                           API GATEWAY (FastAPI / main.py)                       │
  │       CORS Middleware  ·  Global Exception Handler  ·  JWT Authentication       │
  │       /api/upload      /api/job/{id}     /api/transcripts (camera_id filter)    │
  │       /api/query       /api/alerts       /api/cameras         /api/digest       │
  └───────────┬─────────────────────────────────┬──────────────────────┬────────────┘
              │                                 │                      │
     ┌────────▼────────┐               ┌────────▼────────┐    ┌────────▼────────┐
     │   Redis Store   │               │ Ingestion Engine│    │  RAG Engine     │
     │   Job Lifecycle │               │ (ingestion.py)  │    │  (rag.py)       │
     │   - pending     │               │                 │    │                 │
     │   - extracting  │◄──────────────┤ 1. Uniform fps  │    │ 1. ChromaDB Top5│
     │   - analyzing   │  Status       │ 2. Motion-Burst │    │ 2. Context Build│
     │   - synthesizing│  Updates      │ 3. Temporal Ctx │    │ 3. Multi-Model  │
     │   - done        │               └────────┬────────┘    │    Cascade      │
     └─────────────────┘                        │             └────────┬────────┘
                                                ▼                      │
  ┌────────────────────────────────────────────────────────────────────▼────────────┐
  │                         MULTI-PROVIDER AI RESILIENCE LAYER                      │
  │                                                                                 │
  │  Layer 1 (Primary)    : Google Gemini 2.5 Flash API (30% higher vision precision)│
  │  Layer 2 (Secondary)  : Groq Llama 4 Scout / Llama 3.2 Vision (Unblocked cascade)│
  │  Layer 3 (Local GPU)  : Ollama Qwen3-VL 8B (Zero-cost offline fallback)         │
  │  Layer 4 (Heuristic)  : Deterministic non-LLM synthesis (100% demo uptime)     │
  └─────────────────────────────────────┬───────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                               PERSISTENCE DOMAIN                                │
  │                                                                                 │
  │  Supabase (PostgreSQL 16)              ChromaDB / Supabase RPC                  │
  │  - cameras     (id, name, status)      - visualiq_transcripts collection        │
  │  - events      (temporal frame logs)   - Cosine similarity vector search        │
  │  - transcripts (narrative shift logs)  - Dimensionality validation (384/768)   │
  │  - alerts      (auto-created score>6)  - In-memory vector fallback              │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 03. Resolution of Critical Gaps & 2026 Upgrades

| # | Severity | Component | Issue Identified | Exact V2.0 Fix Implemented |
|---|----------|-----------|------------------|----------------------------|
| **1** | **CRITICAL** | `backend/services/rag.py` | Query fallback short-circuited when Gemini was absent; Groq path was unreachable | **Unblocked cascade:** Removed early return; queries cascade: Gemini 2.5 Flash → Groq Llama 4 Scout → Ollama → Deterministic Transcript Synthesis. |
| **2** | **CRITICAL** | `backend/services/ingestion.py` | Mock Redis returned `None`, leaving `/api/job/{id}` permanently stuck in `pending` | **Real Redis + In-Memory Fallback:** Connected real Redis client via `REDIS_URL` with `.ping()` verification, paired with a thread-safe in-memory store fallback. |
| **3** | **HIGH** | `backend/routers/transcripts.py` | Transcript list endpoint ignored `camera_id` param sent by frontend | **Param Passed & Filtered:** Added `camera_id: Optional[str] = Query(None)` to transcript endpoint and routed through Supabase/local queries. |
| **4** | **MEDIUM** | `README.md` | Stale documentation with obsolete models and legacy ChromaDB paths | **Comprehensively updated** with 2026 model stack, RTSP stream manager, and live setup procedures. |

### Architectural Upgrades (Phase 2 & 3)
1. **2026 Model Upgrades:**
   - Primary: `gemini-2.5-flash`
   - Vision Fallback: `meta-llama/llama-4-scout-17b-16e-instruct` / `llama-3.2-11b-vision-preview`
   - Text Fallback: `meta-llama/llama-4-scout-17b-16e-instruct` / `llama-3.1-8b-instant`
   - Local Dev: `qwen3-vl:8b` via Ollama
2. **Temporal Frame Context (`analyzer.py`):**
   - Each frame analysis now receives the previous 3 events as context. This enables accurate detection of **loitering (>5 min)**, escalating altercations, and activity continuity.
3. **Motion-Burst Frame Extraction (`ingestion.py`):**
   - Combines uniform sampling (1 frame per 5 seconds) with OpenCV pixel difference analysis (`MOTION_THRESHOLD=0.08`, `MAX_BURST_FRAMES=5`) to capture sudden, rapid events that occur between standard sample intervals.
4. **Live RTSP Stream Manager (`stream_manager.py`):**
   - Real-time stream worker with circular event buffer (100 items), reconnect tracking, and health metrics.

---

## 04. API Endpoint Reference

| Method | Endpoint | Description | Request / Query | Response |
|--------|----------|-------------|-----------------|----------|
| `POST` | `/api/upload` | Upload MP4/AVI and start extraction & VLM pipeline | `multipart/form-data` (`file`, `camera_id`) | `{ job_id, status: "pending" }` |
| `GET` | `/api/job/{job_id}` | Poll real-time pipeline status | Path `job_id` | `JobStatus` (`extracting`/`analyzing`/`done`) |
| `GET` | `/api/transcripts` | Retrieve transcripts (supports camera filter) | `?camera_id=cam_gate_01&limit=50` | `List[Transcript]` |
| `GET` | `/api/transcripts/{id}` | Retrieve single transcript with all events | Path `id` | `Transcript` with event details |
| `GET` | `/api/events` | Retrieve raw frame analysis events | `?camera_id=cam_gate_01` | `List[FrameEvent]` |
| `POST` | `/api/query` | Natural language RAG query | `{ question: string, camera_id?: string }` | `{ answer, sources, provider, latency_ms }` |
| `GET` | `/api/alerts` | List security anomalies (score > 6) | `?camera_id=...&resolved=false` | `List[Alert]` |
| `POST` | `/api/alerts/{id}/resolve`| Mark anomaly alert as resolved | Path `id` | `{ status: "ok" }` |
| `GET` | `/api/cameras` | List all monitored CCTV cameras | None | `List[Camera]` |
| `POST` | `/api/digest` | Generate daily executive security digest | `?date_str=2026-10-01` | `DigestResponse` (paragraph summary) |
| `GET` | `/health` | Diagnostic health & model status | None | `{ status: "ok", models: {...} }` |

---

## 05. Quick Start & Execution Guide

### Option A: Running with Docker Compose (Recommended for Production)

```bash
# 1. Clone repository
git clone https://github.com/saikumar/visualiq.git
cd visualiq

# 2. Configure environment
cp .env.example .env
# Edit .env and supply GEMINI_API_KEY (or use MOCK_MODE=true)

# 3. Launch stack (Backend, Redis, ChromaDB)
docker-compose up --build
```

The services will be available at:
- Backend API & Swagger: `http://localhost:8000/docs`
- ChromaDB: `http://localhost:8001`
- Redis: `localhost:6379`

### Option B: Running Locally (Development Mode)

#### 1. Backend Setup:
```bash
# From repository root
py -3.12 -m pip install -r backend/requirements.txt

# Run backend (with auto-reload and automatic demo data seeding)
py -3.12 backend/main.py
```
*Backend runs on `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.*

#### 2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 06. 5-Minute Client Demo Script (Apartment Society Committee)

- **Minute 1 — The Problem:**
  > *"Sir, your gate camera records 24 hours every day. That is 1,440 minutes of footage. Nobody has time to watch it. If something unusual happened last night, how would you know?"*
- **Minute 2 — The Solution:**
  > *"We plug directly into your existing cameras with zero new hardware. Just grant access to your DVR network. Watch what happens."*
  - Open `http://localhost:5173/upload` → Select Gate Camera → Upload footage → Watch live extraction and Gemini 2.5 Flash analysis progress in real time.
- **Minute 3 — The Transcript & Alerts:**
  - Transition to `http://localhost:5173/` (Dashboard).
  - Show the vertical chronological timeline: every delivery, resident entry, and vehicle move.
  - Point to the **Red Anomaly Alert**: *"At 23:30, our AI detected a person loitering near visitor parking for 8 minutes after food delivery departure, peering into parked vehicles (Threat Score: 8/10)."*
- **Minute 4 — Natural Language Intelligence Query:**
  - Click **Intelligence Q&A** (`/query`).
  - Ask: *"Were there any strangers or unusual activities last night?"*
  - Show the answer appear in under 3 seconds with exact timestamp citations (`23:30`, `02:15 AM`).
- **Minute 5 — The Daily Digest & Close:**
  - Return to Dashboard and click **"Generate Today Summary"**.
  - Show the cohesive executive paragraph ready for the society WhatsApp group or committee report.
  - Close with: *"We want to deploy this in your society for 2 weeks free of charge. Can we connect your DVR feed this week?"*

---

## 07. Privacy & DPDP Act 2023 Compliance

1. **Zero Biometric / Face Storage:** Facial embeddings are strictly suppressed (`faces_visible: false`). Only factual behavioral descriptions are retained.
2. **Ephemeral Frame Retention:** Video frames are processed in-memory / temporary directories and automatically unlinked after transcript synthesis.
3. **Row-Level Security (RLS):** Supabase PostgreSQL tables enforce tenant-level isolation for all stored transcripts and camera metadata.
