"""Pydantic v2 schemas for Business Insights and Analytics endpoints."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

DatePreset = Literal["today", "7d", "30d", "90d", "custom", "all"]


class LabelCountItem(BaseModel):
    label: str
    count: int


class TimeSeriesPoint(BaseModel):
    date: str
    count: int


class SentimentTrendPoint(BaseModel):
    date: str
    POSITIVE: int = 0
    NEUTRAL: int = 0
    FRUSTRATED: int = 0
    NEGATIVE: int = 0


class AnalyticsOverviewResponse(BaseModel):
    preset: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    new_leads: int
    lead_distribution: list[LabelCountItem]
    total_appointments: int
    confirmed_appointments: int
    cancelled_appointments: int
    appointment_distribution: list[LabelCountItem]
    appointment_booking_rate: float
    booking_rate_definition: str


class LeadAnalyticsResponse(BaseModel):
    preset: str
    total_leads: int
    new_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    distribution: list[LabelCountItem]
    leads_over_time: list[TimeSeriesPoint]


class SentimentAnalyticsResponse(BaseModel):
    preset: str
    total_analyzed_messages: int
    positive_count: int
    neutral_count: int
    frustrated_count: int
    negative_count: int
    distribution: list[LabelCountItem]
    sentiment_trend_over_time: list[SentimentTrendPoint]


class AppointmentAnalyticsResponse(BaseModel):
    preset: str
    total_appointments: int
    confirmed_count: int
    cancelled_count: int
    completed_count: int
    no_show_count: int
    upcoming_count: int
    appointment_booking_rate: float
    booking_rate_definition: str
    status_distribution: list[LabelCountItem]


class InsightRecommendationItem(BaseModel):
    lead_id: int
    session_id: str
    customer_name: str | None = None
    qualification_status: str
    latest_sentiment: str | None = None
    recommended_action: str


class SalesInsightsResponse(BaseModel):
    preset: str
    top_requirements: list[LabelCountItem] = Field(default_factory=list)
    common_pain_points: list[LabelCountItem] = Field(default_factory=list)
    common_objections: list[LabelCountItem] = Field(default_factory=list)
    frequently_asked_questions: list[LabelCountItem] = Field(default_factory=list)
    recommended_follow_ups: list[InsightRecommendationItem] = Field(default_factory=list)
