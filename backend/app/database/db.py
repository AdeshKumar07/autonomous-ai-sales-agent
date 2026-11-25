"""SQLAlchemy database engine, session factory, and safe schema initialization."""

from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from app.core.config import get_settings

settings = get_settings()

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not configured in backend/.env.")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
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


def init_db() -> None:
    """Safely create missing tables and migrate new columns without deleting records."""
    from app.models import appointment, lead, summary  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Idempotent column additions for existing tables.
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
