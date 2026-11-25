"""ChromaDB persistent vector store and semantic retrieval helpers."""

from functools import lru_cache
from typing import Any
import chromadb
from app.core.config import get_settings
from app.rag.embeddings import GeminiEmbeddingFunction


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """Return a cached PersistentClient backed by disk storage."""
    settings = get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_persist_dir))


@lru_cache(maxsize=1)
def get_embedding_function() -> GeminiEmbeddingFunction:
    """Return a cached Gemini embedding function."""
    return GeminiEmbeddingFunction(get_settings())


def get_knowledge_collection():
    """Get or create the persisted ChromaDB knowledge base collection."""
    settings = get_settings()
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def search_knowledge(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    """Retrieve the top-k most semantically relevant chunks for a query."""
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    settings = get_settings()
    collection = get_knowledge_collection()
    total = collection.count()
    if total == 0:
        return []

    n_results = min(top_k or settings.rag_top_k, total)
    results = collection.query(
        query_texts=[cleaned_query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    ids = (results.get("ids") or [[]])[0]
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    matches: list[dict[str, Any]] = []
    for chunk_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
        meta = meta or {}
        similarity = round(max(0.0, 1.0 - float(dist)), 4) if dist is not None else 0.0
        source_filename = meta.get("source_filename") or meta.get("document_name", "unknown")
        matches.append(
            {
                "chunk_id": chunk_id,
                "source_filename": source_filename,
                "document_type": meta.get("document_type", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "ingestion_timestamp": meta.get("ingestion_timestamp", ""),
                "content": doc_text,
                "distance": round(float(dist), 4) if dist is not None else None,
                "score": similarity,
            }
        )

    return matches


def list_indexed_documents() -> dict[str, Any]:
    """Summarize all indexed documents and chunk counts in ChromaDB."""
    settings = get_settings()
    collection = get_knowledge_collection()
    total_chunks = collection.count()

    if total_chunks == 0:
        return {
            "collection_name": settings.chroma_collection_name,
            "embedding_model": settings.gemini_embedding_model,
            "persist_directory": str(settings.chroma_persist_dir),
            "total_documents": 0,
            "total_chunks": 0,
            "documents": [],
        }

    records = collection.get(include=["metadatas"])
    metadatas = records.get("metadatas") or []

    doc_map: dict[str, dict[str, Any]] = {}
    for meta in metadatas:
        if not meta:
            continue
        name = meta.get("source_filename") or meta.get("document_name", "unknown")
        if name not in doc_map:
            doc_map[name] = {
                "source_filename": name,
                "document_type": meta.get("document_type", "unknown"),
                "chunk_count": 0,
                "content_hash": meta.get("content_hash", ""),
                "ingestion_timestamp": meta.get("ingestion_timestamp", ""),
            }
        doc_map[name]["chunk_count"] += 1

    documents = sorted(doc_map.values(), key=lambda d: d["source_filename"])
    return {
        "collection_name": settings.chroma_collection_name,
        "embedding_model": settings.gemini_embedding_model,
        "persist_directory": str(settings.chroma_persist_dir),
        "total_documents": len(documents),
        "total_chunks": total_chunks,
        "documents": documents,
    }


def get_knowledge_status() -> dict[str, Any]:
    """Return ChromaDB connection and ingestion status."""
    settings = get_settings()
    summary = list_indexed_documents()
    timestamps = [d["ingestion_timestamp"] for d in summary["documents"] if d.get("ingestion_timestamp")]
    last_ingested_at = max(timestamps) if timestamps else None
    total_chunks = summary["total_chunks"]

    return {
        "chromadb_connected": True,
        "status": "ready" if total_chunks > 0 else "empty",
        "collection_name": settings.chroma_collection_name,
        "embedding_model": settings.gemini_embedding_model,
        "persist_directory": str(settings.chroma_persist_dir),
        "knowledge_base_dir": str(settings.knowledge_base_dir),
        "total_documents": summary["total_documents"],
        "total_chunks": total_chunks,
        "last_ingested_at": last_ingested_at,
    }
