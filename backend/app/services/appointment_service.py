"""Appointment availability, conflict-safe booking, rescheduling, and cancellation."""

from datetime import date, datetime, time, timedelta, timezone
import uuid
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.appointment import Appointment
from app.models.lead import Lead
from app.schemas.appointment_schema import (
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AvailabilityResponse,
    AvailableSlotSchema,
    validate_iana_timezone,
)
from app.services.crm_service import log_crm_activity

ACTIVE_BOOKING_STATUSES = ("CONFIRMED", "PENDING")


def _to_utc(dt: datetime, fallback_tz: str = "UTC") -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo(fallback_tz)).astimezone(timezone.utc)
    return dt.astimezone(timezone.utc)


def _generate_reference(start_utc: datetime) -> str:
    short_id = uuid.uuid4().hex[:6].upper()
    return f"FTX-{start_utc.strftime('%Y%m%d')}-{short_id}"


def _validate_slot_window(start_utc: datetime, end_utc: datetime, tz_name: str) -> None:
    settings = get_settings()
    now_utc = datetime.now(timezone.utc)
    min_allowed = now_utc + timedelta(minutes=settings.booking_min_advance_minutes)
    max_allowed = now_utc + timedelta(days=settings.booking_max_days_ahead)

    if start_utc <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book or reschedule an appointment in the past.",
        )
    if start_utc < min_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Appointments require at least {settings.booking_min_advance_minutes} minutes advance notice.",
        )
    if start_utc > max_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Appointments cannot be booked more than {settings.booking_max_days_ahead} days in advance.",
        )

    local_tz = ZoneInfo(tz_name)
    local_start = start_utc.astimezone(local_tz)
    local_end = end_utc.astimezone(local_tz)

    if local_start.weekday() not in settings.booking_working_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected date is outside working days (Monday–Friday).",
        )

    open_dt = datetime.combine(local_start.date(), time(settings.booking_open_hour, 0), tzinfo=local_tz)
    close_dt = datetime.combine(local_start.date(), time(settings.booking_close_hour, 0), tzinfo=local_tz)
    if local_start < open_dt or local_end > close_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected time is outside working hours ({settings.booking_open_hour:02d}:00–{settings.booking_close_hour:02d}:00 {tz_name}).",
        )


def _find_overlapping_appointments(
    db: Session,
    start_utc: datetime,
    end_utc: datetime,
    exclude_appointment_id: int | None = None,
) -> list[Appointment]:
    settings = get_settings()
    buffer_delta = timedelta(minutes=settings.booking_buffer_minutes)
    window_start = start_utc - buffer_delta
    window_end = end_utc + buffer_delta

    stmt = (
        select(Appointment)
        .where(
            Appointment.status.in_(ACTIVE_BOOKING_STATUSES),
            Appointment.scheduled_start < window_end,
            Appointment.scheduled_end > window_start,
        )
        .with_for_update()
    )
    if exclude_appointment_id is not None:
        stmt = stmt.where(Appointment.id != exclude_appointment_id)

    return list(db.scalars(stmt).all())


def get_available_slots(
    db: Session,
    target_date: date,
    appointment_type: str = "DEMO",
    timezone_name: str | None = None,
) -> AvailabilityResponse:
    """Generate real available time slots from PostgreSQL and booking config."""
    settings = get_settings()
    tz_name = validate_iana_timezone(timezone_name or settings.booking_default_timezone)
    local_tz = ZoneInfo(tz_name)

    is_working_day = target_date.weekday() in settings.booking_working_days
    now_utc = datetime.now(timezone.utc)
    min_allowed = now_utc + timedelta(minutes=settings.booking_min_advance_minutes)
    max_allowed = now_utc + timedelta(days=settings.booking_max_days_ahead)

    slots: list[AvailableSlotSchema] = []
    if is_working_day:
        day_start_local = datetime.combine(target_date, time(settings.booking_open_hour, 0), tzinfo=local_tz)
        day_end_local = datetime.combine(target_date, time(settings.booking_close_hour, 0), tzinfo=local_tz)
        day_start_utc = day_start_local.astimezone(timezone.utc)
        day_end_utc = day_end_local.astimezone(timezone.utc)

        existing = list(
            db.scalars(
                select(Appointment).where(
                    Appointment.status.in_(ACTIVE_BOOKING_STATUSES),
                    Appointment.scheduled_start < day_end_utc + timedelta(minutes=settings.booking_buffer_minutes),
                    Appointment.scheduled_end > day_start_utc - timedelta(minutes=settings.booking_buffer_minutes),
                )
            ).all()
        )

        slot_delta = timedelta(minutes=settings.booking_slot_minutes)
        step_delta = timedelta(minutes=settings.booking_slot_minutes + settings.booking_buffer_minutes)
        buffer_delta = timedelta(minutes=settings.booking_buffer_minutes)

        cursor_local = day_start_local
        while cursor_local + slot_delta <= day_end_local:
            slot_end_local = cursor_local + slot_delta
            slot_start_utc = cursor_local.astimezone(timezone.utc)
            slot_end_utc = slot_end_local.astimezone(timezone.utc)

            if min_allowed <= slot_start_utc <= max_allowed:
                has_conflict = any(
                    (appt.scheduled_start - buffer_delta) < slot_end_utc
                    and (appt.scheduled_end + buffer_delta) > slot_start_utc
                    for appt in existing
                )
                if not has_conflict:
                    slots.append(
                        AvailableSlotSchema(
                            start_utc=slot_start_utc,
                            end_utc=slot_end_utc,
                            display_start=cursor_local.strftime("%I:%M %p").lstrip("0"),
                            display_end=slot_end_local.strftime("%I:%M %p").lstrip("0"),
                            timezone=tz_name,
                        )
                    )
            cursor_local += step_delta

    return AvailabilityResponse(
        date=target_date.isoformat(),
        appointment_type=appointment_type,  # type: ignore[arg-type]
        timezone=tz_name,
        slot_duration_minutes=settings.booking_slot_minutes,
        buffer_minutes=settings.booking_buffer_minutes,
        working_hours=f"{settings.booking_open_hour:02d}:00 - {settings.booking_close_hour:02d}:00 ({tz_name})",
        is_working_day=is_working_day,
        available_slots=slots,
        config_note="Configurable MVP calendar defaults (Mon-Fri, 30m slots, 15m buffer); not official FORTIVEX policy.",
    )


def create_appointment(db: Session, payload: AppointmentCreateRequest) -> Appointment:
    """Validate availability inside a locked transaction and persist a new appointment."""
    tz_name = validate_iana_timezone(payload.timezone)
    start_utc = _to_utc(payload.scheduled_start, tz_name)
    end_utc = _to_utc(payload.scheduled_end, tz_name)

    _validate_slot_window(start_utc, end_utc, tz_name)

    # Lock the lead row to serialize concurrent bookings from the same customer/session.
    if payload.lead_id is not None:
        lead = db.scalar(
            select(Lead).where(Lead.id == payload.lead_id).with_for_update()
        )
    else:
        lead = db.scalar(
            select(Lead).where(Lead.session_id == payload.session_id).with_for_update()
        )

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated CRM lead was not found.",
        )

    # Prevent duplicate booking for the same lead and time slot.
    duplicate = db.scalar(
        select(Appointment).where(
            Appointment.lead_id == lead.id,
            Appointment.status.in_(ACTIVE_BOOKING_STATUSES),
            Appointment.scheduled_start == start_utc,
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active appointment ({duplicate.appointment_reference}) already exists for this lead at that time.",
        )

    # Revalidate availability with row-level lock to prevent double-booking race conditions.
    conflicts = _find_overlapping_appointments(db, start_utc, end_utc)
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested time slot is no longer available. Please choose another slot.",
        )

    customer_name = payload.customer_name or lead.customer_name
    customer_email = payload.customer_email or lead.email
    customer_phone = payload.customer_phone or lead.phone

    # Sync newly supplied contact fields back onto the Lead record if missing.
    if customer_name and not lead.customer_name:
        lead.customer_name = customer_name
    if customer_email and not lead.email:
        lead.email = customer_email
    if customer_phone and not lead.phone:
        lead.phone = customer_phone

    ref = _generate_reference(start_utc)
    meeting_link = (
        f"https://meet.fortivex.demo/{ref.lower()}"
        if payload.appointment_type in ("ONLINE_MEETING", "DEMO")
        else None
    )

    appointment = Appointment(
        appointment_reference=ref,
        lead_id=lead.id,
        session_id=lead.session_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        appointment_type=payload.appointment_type,
        scheduled_start=start_utc,
        scheduled_end=end_utc,
        timezone=tz_name,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        status="CONFIRMED",
        meeting_link=meeting_link,
    )
    db.add(appointment)
    db.add(lead)

    local_str = start_utc.astimezone(ZoneInfo(tz_name)).strftime("%Y-%m-%d %I:%M %p")
    log_crm_activity(
        db=db,
        lead_id=lead.id,
        session_id=lead.session_id,
        activity_type="APPOINTMENT_BOOKED",
        description=f"{payload.appointment_type} booked ({ref}) for {local_str} ({tz_name}).",
        metadata_json={"appointment_reference": ref, "appointment_type": payload.appointment_type},
        commit=False,
    )

    db.commit()
    db.refresh(appointment)
    return appointment


def list_appointments(
    db: Session,
    status_filter: str | None = None,
    date_filter: date | None = None,
    lead_id: int | None = None,
    session_id: str | None = None,
) -> list[Appointment]:
    """List appointments with optional status, date, lead_id, and session_id filters."""
    stmt = select(Appointment)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter.strip().upper())
    if lead_id is not None:
        stmt = stmt.where(Appointment.lead_id == lead_id)
    if session_id:
        stmt = stmt.where(Appointment.session_id == session_id.strip())
    if date_filter is not None:
        day_start = datetime.combine(date_filter, time.min, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(
            Appointment.scheduled_start >= day_start,
            Appointment.scheduled_start < day_end,
        )

    return list(db.scalars(stmt.order_by(Appointment.scheduled_start.asc())).all())


def get_appointment(
    db: Session,
    appointment_id: int,
    session_id: str | None = None,
) -> Appointment:
    """Fetch an appointment by ID, enforcing session isolation when session_id is provided."""
    appt = db.scalar(select(Appointment).where(Appointment.id == appointment_id))
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} was not found.",
        )
    if session_id and appt.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this appointment.",
        )
    return appt


def cancel_appointment(
    db: Session,
    appointment_id: int,
    payload: AppointmentCancelRequest | None = None,
) -> Appointment:
    """Cancel an appointment and log a CRM activity event."""
    session_id = payload.session_id if payload else None
    appt = get_appointment(db, appointment_id, session_id=session_id)
    if appt.status == "CANCELLED":
        return appt

    appt.status = "CANCELLED"
    reason = payload.reason.strip() if payload and payload.reason else "Cancelled by request."
    db.add(appt)

    log_crm_activity(
        db=db,
        lead_id=appt.lead_id,
        session_id=appt.session_id,
        activity_type="APPOINTMENT_CANCELLED",
        description=f"Appointment {appt.appointment_reference} cancelled: {reason}",
        metadata_json={"appointment_reference": appt.appointment_reference},
        commit=False,
    )
    db.commit()
    db.refresh(appt)
    return appt


def reschedule_appointment(
    db: Session,
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
) -> Appointment:
    """Revalidate availability and reschedule an existing appointment."""
    appt = db.scalar(
        select(Appointment).where(Appointment.id == appointment_id).with_for_update()
    )
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} was not found.",
        )
    if payload.session_id and appt.session_id != payload.session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this appointment.",
        )
    if appt.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancelled appointments cannot be rescheduled.",
        )

    tz_name = validate_iana_timezone(payload.timezone or appt.timezone)
    start_utc = _to_utc(payload.scheduled_start, tz_name)
    end_utc = _to_utc(payload.scheduled_end, tz_name)

    _validate_slot_window(start_utc, end_utc, tz_name)

    conflicts = _find_overlapping_appointments(
        db, start_utc, end_utc, exclude_appointment_id=appt.id
    )
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested new time slot is unavailable.",
        )

    appt.scheduled_start = start_utc
    appt.scheduled_end = end_utc
    appt.timezone = tz_name
    appt.status = "CONFIRMED"
    db.add(appt)

    local_str = start_utc.astimezone(ZoneInfo(tz_name)).strftime("%Y-%m-%d %I:%M %p")
    log_crm_activity(
        db=db,
        lead_id=appt.lead_id,
        session_id=appt.session_id,
        activity_type="APPOINTMENT_RESCHEDULED",
        description=f"Appointment {appt.appointment_reference} rescheduled to {local_str} ({tz_name}).",
        metadata_json={"appointment_reference": appt.appointment_reference},
        commit=False,
    )
    db.commit()
    db.refresh(appt)
    return appt
