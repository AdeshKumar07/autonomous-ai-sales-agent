"""SQLAlchemy ORM models for leads and conversation history with sentiment."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment, CRMActivity


class Lead(Base):
    """Customer lead record linked 1-to-1 with a conversation session_id."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purchase_timeline: Mapped[str | None] = mapped_column(String(120), nullable=True)
    interest_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qualification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NEW"
    )
    qualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_follow_up: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="lead",
        order_by="ConversationMessage.id",
        cascade="all, delete-orphan",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="lead",
        order_by="Appointment.scheduled_start",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list["CRMActivity"]] = relationship(
        "CRMActivity",
        back_populates="lead",
        order_by="CRMActivity.id.desc()",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    """Individual user or assistant message belonging to a lead session."""

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("leads.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_indicators: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommended_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="messages")
