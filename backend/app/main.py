from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings, validate_startup_config
from app.database.db import check_db_connection, init_db_with_retry
from app.rag.ingest import ingest_knowledge_base
from app.rag.retriever import get_knowledge_status
from app.routes.agent_routes import router as agent_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.appointment_routes import router as appointment_router
from app.routes.crm_routes import router as crm_router
from app.routes.knowledge_routes import router as knowledge_router
from app.routes.lead_routes import router as lead_router
from app.routes.summary_routes import router as summary_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Validate config, initialize PostgreSQL with retry, and ingest new/updated docs."""
    validate_startup_config(settings)
    init_db_with_retry()
    try:
        ingest_knowledge_base(force=False)
    except Exception:
        logger.warning("Initial knowledge base ingestion skipped due to transient error.")
    yield


app = FastAPI(
    title="Autonomous AI Sales Voice Agent API",
    version="1.0.0",
    debug=False,
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
    """Liveness endpoint confirming the FastAPI process is running."""
    return {
        "status": "ok",
        "service": "autonomous-ai-sales-agent-backend",
        "env": settings.app_env,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness endpoint verifying PostgreSQL and ChromaDB dependencies."""
    db_ok = check_db_connection()
    try:
        kb_status = get_knowledge_status()
        chroma_ok = bool(kb_status.get("chromadb_connected"))
    except Exception:
        chroma_ok = False

    if not db_ok or not chroma_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok" if db_ok else "unavailable",
                "chromadb": "ok" if chroma_ok else "unavailable",
            },
        )

    return {
        "status": "ready",
        "database": "ok",
        "chromadb": "ok",
    }
