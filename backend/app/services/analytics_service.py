"""PostgreSQL-backed business analytics and sales insights aggregation service."""

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from app.models.lead import ConversationMessage, Lead
from app.models.summary import ConversationSummary
from app.schemas.analytics_schema import (
    AnalyticsOverviewResponse,
    AppointmentAnalyticsResponse,
    InsightRecommendationItem,
    LabelCountItem,
    LeadAnalyticsResponse,
    SalesInsightsResponse,
    SentimentAnalyticsResponse,
    SentimentTrendPoint,
    TimeSeriesPoint,
)
from app.services.sentiment_service import compute_sentiment_summary
from app.services.summary_service import determine_recommended_action

BOOKING_RATE_DEFINITION = (
    "Percentage of leads created in the selected period that have at least one "
    "CONFIRMED or COMPLETED appointment: (booked_leads / total_leads) * 100."
)


def resolve_date_window(
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Convert preset or custom date filters into consistent UTC datetime bounds."""
    now_utc = datetime.now(timezone.utc)
    today_start = datetime.combine(now_utc.date(), time.min, tzinfo=timezone.utc)

    if preset == "all":
        return None, None
    if preset == "today":
        return today_start, now_utc
    if preset == "7d":
        return today_start - timedelta(days=6), now_utc
    if preset == "30d":
        return today_start - timedelta(days=29), now_utc
    if preset == "90d":
        return today_start - timedelta(days=89), now_utc
    if preset == "custom":
        if not start_date or not end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both start_date and end_date are required for custom date range.",
            )
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date cannot be earlier than start_date.",
            )
        return (
            datetime.combine(start_date, time.min, tzinfo=timezone.utc),
            datetime.combine(end_date, time.max, tzinfo=timezone.utc),
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported date preset: '{preset}'.",
    )


def _apply_date_bounds(stmt, column, start_utc: datetime | None, end_utc: datetime | None):
    if start_utc is not None:
        stmt = stmt.where(column >= start_utc)
    if end_utc is not None:
        stmt = stmt.where(column <= end_utc)
    return stmt


def get_lead_analytics(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> LeadAnalyticsResponse:
    start_utc, end_utc = resolve_date_window(preset, start_date, end_date)

    status_stmt = _apply_date_bounds(
        select(Lead.qualification_status, func.count(Lead.id)).group_by(Lead.qualification_status),
        Lead.created_at,
        start_utc,
        end_utc,
    )
    counts = {row[0]: int(row[1]) for row in db.execute(status_stmt).all()}

    new_c = counts.get("NEW", 0)
    hot_c = counts.get("HOT", 0)
    warm_c = counts.get("WARM", 0)
    cold_c = counts.get("COLD", 0)
    total = new_c + hot_c + warm_c + cold_c

    series_stmt = _apply_date_bounds(
        select(func.date(Lead.created_at), func.count(Lead.id))
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at).asc()),
        Lead.created_at,
        start_utc,
        end_utc,
    )
    leads_over_time = [
        TimeSeriesPoint(date=str(row[0]), count=int(row[1]))
        for row in db.execute(series_stmt).all()
    ]

    return LeadAnalyticsResponse(
        preset=preset,
        total_leads=total,
        new_leads=new_c,
        hot_leads=hot_c,
        warm_leads=warm_c,
        cold_leads=cold_c,
        distribution=[
            LabelCountItem(label="HOT", count=hot_c),
            LabelCountItem(label="WARM", count=warm_c),
            LabelCountItem(label="COLD", count=cold_c),
            LabelCountItem(label="NEW", count=new_c),
        ],
        leads_over_time=leads_over_time,
    )


def get_sentiment_analytics(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> SentimentAnalyticsResponse:
    start_utc, end_utc = resolve_date_window(preset, start_date, end_date)

    base_filter = (ConversationMessage.role == "user") & (ConversationMessage.sentiment.is_not(None))
    counts_stmt = _apply_date_bounds(
        select(ConversationMessage.sentiment, func.count(ConversationMessage.id))
        .where(base_filter)
        .group_by(ConversationMessage.sentiment),
        ConversationMessage.created_at,
        start_utc,
        end_utc,
    )
    counts = {row[0]: int(row[1]) for row in db.execute(counts_stmt).all()}

    pos = counts.get("POSITIVE", 0)
    neu = counts.get("NEUTRAL", 0)
    fru = counts.get("FRUSTRATED", 0)
    neg = counts.get("NEGATIVE", 0)
    total = pos + neu + fru + neg

    trend_stmt = _apply_date_bounds(
        select(
            func.date(ConversationMessage.created_at),
            ConversationMessage.sentiment,
            func.count(ConversationMessage.id),
        )
        .where(base_filter)
        .group_by(func.date(ConversationMessage.created_at), ConversationMessage.sentiment)
        .order_by(func.date(ConversationMessage.created_at).asc()),
        ConversationMessage.created_at,
        start_utc,
        end_utc,
    )

    by_day: dict[str, dict[str, int]] = defaultdict(
        lambda: {"POSITIVE": 0, "NEUTRAL": 0, "FRUSTRATED": 0, "NEGATIVE": 0}
    )
    for day_val, label, cnt in db.execute(trend_stmt).all():
        if label in by_day[str(day_val)]:
            by_day[str(day_val)][label] = int(cnt)

    trend_points = [
        SentimentTrendPoint(date=day_key, **vals)
        for day_key, vals in sorted(by_day.items())
    ]

    return SentimentAnalyticsResponse(
        preset=preset,
        total_analyzed_messages=total,
        positive_count=pos,
        neutral_count=neu,
        frustrated_count=fru,
        negative_count=neg,
        distribution=[
            LabelCountItem(label="POSITIVE", count=pos),
            LabelCountItem(label="NEUTRAL", count=neu),
            LabelCountItem(label="FRUSTRATED", count=fru),
            LabelCountItem(label="NEGATIVE", count=neg),
        ],
        sentiment_trend_over_time=trend_points,
    )


def get_appointment_analytics(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> AppointmentAnalyticsResponse:
    start_utc, end_utc = resolve_date_window(preset, start_date, end_date)
    now_utc = datetime.now(timezone.utc)

    status_stmt = _apply_date_bounds(
        select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status),
        Appointment.created_at,
        start_utc,
        end_utc,
    )
    counts = {row[0]: int(row[1]) for row in db.execute(status_stmt).all()}

    conf = counts.get("CONFIRMED", 0)
    canc = counts.get("CANCELLED", 0)
    comp = counts.get("COMPLETED", 0)
    nosh = counts.get("NO_SHOW", 0)
    pend = counts.get("PENDING", 0)
    total = conf + canc + comp + nosh + pend

    upcoming_stmt = select(func.count(Appointment.id)).where(
        Appointment.status.in_(("CONFIRMED", "PENDING")),
        Appointment.scheduled_start >= now_utc,
    )
    upcoming = int(db.scalar(upcoming_stmt) or 0)

    lead_total_stmt = _apply_date_bounds(
        select(func.count(Lead.id)),
        Lead.created_at,
        start_utc,
        end_utc,
    )
    total_leads = int(db.scalar(lead_total_stmt) or 0)

    booked_leads_stmt = _apply_date_bounds(
        select(func.count(func.distinct(Appointment.lead_id))).where(
            Appointment.status.in_(("CONFIRMED", "COMPLETED"))
        ),
        Appointment.created_at,
        start_utc,
        end_utc,
    )
    booked_leads = int(db.scalar(booked_leads_stmt) or 0)
    booking_rate = round((booked_leads / total_leads) * 100.0, 2) if total_leads > 0 else 0.0

    return AppointmentAnalyticsResponse(
        preset=preset,
        total_appointments=total,
        confirmed_count=conf,
        cancelled_count=canc,
        completed_count=comp,
        no_show_count=nosh,
        upcoming_count=upcoming,
        appointment_booking_rate=booking_rate,
        booking_rate_definition=BOOKING_RATE_DEFINITION,
        status_distribution=[
            LabelCountItem(label="CONFIRMED", count=conf),
            LabelCountItem(label="CANCELLED", count=canc),
            LabelCountItem(label="COMPLETED", count=comp),
            LabelCountItem(label="NO_SHOW", count=nosh),
        ],
    )


def get_analytics_overview(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> AnalyticsOverviewResponse:
    start_utc, end_utc = resolve_date_window(preset, start_date, end_date)
    lead_stats = get_lead_analytics(db, preset, start_date, end_date)
    appt_stats = get_appointment_analytics(db, preset, start_date, end_date)

    return AnalyticsOverviewResponse(
        preset=preset,
        start_date=start_utc,
        end_date=end_utc,
        total_leads=lead_stats.total_leads,
        hot_leads=lead_stats.hot_leads,
        warm_leads=lead_stats.warm_leads,
        cold_leads=lead_stats.cold_leads,
        new_leads=lead_stats.new_leads,
        lead_distribution=lead_stats.distribution,
        total_appointments=appt_stats.total_appointments,
        confirmed_appointments=appt_stats.confirmed_count,
        cancelled_appointments=appt_stats.cancelled_count,
        appointment_distribution=appt_stats.status_distribution,
        appointment_booking_rate=appt_stats.appointment_booking_rate,
        booking_rate_definition=BOOKING_RATE_DEFINITION,
    )


def get_sales_insights(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> SalesInsightsResponse:
    start_utc, end_utc = resolve_date_window(preset, start_date, end_date)

    summary_stmt = _apply_date_bounds(
        select(ConversationSummary),
        ConversationSummary.updated_at,
        start_utc,
        end_utc,
    )
    summaries = list(db.scalars(summary_stmt).all())

    req_counter: Counter[str] = Counter()
    pain_counter: Counter[str] = Counter()
    obj_counter: Counter[str] = Counter()
    q_counter: Counter[str] = Counter()

    for s in summaries:
        for r in s.customer_requirements or []:
            if r.strip():
                req_counter[r.strip()] += 1
        for p in s.pain_points or []:
            if p.strip():
                pain_counter[p.strip()] += 1
        for o in s.objections or []:
            if o.strip():
                obj_counter[o.strip()] += 1
        for q in s.customer_questions or []:
            if q.strip():
                q_counter[q.strip()] += 1

    # Also include Lead.requirements from leads that don't yet have a ConversationSummary
    summarized_lead_ids = {s.lead_id for s in summaries}
    lead_stmt = _apply_date_bounds(
        select(Lead).order_by(Lead.updated_at.desc()).limit(50),
        Lead.created_at,
        start_utc,
        end_utc,
    )
    leads = list(db.scalars(lead_stmt).all())
    for ld in leads:
        if ld.id not in summarized_lead_ids and ld.requirements and ld.requirements.strip():
            req_counter[ld.requirements.strip()] += 1

    recommendations: list[InsightRecommendationItem] = []
    for ld in leads[:10]:
        msgs = list(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.session_id == ld.session_id)
                .order_by(ConversationMessage.id.asc())
            ).all()
        )
        sent = compute_sentiment_summary(msgs)
        appt = db.scalar(
            select(Appointment)
            .where(Appointment.lead_id == ld.id, Appointment.status.in_(("CONFIRMED", "COMPLETED")))
            .limit(1)
        )
        action = determine_recommended_action(
            lead=ld,
            latest_sentiment=sent.latest_sentiment,
            appointment=appt,
            messages=msgs,
        )
        recommendations.append(
            InsightRecommendationItem(
                lead_id=ld.id,
                session_id=ld.session_id,
                customer_name=ld.customer_name,
                qualification_status=ld.qualification_status,
                latest_sentiment=sent.latest_sentiment,
                recommended_action=action,
            )
        )

    def _top(counter: Counter[str]) -> list[LabelCountItem]:
        return [LabelCountItem(label=k, count=v) for k, v in counter.most_common(6)]

    return SalesInsightsResponse(
        preset=preset,
        top_requirements=_top(req_counter),
        common_pain_points=_top(pain_counter),
        common_objections=_top(obj_counter),
        frequently_asked_questions=_top(q_counter),
        recommended_follow_ups=recommendations,
    )
