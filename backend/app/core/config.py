"""Application configuration loaded securely from backend/.env."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import quote_plus, unquote
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

# Load backend/.env if present; existing process env vars take precedence if set.
load_dotenv(dotenv_path=ENV_FILE)


def normalize_database_url(raw_url: str) -> str:
    """Normalize a PostgreSQL URL for SQLAlchemy + psycopg2 without logging secrets."""
    url = (raw_url or "").strip()
    if url.startswith("DATABASE_URL="):
        url = url[len("DATABASE_URL="):].strip()
    if not url:
        return ""

    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]

    if "://" in url and "@" in url:
        scheme, rest = url.split("://", 1)
        creds, host_and_db = rest.rsplit("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
            encoded_password = quote_plus(unquote(password))
            url = f"{scheme}://{user}:{encoded_password}@{host_and_db}"

    return url


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings for the backend service."""

    gemini_api_key: str
    gemini_model: str
    gemini_embedding_model: str
    gemini_timeout_seconds: float
    database_url: str
    max_history_turns: int
    cors_origins: tuple[str, ...]
    knowledge_base_dir: Path
    chroma_persist_dir: Path
    chroma_collection_name: str
    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_top_k: int
    rag_admin_token: str
    # Configurable MVP booking calendar defaults (not official FORTIVEX policies)
    booking_working_days: tuple[int, ...]
    booking_open_hour: int
    booking_close_hour: int
    booking_slot_minutes: int
    booking_buffer_minutes: int
    booking_min_advance_minutes: int
    booking_max_days_ahead: int
    booking_default_timezone: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite"
    embedding_model = (
        os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001").strip()
        or "models/gemini-embedding-001"
    )
    timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", "20").strip()
    try:
        timeout = max(5.0, float(timeout_raw))
    except ValueError:
        timeout = 20.0

    database_url = normalize_database_url(os.getenv("DATABASE_URL", ""))
    collection_name = (
        os.getenv("CHROMA_COLLECTION_NAME", "fortivex_research_kb").strip()
        or "fortivex_research_kb"
    )
    rag_admin_token = os.getenv("RAG_ADMIN_TOKEN", "").strip()
    default_tz = os.getenv("BOOKING_DEFAULT_TIMEZONE", "UTC").strip() or "UTC"

    return Settings(
        gemini_api_key=api_key,
        gemini_model=model,
        gemini_embedding_model=embedding_model,
        gemini_timeout_seconds=timeout,
        database_url=database_url,
        max_history_turns=20,
        cors_origins=(
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ),
        knowledge_base_dir=BACKEND_DIR / "app" / "knowledge_base",
        chroma_persist_dir=BACKEND_DIR / "chroma_db",
        chroma_collection_name=collection_name,
        rag_chunk_size=500,
        rag_chunk_overlap=80,
        rag_top_k=4,
        rag_admin_token=rag_admin_token,
        booking_working_days=(0, 1, 2, 3, 4),  # Mon-Fri
        booking_open_hour=int(os.getenv("BOOKING_OPEN_HOUR", "9")),
        booking_close_hour=int(os.getenv("BOOKING_CLOSE_HOUR", "18")),
        booking_slot_minutes=int(os.getenv("BOOKING_SLOT_MINUTES", "30")),
        booking_buffer_minutes=int(os.getenv("BOOKING_BUFFER_MINUTES", "15")),
        booking_min_advance_minutes=int(os.getenv("BOOKING_MIN_ADVANCE_MINUTES", "60")),
        booking_max_days_ahead=int(os.getenv("BOOKING_MAX_DAYS_AHEAD", "30")),
        booking_default_timezone=default_tz,
    )


def validate_gemini_config(settings: Settings | None = None) -> Settings:
    """Ensure required Gemini configuration values are present without exposing secrets."""
    cfg = settings or get_settings()
    if not cfg.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in backend/.env.")
    if not cfg.gemini_model:
        raise RuntimeError("GEMINI_MODEL is not configured in backend/.env.")
    return cfg
