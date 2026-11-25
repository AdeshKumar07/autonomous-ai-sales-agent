# Round 3 Technical Evaluation — Live Demo Guide (5–7 Minutes)

## 1. Opening Pitch (30 seconds)
Start by explaining the business goal:
- **Problem:** Inbound sales teams lose leads due to delayed responses, repetitive qualification, and manual CRM updates.
- **Solution:** An **Autonomous AI Sales Voice Agent** for **FORTIVEX AI PRIVATE LIMITED** that conducts natural voice/text conversations, grounds answers in company documents (RAG), qualifies leads, tracks sentiment, books conflict-free appointments, and generates manager summaries + analytics in PostgreSQL.

---

## 2. Live Demo Sequence (5–6 minutes)

### Step 1: Verify System Health & Architecture (30s)
- Open `http://localhost:5173` in Chrome or Edge.
- Point out the green **Online** badge in the header (calls `GET /health` via Nginx → FastAPI).
- Optional: Show `http://localhost:8001/ready` returning `{"status":"ready","database":"ok","chromadb":"ok"}`.

### Step 2: Knowledge Base (RAG) & Abstention (1 min)
- Click **Knowledge** tab in the right sidebar → show `ChromaDB Ready`, `5` documents, `42` chunks (`company_profile.md`, `products.md`, `pricing.md`, `faq.md`, `policies.md`).
- In Chat (voice or text), ask: *"What products or solution areas does Fortivex AI offer?"*
  - Point out the grounded reply and the **`products.md` / `faq.md` source badges** below the message.
- Ask an unsupported question: *"What is your refund policy?"*
  - Show that it retrieves `policies.md` and **refuses to invent** unverified policies, offering team follow-up instead.

### Step 3: Lead Qualification, Memory & Sentiment (1.5 min)
- Send (or speak): *"We run an e-commerce business and want to automate customer support and order management. Our monthly budget is ₹85,000, and we want to implement this within 30 days."*
- Switch to **Lead Profile** tab: show `requirements`, `budget`, `purchase_timeline`, `qualification_status: HOT`, and `qualification_reason` populated automatically.
- Switch to **Sentiment** tab: show `POSITIVE`/`NEUTRAL` label, confidence bar, emotional indicators, and trend.
- Optional: Send a frustrated message (*"I already explained this twice..."*) to show `FRUSTRATED` detection and empathetic tone adaptation.

### Step 4: Deterministic Appointment Booking & CRM (1.5 min)
- Open **Appointments** in the top nav:
  - Select a weekday, type (`DEMO`), and timezone → show real backend slots from `GET /api/appointments/availability`.
  - Book a slot → show the unique `FTX-...` booking reference.
- Open **CRM** in the top nav:
  - Select the lead → show contact details, qualification, sentiment, appointment history, **Activity Timeline** (`LEAD_CREATED`, `INFO_UPDATED`, `LEAD_QUALIFIED`, `APPOINTMENT_BOOKED`), and add an internal sales note.

### Step 5: Call Summary & Business Analytics (1 min)
- Open **Summary** → click **Generate Summary** → show structured requirements, questions, unresolved items, and **Recommended Next Sales Action**.
- Open **Insights** → show KPI cards (Total Leads, HOT Leads, Appointments, Booking Rate) and **Recharts** charts fed from PostgreSQL, plus `7d` / `30d` / `Custom` date filters.

---

## 3. Technical Talking Points for Evaluator Q&A
- **Gemini & RAG:** `google-genai` async SDK (`gemini-3.5-flash-lite` + `models/gemini-embedding-001`) with ChromaDB cosine similarity (`score >= 0.35`). Research-draft docs explicitly prevent hallucinated pricing/policies.
- **Voice State Machine:** Single-state (`idle | listening | processing | speaking | error`) with `continuous: false` and 250ms post-TTS delay in Continuous mode to eliminate speaker-to-mic echo loops.
- **PostgreSQL & Concurrency:** SQLAlchemy 2.1 ORM with `SELECT ... FOR UPDATE` row locking in `appointment_service.py` to prevent double-booking race conditions and duplicate bookings (`409 Conflict`).
- **Sentiment:** Stored per user message in `conversation_messages`; directional trend computed on ordinal valence (`NEGATIVE < FRUSTRATED < NEUTRAL < POSITIVE`). Kept strictly separate from lead qualification.
- **Docker:** Multi-stage React/Nginx frontend, non-root Python 3.11 FastAPI backend, internal-only Postgres 18 (`postgres_data`), and persistent `chroma_data` volume.

---

## 4. Honest Limitations to Disclose
1. CRM, summary, and analytics endpoints do not yet have JWT/OAuth RBAC (session isolation is enforced on customer appointment queries).
2. External CRM (HubSpot/Salesforce) and Google Calendar sync are future roadmap items; current CRM is PostgreSQL-backed.
3. Browser `SpeechRecognition` requires Chrome or Edge over `localhost` or `HTTPS`.
4. Sequential Gemini calls per chat turn (sentiment + booking intent + reply + extraction) add ~2–4s latency; parallelizing with `asyncio.gather` is a straightforward next optimization.

---

## 5. If Something Fails During the Demo
- **Microphone not working / noisy room:** Immediately type in the footer text input or click a welcome prompt chip—the exact same Gemini, RAG, Lead, Sentiment, and CRM pipeline runs identically.
- **Gemini 429 rate limit:** Wait 5–10 seconds and retry; note that `summary_service.py` and `sentiment_service.py` include graceful non-crashing fallbacks.
- **Containers stopped:** Run `docker compose up -d` and check `docker compose ps` + `http://localhost:8001/ready`.
