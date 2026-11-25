# Project Setup Guide

## Prerequisites

- **Node.js** (v20+ recommended) and **npm**
- **Python 3.11**
- **PostgreSQL 18.1** (for database features)

## 1. Environment Configuration

Copy `backend/.env.example` to `backend/.env` and fill in your credentials:

```powershell
Copy-Item backend\.env.example backend\.env
```

Required variables in `backend/.env`:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://username:password@localhost:5432/database_name`).

> **Note:** Never commit `.env` files or real credentials to version control.

## 2. Backend Setup (Windows PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the FastAPI development server:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify the backend is running by visiting `http://127.0.0.1:8000/health` (or `http://localhost:8000/health`), which returns:

```json
{
  "status": "ok",
  "service": "autonomous-ai-sales-agent-backend"
}
```

## 3. Frontend Setup (Windows PowerShell)

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server starts at `http://localhost:5173`.
