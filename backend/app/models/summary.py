"""SQLAlchemy ORM model for structured conversation summaries."""

from datetime import datetime
from typing import Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


class ConversationSummary(Base):
    """Persisted structured sales summary linked 1-to-1 with a session_id and Lead."""

    __tablename__ = "conversation_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("leads.session_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    lead_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    budget: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purchase_timeline: Mapped[str | None] = mapped_column(String(120), nullable=True)
    main_business_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    pain_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    discussed_products: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    customer_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    sentiment_overview: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    qualification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    appointment_reference: Mapped[str | None] = mapped_column(String(40), nullable=True)
    unresolved_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommended_next_action: Mapped[str] = mapped_column(Text, nullable=False)
    is_conversation_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    message_count_at_generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
