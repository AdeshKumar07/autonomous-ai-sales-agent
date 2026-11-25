"""Pydantic v2 schemas for appointment availability, booking, and management."""

from datetime import datetime
import re
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AppointmentType = Literal["CALL", "ONLINE_MEETING", "DEMO"]
AppointmentStatus = Literal["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED", "NO_SHOW"]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,20}$")


def validate_iana_timezone(tz_name: str) -> str:
    cleaned = (tz_name or "").strip()
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid IANA timezone: '{cleaned}'.") from exc
    return cleaned


class AvailableSlotSchema(BaseModel):
    start_utc: datetime
    end_utc: datetime
    display_start: str
    display_end: str
    timezone: str


class AvailabilityResponse(BaseModel):
    date: str
    appointment_type: AppointmentType
    timezone: str
    slot_duration_minutes: int
    buffer_minutes: int
    working_hours: str
    is_working_day: bool
    available_slots: list[AvailableSlotSchema]
    config_note: str


class AppointmentCreateRequest(BaseModel):
    lead_id: int | None = None
    session_id: str | None = Field(default=None, min_length=1, max_length=100)
    title: str = Field(default="Fortivex AI Product Demo", min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    appointment_type: AppointmentType = "DEMO"
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    customer_name: str | None = Field(default=None, max_length=150)
    customer_email: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_iana_timezone(value)

    @field_validator("customer_email")
    @classmethod
    def check_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if not _EMAIL_RE.match(cleaned):
            raise ValueError("Invalid email address format.")
        return cleaned

    @field_validator("customer_phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        digits = re.sub(r"\D", "", cleaned)
        if not _PHONE_RE.match(cleaned) or len(digits) < 7 or len(digits) > 15:
            raise ValueError("Invalid phone number format.")
        return cleaned

    @model_validator(mode="after")
    def validate_request(self):
        if self.lead_id is None and not (self.session_id and self.session_id.strip()):
            raise ValueError("Either lead_id or session_id is required.")
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("scheduled_end must be after scheduled_start.")
        duration_minutes = (self.scheduled_end - self.scheduled_start).total_seconds() / 60.0
        if duration_minutes < 15 or duration_minutes > 120:
            raise ValueError("Appointment duration must be between 15 and 120 minutes.")
        return self


class AppointmentRescheduleRequest(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    session_id: str | None = Field(default=None, max_length=100)

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_iana_timezone(value)

    @model_validator(mode="after")
    def validate_times(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("scheduled_end must be after scheduled_start.")
        duration_minutes = (self.scheduled_end - self.scheduled_start).total_seconds() / 60.0
        if duration_minutes < 15 or duration_minutes > 120:
            raise ValueError("Appointment duration must be between 15 and 120 minutes.")
        return self


class AppointmentCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=100)


class AppointmentPublicSchema(BaseModel):
    """Customer-safe appointment representation (excludes internal_notes)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_reference: str
    lead_id: int
    session_id: str
    title: str
    description: str | None = None
    appointment_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    status: str
    meeting_link: str | None = None
    created_at: datetime
    updated_at: datetime


class AppointmentActionResponse(BaseModel):
    success: bool = True
    appointment_reference: str
    status: str
    confirmation_message: str
    appointment: AppointmentPublicSchema
