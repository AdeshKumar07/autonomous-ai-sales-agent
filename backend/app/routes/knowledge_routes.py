"""API routes for knowledge base ingestion, status, listing, and semantic search."""

import secrets
from fastapi import APIRouter, Header, HTTPException, status
from app.core.config import get_settings
from app.rag.ingest import ingest_knowledge_base
from app.rag.retriever import get_knowledge_status, list_indexed_documents, search_knowledge
from app.schemas.knowledge_schema import (
    KnowledgeDocumentsResponse,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeStatusResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])


def _verify_ingest_access(x_admin_token: str | None) -> None:
    """Protect ingestion endpoint when RAG_ADMIN_TOKEN is configured."""
    settings = get_settings()
    if not settings.rag_admin_token:
        return
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.rag_admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token for knowledge ingestion.",
        )


@router.post("/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge(
    payload: KnowledgeIngestRequest | None = None,
    x_admin_token: str | None = Header(default=None),
) -> KnowledgeIngestResponse:
    """Ingest documents from backend/app/knowledge_base into ChromaDB."""
    _verify_ingest_access(x_admin_token)
    force = payload.force if payload else False
    try:
        result = ingest_knowledge_base(force=force)
        return KnowledgeIngestResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest knowledge base documents.",
        ) from exc


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge_endpoint(payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    """Perform semantic similarity search against the indexed knowledge base."""
    try:
        matches = search_knowledge(query=payload.query, top_k=payload.top_k)
        return KnowledgeSearchResponse(query=payload.query, results=matches)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge base.",
        ) from exc


@router.get("/documents", response_model=KnowledgeDocumentsResponse)
def list_knowledge_documents() -> KnowledgeDocumentsResponse:
    """List indexed documents and chunk counts from ChromaDB."""
    try:
        summary = list_indexed_documents()
        return KnowledgeDocumentsResponse(**summary)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list indexed knowledge documents.",
        ) from exc


@router.get("/status", response_model=KnowledgeStatusResponse)
def knowledge_status() -> KnowledgeStatusResponse:
    """Return ChromaDB collection and ingestion status."""
    try:
        status_data = get_knowledge_status()
        return KnowledgeStatusResponse(**status_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ChromaDB knowledge status.",
        ) from exc
