"""FastAPI routes for PostgreSQL-backed Business Insights & Sales Analytics."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.analytics_schema import (
    AnalyticsOverviewResponse,
    AppointmentAnalyticsResponse,
    DatePreset,
    LeadAnalyticsResponse,
    SalesInsightsResponse,
    SentimentAnalyticsResponse,
)
from app.services.analytics_service import (
    get_analytics_overview,
    get_appointment_analytics,
    get_lead_analytics,
    get_sales_insights,
    get_sentiment_analytics,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview(
    preset: DatePreset = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:
    return get_analytics_overview(db, preset=preset, start_date=start_date, end_date=end_date)


@router.get("/leads", response_model=LeadAnalyticsResponse)
def analytics_leads(
    preset: DatePreset = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> LeadAnalyticsResponse:
    return get_lead_analytics(db, preset=preset, start_date=start_date, end_date=end_date)


@router.get("/sentiment", response_model=SentimentAnalyticsResponse)
def analytics_sentiment(
    preset: DatePreset = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SentimentAnalyticsResponse:
    return get_sentiment_analytics(db, preset=preset, start_date=start_date, end_date=end_date)


@router.get("/appointments", response_model=AppointmentAnalyticsResponse)
def analytics_appointments(
    preset: DatePreset = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AppointmentAnalyticsResponse:
    return get_appointment_analytics(db, preset=preset, start_date=start_date, end_date=end_date)


@router.get("/sales-insights", response_model=SalesInsightsResponse)
def analytics_sales_insights(
    preset: DatePreset = Query(default="30d"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SalesInsightsResponse:
    return get_sales_insights(db, preset=preset, start_date=start_date, end_date=end_date)
