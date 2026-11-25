# Autonomous AI Sales Voice Agent — FORTIVEX AI PRIVATE LIMITED

An end-to-end AI-powered sales voice agent platform built with **React + Vite + Tailwind CSS v4**, **FastAPI + SQLAlchemy + PostgreSQL**, **Google Gemini (`google-genai`)**, **ChromaDB RAG**, **Sentiment Analysis**, and **Appointment Booking + CRM**.

---

## Architecture Overview

### 1. Voice & Chat Pipeline
- **Speech-to-Text / Text-to-Speech:** Browser Web Speech API (`SpeechRecognition` + `speechSynthesis`) with a deterministic voice state machine (`idle | listening | processing | speaking | error`) supporting **Push-to-talk** (default) and **Continuous** modes.
- **RAG Knowledge Retrieval:** ChromaDB (`backend/chroma_db`, `models/gemini-embedding-001`) indexes the five researched Markdown documents in `backend/app/knowledge_base/`.
- **Sentiment Analysis:** Analyzes each customer message (`POSITIVE | NEUTRAL | FRUSTRATED | NEGATIVE`), adapts the agent's tone, and tracks session sentiment trends (`improving | stable | declining | insufficient_data`).

### 2. Appointment Booking & Availability Architecture
- **Deterministic Backend Scheduling:** Gemini extracts booking intent (`appointment_intent_service.py`), while `appointment_service.py` computes real availability, validates business rules, and executes bookings inside PostgreSQL transactions with row-level `SELECT ... FOR UPDATE` locking.
- **MVP Booking Defaults (Configurable, NOT official FORTIVEX policy):**
  - Working days: Monday–Friday
  - Working hours: `09:00` – `18:00` (configurable via `BOOKING_OPEN_HOUR` / `BOOKING_CLOSE_HOUR`)
  - Slot duration: `30` minutes (`BOOKING_SLOT_MINUTES`)
  - Buffer between meetings: `15` minutes (`BOOKING_BUFFER_MINUTES`)
  - Minimum advance notice: `60` minutes (`BOOKING_MIN_ADVANCE_MINUTES`)
  - Maximum booking horizon: `30` days (`BOOKING_MAX_DAYS_AHEAD`)
  - Default timezone: `UTC` (`BOOKING_DEFAULT_TIMEZONE`)

### 3. CRM Architecture (PostgreSQL MVP vs. External CRM Roadmap)
- **Current MVP:** Built directly on PostgreSQL (`leads`, `conversation_messages`, `appointments`, `crm_activities`) with lead qualification (`NEW | HOT | WARM | COLD`), internal sales notes, and a chronological activity timeline (`LEAD_CREATED`, `INFO_UPDATED`, `LEAD_QUALIFIED`, `APPOINTMENT_REQUESTED`, `APPOINTMENT_BOOKED`, `APPOINTMENT_RESCHEDULED`, `APPOINTMENT_CANCELLED`, `NOTE_ADDED`).
- **External CRM Roadmap:** The `crm_service.py` and `CRMActivity` model are structured so outbound webhooks/adapters for **HubSpot** or **Salesforce** can be added later without altering the chat or voice UI. *(External HubSpot/Salesforce integrations are not implemented in this MVP.)*

---

## Database Relationships

- `Lead (1)` ──▶ `(N) ConversationMessage` (`leads.session_id` → `conversation_messages.session_id`)
- `Lead (1)` ──▶ `(N) Appointment` (`leads.id` → `appointments.lead_id`)
- `Lead (1)` ──▶ `(N) CRMActivity` (`leads.id` → `crm_activities.lead_id`)

---

## API Endpoints

- **Health:** `GET /health`
- **Agent & Session:**
  - `POST /api/agent/chat`
  - `GET /api/agent/session/{session_id}`
- **Knowledge Base (RAG):**
  - `POST /api/knowledge/ingest`
  - `POST /api/knowledge/search`
  - `GET /api/knowledge/documents`
  - `GET /api/knowledge/status`
- **Appointments:**
  - `GET /api/appointments/availability?date=YYYY-MM-DD&appointment_type=DEMO&timezone=UTC`
  - `POST /api/appointments`
  - `GET /api/appointments` (filters: `status`, `date`, `lead_id`, `session_id`)
  - `GET /api/appointments/{appointment_id}`
  - `PATCH /api/appointments/{appointment_id}/cancel`
  - `PATCH /api/appointments/{appointment_id}/reschedule`
- **CRM:**
  - `GET /api/crm/leads`
  - `GET /api/crm/leads/{lead_id}`
  - `GET /api/crm/leads/{lead_id}/appointments`
  - `POST /api/crm/leads/{lead_id}/notes`

---

## Environment Variables (`backend/.env`)

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

Optional overrides: `GEMINI_EMBEDDING_MODEL`, `RAG_ADMIN_TOKEN`, `BOOKING_DEFAULT_TIMEZONE`, `BOOKING_OPEN_HOUR`, `BOOKING_CLOSE_HOUR`, `BOOKING_SLOT_MINUTES`, `BOOKING_BUFFER_MINUTES`.

---

## Local Setup & Running

### Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in Chrome or Edge.

---

## Known MVP Limitations

- **Authorization:** Customer-facing appointment endpoints support `session_id` isolation checks, while CRM dashboard endpoints are unauthenticated for local MVP demonstration. Production deployment requires user/role authentication (e.g., JWT/OAuth).
- **External Calendar & CRM Sync:** Appointments and CRM records are persisted in PostgreSQL; Google Calendar, HubSpot, and Salesforce sync are not yet connected.
- **Browser Voice Support:** Web Speech API (`SpeechRecognition`) requires Chrome or Edge.
