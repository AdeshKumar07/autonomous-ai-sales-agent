"""Pydantic v2 schemas for knowledge base ingestion, status, and semantic search."""

from pydantic import BaseModel, Field, field_validator


class KnowledgeIngestRequest(BaseModel):
    force: bool = False


class KnowledgeIngestDetail(BaseModel):
    document_name: str
    action: str
    chunks: int


class KnowledgeIngestResponse(BaseModel):
    status: str
    ingested_documents: int
    updated_documents: int
    skipped_documents: int
    total_chunks_added: int
    details: list[KnowledgeIngestDetail]


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Search query cannot be empty.")
        return cleaned


class KnowledgeSearchChunk(BaseModel):
    chunk_id: str
    source_filename: str
    document_type: str
    chunk_index: int
    ingestion_timestamp: str
    content: str
    distance: float | None = None
    score: float


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchChunk]


class IndexedDocumentItem(BaseModel):
    source_filename: str
    document_type: str
    chunk_count: int
    content_hash: str
    ingestion_timestamp: str


class KnowledgeDocumentsResponse(BaseModel):
    collection_name: str
    embedding_model: str
    persist_directory: str
    total_documents: int
    total_chunks: int
    documents: list[IndexedDocumentItem]


class KnowledgeStatusResponse(BaseModel):
    chromadb_connected: bool
    status: str
    collection_name: str
    embedding_model: str
    persist_directory: str
    knowledge_base_dir: str
    total_documents: int
    total_chunks: int
    last_ingested_at: str | None = None
