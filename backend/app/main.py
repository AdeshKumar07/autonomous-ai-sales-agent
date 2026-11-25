from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.database.db import init_db
from app.rag.ingest import ingest_knowledge_base
from app.routes.agent_routes import router as agent_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.appointment_routes import router as appointment_router
from app.routes.crm_routes import router as crm_router
from app.routes.knowledge_routes import router as knowledge_router
from app.routes.lead_routes import router as lead_router
from app.routes.summary_routes import router as summary_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize PostgreSQL tables and ingest any new/updated knowledge docs on startup."""
    init_db()
    try:
        ingest_knowledge_base(force=False)
    except Exception:
        pass
    yield


app = FastAPI(
    title="Autonomous AI Sales Voice Agent API",
    version="0.6.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(lead_router)
app.include_router(knowledge_router)
app.include_router(appointment_router)
app.include_router(crm_router)
app.include_router(summary_router)
app.include_router(analytics_router)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API server is running."""
    return {"status": "ok", "service": "autonomous-ai-sales-agent-backend"}
