# Autonomous AI Sales Voice Agent — FORTIVEX AI PRIVATE LIMITED

## 1. Project Overview
An end-to-end **Autonomous AI Sales Voice Agent** MVP built for **FORTIVEX AI PRIVATE LIMITED**. The platform conducts natural voice and text conversations, grounds company answers using ChromaDB RAG, qualifies leads in PostgreSQL, adapts to customer sentiment, books conflict-free appointments, and provides structured call summaries and business analytics.

For a concise executive summary, see [PROJECT_REPORT.md](PROJECT_REPORT.md). For the live walkthrough script, see [docs/ROUND_3_DEMO_GUIDE.md](docs/ROUND_3_DEMO_GUIDE.md).

---

## 2. Business Problem & Solution
- **Problem:** Manual inbound lead qualification is slow, inconsistent across reps, and often leaves CRM notes, follow-ups, and sentiment signals unrecorded.
- **Solution:** A voice-first AI sales assistant that qualifies leads naturally (one question at a time), retrieves verified company knowledge, detects customer frustration or opt-out, books real calendar slots without double-booking, and logs every interaction into PostgreSQL.

---

## 3. Key Features
- Browser Web Speech API **Speech-to-Text** (`en-IN`, `hi-IN`) and **Text-to-Speech** with **Push-to-talk** (default) and **Continuous** modes.
- **Google Gemini (`gemini-3.5-flash-lite`)** sales conversation, structured lead extraction, sentiment analysis, and call summarization.
- **ChromaDB RAG** over five researched Markdown documents (`backend/app/knowledge_base/`) with source attribution and abstention on unknowns.
- **Lead Qualification** (`NEW | HOT | WARM | COLD`) and persistent multi-turn **Conversation Memory** in PostgreSQL 18.
- **Sentiment Analysis** (`POSITIVE | NEUTRAL | FRUSTRATED | NEGATIVE`), tone adaptation, and directional trend tracking.
- **Deterministic Appointment Booking** with availability generation and row-locked conflict prevention.
- **PostgreSQL-Backed CRM** with lead profiles, internal notes, and chronological activity timelines.
- **Call Summaries & Business Insights Dashboard** powered by Recharts and SQLAlchemy aggregations.

---

## 4. Technology Stack
- **Frontend:** React 19, Vite 8, JavaScript, Tailwind CSS v4, Axios, React Router DOM, Lucide React, Recharts, Browser Web Speech API.
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.1, `psycopg2-binary`, `python-dotenv`, `google-genai`.
- **Databases & Vector Store:** PostgreSQL 18 (`postgres:18-alpine`), ChromaDB (`1.5.9`, `models/gemini-embedding-001`).
- **Containerization:** Docker, Docker Compose, Nginx (`nginx:1.27-alpine`).

---

## 5. System Architecture
See [docs/architecture.md](docs/architecture.md) for the step-by-step explanation and Mermaid source.

```text
  ┌─────────────────────────┐     1. Voice / Text      ┌──────────────────────────────────┐
  │    Customer Browser     │ ───────────────────────▶ │  React + Vite UI (Nginx :5173)   │
  │ (Chrome/Edge Web Speech │ ◀─────────────────────── │  Push-to-Talk / Continuous Mode  │
  │    STT + TTS Audio)     │     6. Reply + Audio     └────────────────┬─────────────────┘
  └─────────────────────────┘                                           │ 2. /api/* Proxy
                                                                        ▼
  ┌─────────────────────────┐     3. Semantic Search   ┌──────────────────────────────────┐
  │   ChromaDB (/chroma_db) │ ◀──────────────────────▶ │     FastAPI Backend (:8001)      │
  │  5 Docs / 42 KB Chunks  │    (Grounded Context)    │  • Sentiment & Booking Intent    │
  └────────────┬────────────┘                          │  • Lead Extraction & Memory      │
               │                                       │  • Appointment Row-Locking       │
               │ Embeddings                            └────────┬───────────────┬─────────┘
               ▼                                                │ 4. AI Calls   │ 5. Persist
  ┌─────────────────────────┐                                   ▼               ▼
  │    Google Gemini API    │ ◀─────────────────────────────────┘   ┌─────────────────────┐
  │ gemini-3.5-flash-lite   │                                       │  PostgreSQL 18 (db) │
  │ gemini-embedding-001    │                                       │ Leads, Msgs, Appts, │
  └─────────────────────────┘                                       │ CRM, Summaries      │
                                                                    └─────────────────────┘
```

---

## 6. End-to-End Business Workflow Example
*(Illustrative test scenario, not an official FORTIVEX price quotation or business policy.)*

A prospective customer says:
> *"We run an e-commerce business and want to automate customer support and order management. Our monthly budget is ₹85,000, and we want to implement this within 30 days."*

1. **Understand Requirement:** Gemini identifies the e-commerce automation use case and checks saved session context.
2. **RAG Retrieval:** ChromaDB searches `products.md`, `company_profile.md`, and `pricing.md` (`score >= 0.35`) so the agent describes publicly listed capabilities without inventing unverified prices.
3. **Follow-Up Question:** The agent asks at most one missing detail (e.g., customer name or preferred demo date).
4. **Extract & Store Lead:** `gemini_service.extract_lead_updates()` extracts `business_type`, `requirements`, `budget`, and `purchase_timeline` into `leads` without overwriting unmentioned fields.
5. **Lead Qualification:** `lead_service._resolve_consistent_status()` classifies the lead as `HOT` (clear requirements + near-term 30-day timeline + high intent) with a `qualification_reason`.
6. **Sentiment Analysis:** `sentiment_service.py` classifies the turn (`POSITIVE` / `NEUTRAL`) and stores confidence, indicators, and strategy on the user `ConversationMessage` row.
7. **Persist History:** User and assistant messages are saved in `conversation_messages`.
8. **Offer Availability & Book:** If the customer requests a demo, `appointment_service.py` queries `GET /api/appointments/availability`, presents real slots, and upon confirmation creates a `CONFIRMED` `Appointment` (`FTX-...`) inside a `SELECT ... FOR UPDATE` transaction.
9. **Update CRM & Summary:** `crm_activities` logs `LEAD_CREATED`, `INFO_UPDATED`, `LEAD_QUALIFIED`, and `APPOINTMENT_BOOKED`; `POST /api/summaries/{session_id}/generate` creates a structured `ConversationSummary`, and `/api/analytics/*` reflects the updated metrics.

---

## 7. AI and RAG Implementation
- **Chat & Extraction:** `google-genai` async client (`gemini-3.5-flash-lite`) with Pydantic `response_schema` for structured JSON extraction and 1 controlled retry on invalid JSON.
- **Knowledge Base:** Five researched Markdown files in `backend/app/knowledge_base/` (`company_profile.md`, `products.md`, `pricing.md`, `faq.md`, `policies.md`; `README.md` is excluded from ingestion).
- **Chunking & Embeddings:** `500`-character chunks with `80`-character overlap, SHA-256 `content_hash` deduplication, metadata (`source_filename`, `document_type`, `chunk_index`, `ingestion_timestamp`), embedded with `models/gemini-embedding-001` into ChromaDB (`fortivex_research_kb`).

---

## 8. Lead Qualification & Sentiment Analysis
- **Lead Qualification (`NEW | HOT | WARM | COLD`):** Evaluated from buying intent, requirements, and purchase timeline (never budget alone).
- **Sentiment Analysis (`POSITIVE | NEUTRAL | FRUSTRATED | NEGATIVE`):** Supports English and Hindi; adapts response tone (e.g., apologizing and offering human help for `FRUSTRATED`, respecting opt-out for `NEGATIVE`).
- **Separation of Concerns:** Sentiment does not automatically determine lead qualification. Trend is computed over analyzed user turns using ordinal valence (`NEGATIVE < FRUSTRATED < NEUTRAL < POSITIVE`) → `improving | stable | declining | insufficient_data`.

---

## 9. Appointment Booking
- **Configurable MVP Defaults** *(development defaults, not official FORTIVEX policies)*:
  - Monday–Friday, `09:00`–`18:00` (`BOOKING_OPEN_HOUR`, `BOOKING_CLOSE_HOUR`)
  - `30`-minute slots (`BOOKING_SLOT_MINUTES`), `15`-minute buffer (`BOOKING_BUFFER_MINUTES`)
  - `60`-minute minimum advance notice (`BOOKING_MIN_ADVANCE_MINUTES`), `30`-day max horizon (`BOOKING_MAX_DAYS_AHEAD`)
  - Default timezone `UTC` (`BOOKING_DEFAULT_TIMEZONE`) — never assumes India without customer input.
- **Concurrency Safety:** `create_appointment()` and `reschedule_appointment()` lock the `Lead` row and overlapping active `Appointment` rows using `SELECT ... FOR UPDATE`, rejecting conflicts/duplicates with `409 Conflict` and past/invalid dates with `400 Bad Request`.

---

## 10. CRM Functionality
- Built on PostgreSQL (`leads`, `appointments`, `crm_activities`) — **external HubSpot/Salesforce integrations are not implemented in this MVP**.
- Tracks lead profile, qualification, sentiment summary, appointment history, internal sales notes, `next_follow_up`, and `CRMActivity` events (`LEAD_CREATED`, `INFO_UPDATED`, `LEAD_QUALIFIED`, `APPOINTMENT_REQUESTED`, `APPOINTMENT_BOOKED`, `APPOINTMENT_RESCHEDULED`, `APPOINTMENT_CANCELLED`, `NOTE_ADDED`).

---

## 11. Conversation Summaries & Business Analytics
- **Summaries (`conversation_summaries`):** Combines PostgreSQL lead/sentiment/appointment facts with Gemini narrative extraction (`summary_version`, `is_conversation_completed`, `recommended_next_action`) and includes a deterministic fallback if Gemini is rate-limited.
- **Booking Rate Formula:**
  $$\text{Appointment Booking Rate (\%)} = \frac{\text{Distinct leads with } \ge 1 \text{ CONFIRMED or COMPLETED appointment in period}}{\text{Total leads in period}} \times 100$$
  Returns `0.0` when `total_leads == 0`.
- **Date Filters:** `today`, `7d`, `30d`, `90d`, `custom` (`start_date`..`end_date`), and `all` using UTC boundaries.

---

## 12. Database Schema & Relationships
- `Lead` (`leads`) 1 ──▶ N `ConversationMessage` (`conversation_messages`, FK `session_id`)
- `Lead` (`leads`) 1 ──▶ N `Appointment` (`appointments`, FK `lead_id`)
- `Lead` (`leads`) 1 ──▶ N `CRMActivity` (`crm_activities`, FK `lead_id`)
- `Lead` (`leads`) 1 ──▶ 1 `ConversationSummary` (`conversation_summaries`, FK `lead_id` & `session_id`)

---

## 13. API Endpoints
- **Health & Readiness:** `GET /health`, `GET /ready`
- **Agent & Session:** `POST /api/agent/chat`, `GET /api/agent/session/{session_id}`
- **Leads:** `GET /api/leads`, `GET /api/leads/{lead_id}`
- **Knowledge Base (RAG):** `POST /api/knowledge/ingest`, `POST /api/knowledge/search`, `GET /api/knowledge/documents`, `GET /api/knowledge/status`
- **Appointments:** `GET /api/appointments/availability`, `POST /api/appointments`, `GET /api/appointments`, `GET /api/appointments/{appointment_id}`, `PATCH /api/appointments/{appointment_id}/cancel`, `PATCH /api/appointments/{appointment_id}/reschedule`
- **CRM:** `GET /api/crm/leads`, `GET /api/crm/leads/{lead_id}`, `GET /api/crm/leads/{lead_id}/appointments`, `POST /api/crm/leads/{lead_id}/notes`
- **Summaries:** `POST /api/summaries/{session_id}/generate`, `GET /api/summaries/{session_id}`, `GET /api/summaries`
- **Analytics:** `GET /api/analytics/overview`, `GET /api/analytics/leads`, `GET /api/analytics/sentiment`, `GET /api/analytics/appointments`, `GET /api/analytics/sales-insights`

---

## 14. Docker Deployment Architecture
- **`frontend` (`nginx:1.27-alpine`, host port `5173:80`):** Serves the Vite production build with SPA fallback and proxies `/api/`, `/health`, and `/ready` to `http://backend:8001`.
- **`backend` (`python:3.11-slim`, host port `8001:8001`):** Runs Uvicorn (1 worker, non-root `appuser`), waits for `db` health, and persists ChromaDB in `chroma_data:/app/chroma_db`.
- **`db` (`postgres:18-alpine`, internal-only):** Runs PostgreSQL 18 on the internal Compose network (no host port `5432` exposed) with persistent volume `postgres_data:/var/lib/postgresql`.

```powershell
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```
> **Warning:** Never run `docker compose down -v` casually — `-v` permanently deletes `postgres_data` and `chroma_data`.

---

## 15. Local Setup Instructions (Without Docker)
1. **Backend:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8001
   ```
2. **Frontend:**
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in Chrome or Edge. Vite proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8001`.

---

## 16. Environment Variables
- `backend/.env` is loaded by `python-dotenv` for local dev and passed to the `backend` container via `env_file:` in `docker-compose.yml`.
- **Local vs. Docker:** Local dev uses `DATABASE_URL` pointing to `localhost:5432` and `CHROMA_PERSIST_DIR=./chroma_db`; Docker Compose overrides `DATABASE_URL` to `@db:5432/` and `CHROMA_PERSIST_DIR=/app/chroma_db`.
- Required: `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `DATABASE_URL`. See `.env.example` and `backend/.env.example` (placeholders only).

---

## 17. Testing & Verification Instructions
- **Frontend:** `cd frontend; npm run lint; npm run build`
- **Container & Health Checks:** `docker compose ps`, `GET http://localhost:8001/health`, `GET http://localhost:8001/ready`
- **API Smoke Checks:** Test `/api/knowledge/status`, `/api/knowledge/search`, `/api/agent/chat`, `/api/appointments/availability`, `/api/crm/leads`, `/api/summaries/{session_id}/generate`, and `/api/analytics/overview`.

### Technical Evaluation Demo
*(Demonstrate only features verified in the current build.)*
1. Open `http://localhost:5173` and verify the green **Online** status badge.
2. Interact via microphone (Chrome/Edge) or text input; ask about Fortivex AI capabilities and verify RAG source badges (`products.md`, `faq.md`).
3. Provide e-commerce requirements, ₹85,000 budget, and 30-day timeline; inspect **Lead Profile** (`HOT`) and **Sentiment** tab.
4. Refresh the page to verify PostgreSQL session restoration.
5. Open **Appointments** to view real slots and book a demo; open **CRM** to inspect the activity timeline and add a note.
6. Open **Summary** to generate a structured summary, then open **Insights** to show Recharts analytics.

---

## 18. Known Limitations
- **MVP Auth:** CRM, summary, and analytics endpoints do not yet implement JWT/OAuth RBAC (session isolation is enforced on customer appointment queries).
- **External Integrations:** HubSpot, Salesforce, and Google Calendar are not connected.
- **Voice Browser Support:** Web Speech API `SpeechRecognition` requires Chrome or Edge.
- **Chat Latency:** Multiple sequential Gemini calls per turn (sentiment + booking intent + reply + lead extraction) add ~2–4s latency.

---

## 19. Security Considerations
- Secrets remain in `.env` (Git-ignored); `AppointmentPublicSchema` omits `internal_notes`; SQLAlchemy uses parameterized queries; `validate_startup_config()` fails fast on missing `GEMINI_API_KEY` or `DATABASE_URL`.
- **Pre-Git Hygiene:** Move any literal `POSTGRES_PASSWORD` in `docker-compose.yml` into root `.env` (`${POSTGRES_PASSWORD}`) before pushing to a remote repository.

---

## 20. Scalability Strategy (Proposed — Not Yet Implemented)
- Distinguish **100,000 registered users** from **100,000 simultaneous voice sessions**.
- Proposed path: horizontal React/CDN tier, stateless FastAPI replicas behind a load balancer + API Gateway rate limiting, managed PostgreSQL + read replicas, Redis for session/rate-limit coordination, Celery/ARQ workers for async summarization/ingestion, S3/GCS object storage, and OpenTelemetry/Prometheus/Grafana observability.

---

## 21. Future Roadmap
1. Parallelize per-turn Gemini calls (`asyncio.gather`) to reduce voice response latency.
2. Add JWT/OAuth2 RBAC for CRM, summary, and analytics endpoints.
3. Connect HubSpot/Salesforce webhooks and Google Calendar OAuth sync.
4. Externalize `POSTGRES_PASSWORD` from `docker-compose.yml` to `.env` for production deployments.
