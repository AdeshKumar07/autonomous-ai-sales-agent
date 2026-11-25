"""Knowledge base document loading, cleaning, chunking, and deduplicated ingestion."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any
from app.core.config import get_settings
from app.rag.retriever import get_knowledge_collection

KNOWLEDGE_DOCUMENT_TYPES = {
    "company_profile.md": "company_profile",
    "products.md": "products",
    "pricing.md": "pricing",
    "faq.md": "faq",
    "policies.md": "policies",
}


def clean_text(raw_text: str) -> str:
    """Normalize line endings, collapse excess whitespace, and trim."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 80) -> list[str]:
    """Split cleaned text into overlapping chunks with boundary awareness."""
    if not text:
        return []
    if chunk_size <= 0:
        return [text]

    overlap = max(0, min(chunk_overlap, chunk_size // 2))
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            split_at = text.rfind("\n\n", start + chunk_size // 2, end)
            if split_at == -1:
                split_at = text.rfind(". ", start + chunk_size // 2, end)
                if split_at != -1:
                    split_at += 1
            if split_at == -1:
                split_at = text.rfind(" ", start + chunk_size // 2, end)
            if split_at > start:
                end = split_at

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= length:
            break
        start = max(start + 1, end - overlap)

    return chunks


def ingest_knowledge_base(force: bool = False) -> dict[str, Any]:
    """Ingest the 5 knowledge documents from backend/app/knowledge_base into ChromaDB."""
    settings = get_settings()
    kb_dir = settings.knowledge_base_dir
    if not kb_dir.exists():
        return {
            "status": "no_directory",
            "ingested_documents": 0,
            "updated_documents": 0,
            "skipped_documents": 0,
            "total_chunks_added": 0,
            "details": [],
        }

    collection = get_knowledge_collection()
    existing_records = collection.get(include=["metadatas"])
    existing_hashes: dict[str, str] = {}
    for meta in existing_records.get("metadatas") or []:
        if not meta:
            continue
        fname = meta.get("source_filename") or meta.get("document_name")
        if fname and "content_hash" in meta:
            existing_hashes[fname] = meta["content_hash"]

    files = sorted(
        p for p in kb_dir.iterdir()
        if p.is_file() and p.name in KNOWLEDGE_DOCUMENT_TYPES
    )

    ingested = 0
    skipped = 0
    updated = 0
    total_chunks_added = 0
    details: list[dict[str, Any]] = []
    ingestion_ts = datetime.now(timezone.utc).isoformat()

    for file_path in files:
        raw_text = file_path.read_text(encoding="utf-8")
        cleaned = clean_text(raw_text)
        if not cleaned:
            continue

        content_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]
        doc_name = file_path.name
        doc_type = KNOWLEDGE_DOCUMENT_TYPES[doc_name]
        prev_hash = existing_hashes.get(doc_name)

        if not force and prev_hash == content_hash:
            skipped += 1
            details.append(
                {
                    "document_name": doc_name,
                    "action": "skipped_duplicate",
                    "chunks": 0,
                }
            )
            continue

        if prev_hash is not None:
            collection.delete(where={"source_filename": doc_name})
            action = "updated"
            updated += 1
        else:
            action = "ingested"
            ingested += 1

        chunks = chunk_text(
            cleaned,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )

        ids = [f"{doc_name}::chunk_{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "source_filename": doc_name,
                "document_type": doc_type,
                "chunk_index": idx,
                "ingestion_timestamp": ingestion_ts,
                "content_hash": content_hash,
            }
            for idx in range(len(chunks))
        ]

        collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        total_chunks_added += len(chunks)
        details.append(
            {
                "document_name": doc_name,
                "action": action,
                "chunks": len(chunks),
            }
        )

    return {
        "status": "ok",
        "ingested_documents": ingested,
        "updated_documents": updated,
        "skipped_documents": skipped,
        "total_chunks_added": total_chunks_added,
        "details": details,
    }
