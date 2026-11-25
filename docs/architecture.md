# System Architecture & Flow — Autonomous AI Sales Voice Agent

This diagram reflects the **actual implemented MVP architecture** verified against `docker-compose.yml`, `frontend/nginx.conf`, and `backend/app/`.

## Easy-to-Explain Visual Flow (Steps 1 → 6)

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

### How to Explain Each Step in 30 Seconds
1. **Capture:** Customer speaks (Web Speech STT) or types in the React UI.
2. **Proxy:** Nginx forwards `/api/*` requests to FastAPI (`backend:8001`).
3. **Ground (RAG):** FastAPI queries ChromaDB for relevant company docs (`score >= 0.35`).
4. **Reason (Gemini):** Gemini analyzes sentiment, detects booking intent, generates a grounded reply, and extracts structured lead fields.
5. **Persist (PostgreSQL 18):** FastAPI saves messages, sentiment, lead status (`HOT/WARM/COLD/NEW`), row-locked appointments, CRM activities, and summaries.
6. **Respond:** React updates the chat, Lead/Sentiment/CRM panels, and speaks the reply via Browser TTS.

---

## Mermaid Diagram (for GitHub / Mermaid Viewers)

```mermaid
flowchart TB
    subgraph Client["Client Browser (Chrome / Edge)"]
        Customer["Customer / Sales Evaluator"]
        WebSpeech["Browser Web Speech API (STT + TTS)"]
        ReactApp["React 19 + Vite SPA"]
    end

    subgraph Docker["Docker Compose Network (Single-Host MVP)"]
        Nginx["Frontend Container - nginx:1.27-alpine (:5173 -> :80)"]
        FastAPI["Backend Container - FastAPI + Uvicorn (:8001)"]
        Chroma[("ChromaDB Persistent Volume (/app/chroma_db)")]
        Postgres[("PostgreSQL 18 Container (internal :5432)")]
    end

    subgraph External["External AI Service"]
        Gemini["Google Gemini API (gemini-3.5-flash-lite & gemini-embedding-001)"]
    end

    Customer <-->|"1. Voice / Text"| WebSpeech
    WebSpeech <-->|"Transcripts & Audio"| ReactApp
    ReactApp -->|"2. Same-Origin /api/*"| Nginx
    Nginx -->|"Reverse Proxy"| FastAPI
    FastAPI <-->|"3. Semantic Retrieval"| Chroma
    FastAPI <-->|"4. Chat, Sentiment, Extraction, Summary"| Gemini
    Chroma -.->|"Embeddings"| Gemini
    FastAPI <-->|"5. SQLAlchemy + Row Locks"| Postgres
```
