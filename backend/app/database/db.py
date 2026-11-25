"""SQLAlchemy database engine, session factory, readiness check, and safe migrations."""

from collections.abc import Generator
import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not configured.")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped SQLAlchemy session for FastAPI request handling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verify PostgreSQL connectivity for readiness probes."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db() -> None:
    """Safely create missing tables and migrate new columns without deleting records."""
    from app.models import appointment, lead, summary  # noqa: F401

    Base.metadata.create_all(bind=engine)

    alter_statements = (
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20);",
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS sentiment_confidence DOUBLE PRECISION;",
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS sentiment_explanation TEXT;",
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS emotional_indicators JSON;",
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS recommended_strategy TEXT;",
        "ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS internal_notes TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up VARCHAR(255);",
    )
    with engine.begin() as conn:
        for stmt in alter_statements:
            conn.execute(text(stmt))


def init_db_with_retry(max_attempts: int = 10, delay_seconds: float = 2.0) -> None:
    """Retry database initialization on container startup while PostgreSQL warms up."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            init_db()
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Database not ready (attempt %d/%d); retrying...", attempt, max_attempts)
            time.sleep(delay_seconds)
    raise RuntimeError("Database initialization failed after startup retries.") from last_error
