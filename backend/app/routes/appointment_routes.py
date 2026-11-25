"""FastAPI routes for appointment availability, booking, rescheduling, and cancellation."""

from datetime import date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.appointment_schema import (
    AppointmentActionResponse,
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentPublicSchema,
    AppointmentRescheduleRequest,
    AppointmentType,
    AvailabilityResponse,
)
from app.services.appointment_service import (
    cancel_appointment,
    create_appointment,
    get_appointment,
    get_available_slots,
    list_appointments,
    reschedule_appointment,
)

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.get("/availability", response_model=AvailabilityResponse)
def check_availability(
    date: date = Query(..., description="Target date in YYYY-MM-DD format"),
    appointment_type: AppointmentType = Query(default="DEMO"),
    timezone: str = Query(default="UTC", description="IANA timezone name"),
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    """Return available booking slots for a given date, type, and timezone."""
    return get_available_slots(
        db=db,
        target_date=date,
        appointment_type=appointment_type,
        timezone_name=timezone,
    )


@router.post("", response_model=AppointmentActionResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreateRequest,
    db: Session = Depends(get_db),
) -> AppointmentActionResponse:
    """Validate availability and persist a new appointment linked to a CRM lead."""
    appt = create_appointment(db=db, payload=payload)
    local_time = appt.scheduled_start.astimezone(ZoneInfo(appt.timezone)).strftime("%Y-%m-%d %I:%M %p")
    return AppointmentActionResponse(
        success=True,
        appointment_reference=appt.appointment_reference,
        status=appt.status,
        confirmation_message=(
            f"Your {appt.appointment_type} appointment is confirmed for {local_time} ({appt.timezone}). "
            f"Booking reference: {appt.appointment_reference}."
        ),
        appointment=AppointmentPublicSchema.model_validate(appt),
    )


@router.get("", response_model=list[AppointmentPublicSchema])
def get_appointments(
    status_filter: str | None = Query(default=None, alias="status"),
    date_filter: date | None = Query(default=None, alias="date"),
    lead_id: int | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AppointmentPublicSchema]:
    """List appointments with optional status, date, lead_id, and session_id filters."""
    items = list_appointments(
        db=db,
        status_filter=status_filter,
        date_filter=date_filter,
        lead_id=lead_id,
        session_id=session_id,
    )
    return [AppointmentPublicSchema.model_validate(item) for item in items]


@router.get("/{appointment_id}", response_model=AppointmentPublicSchema)
def get_appointment_details(
    appointment_id: int,
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AppointmentPublicSchema:
    """Return details for a single appointment (enforces session isolation if session_id passed)."""
    appt = get_appointment(db=db, appointment_id=appointment_id, session_id=session_id)
    return AppointmentPublicSchema.model_validate(appt)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentActionResponse)
def cancel_existing_appointment(
    appointment_id: int,
    payload: AppointmentCancelRequest | None = None,
    db: Session = Depends(get_db),
) -> AppointmentActionResponse:
    """Cancel an existing appointment and record CRM activity."""
    appt = cancel_appointment(db=db, appointment_id=appointment_id, payload=payload)
    return AppointmentActionResponse(
        success=True,
        appointment_reference=appt.appointment_reference,
        status=appt.status,
        confirmation_message=f"Appointment {appt.appointment_reference} has been cancelled.",
        appointment=AppointmentPublicSchema.model_validate(appt),
    )


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentActionResponse)
def reschedule_existing_appointment(
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
    db: Session = Depends(get_db),
) -> AppointmentActionResponse:
    """Revalidate availability and reschedule an existing appointment."""
    appt = reschedule_appointment(db=db, appointment_id=appointment_id, payload=payload)
    local_time = appt.scheduled_start.astimezone(ZoneInfo(appt.timezone)).strftime("%Y-%m-%d %I:%M %p")
    return AppointmentActionResponse(
        success=True,
        appointment_reference=appt.appointment_reference,
        status=appt.status,
        confirmation_message=(
            f"Appointment {appt.appointment_reference} rescheduled to {local_time} ({appt.timezone})."
        ),
        appointment=AppointmentPublicSchema.model_validate(appt),
    )
