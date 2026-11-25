"""AI-powered sentiment analysis and session trend calculation."""

import asyncio
from datetime import datetime, timezone
import json
from google import genai
from google.genai import types
from pydantic import ValidationError
from app.core.config import Settings, validate_gemini_config
from app.models.lead import ConversationMessage
from app.schemas.chat_schema import ChatHistoryItem
from app.schemas.sentiment_schema import SentimentAnalysisResult, SentimentSummarySchema

SENTIMENT_SYSTEM_INSTRUCTION = """You are a precise customer sentiment analyzer for a B2B/B2C sales conversation.
Analyze the latest customer message in the context of recent conversation turns.
Support both English and Hindi messages.

Classify into EXACTLY ONE primary sentiment label:
- POSITIVE: Interested, pleased, appreciative, enthusiastic, or receptive.
- NEUTRAL: Informational, curious, matter-of-fact, or ambiguous.
- FRUSTRATED: Impatient, annoyed by repetition/friction, confused after prior attempts, or irritated.
- NEGATIVE: Rejecting, unwilling, asking to stop contact, or expressing clear dissatisfaction.

Rules:
1. For ambiguous or short unclear messages, prefer NEUTRAL with a lower confidence score (e.g. 0.40 - 0.65).
2. Never invent emotions unsupported by the text.
3. Never infer personality, mental health, or protected/sensitive characteristics.
4. Provide:
   - sentiment: "POSITIVE" | "NEUTRAL" | "FRUSTRATED" | "NEGATIVE"
   - confidence: float between 0.0 and 1.0
   - explanation: concise 1-sentence reason grounded in the message
   - emotional_indicators: short list of 1-4 observed cues/phrases from the message (empty list if neutral/none)
   - recommended_strategy: concise 1-sentence guidance for how the sales agent should respond
"""

# Ordinal valence scale used strictly to determine directional trend between turns.
_VALENCE_ORDER = {
    "NEGATIVE": 0,
    "FRUSTRATED": 1,
    "NEUTRAL": 2,
    "POSITIVE": 3,
}


class SentimentService:
    """Asynchronous Gemini sentiment analyzer with graceful non-blocking fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = validate_gemini_config(settings)
        self._client = genai.Client(api_key=self._settings.gemini_api_key)

    async def analyze_message(
        self,
        message: str,
        history: list[ChatHistoryItem] | None = None,
    ) -> SentimentAnalysisResult | None:
        """Analyze customer message sentiment. Returns None on failure so chat never crashes."""
        recent_turns = (history or [])[-4:]
        history_text = (
            "\n".join(f"{t.role.upper()}: {t.content}" for t in recent_turns)
            if recent_turns
            else "No prior messages."
        )

        prompt = (
            f"Recent Conversation Context:\n{history_text}\n\n"
            f"Latest Customer Message to Analyze:\n{message.strip()}"
        )

        config = types.GenerateContentConfig(
            system_instruction=SENTIMENT_SYSTEM_INSTRUCTION,
            temperature=0.1,
            max_output_tokens=350,
            response_mime_type="application/json",
            response_schema=SentimentAnalysisResult,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._settings.gemini_model,
                    contents=prompt,
                    config=config,
                ),
                timeout=min(self._settings.gemini_timeout_seconds, 12.0),
            )
            raw_text = (getattr(response, "text", None) or "").strip()
            if not raw_text:
                return None
            parsed = json.loads(raw_text)
            result = SentimentAnalysisResult.model_validate(parsed)
            result.analyzed_at = datetime.now(timezone.utc)
            return result
        except (asyncio.TimeoutError, json.JSONDecodeError, ValidationError, Exception):
            return None


def compute_sentiment_summary(messages: list[ConversationMessage]) -> SentimentSummarySchema:
    """Compute latest sentiment, weighted recent overall sentiment, and directional trend."""
    analyzed = [
        m for m in messages
        if m.role == "user" and m.sentiment in _VALENCE_ORDER
    ]

    if not analyzed:
        return SentimentSummarySchema(
            sentiment_trend="insufficient_data",
            analyzed_message_count=0,
        )

    latest = analyzed[-1]

    # Weighted frequency across analyzed customer turns (recent turns weighted higher).
    weights: dict[str, float] = {"POSITIVE": 0.0, "NEUTRAL": 0.0, "FRUSTRATED": 0.0, "NEGATIVE": 0.0}
    total = len(analyzed)
    for idx, msg in enumerate(analyzed):
        recency_weight = 1.5 if idx >= max(0, total - 2) else 1.0
        weights[msg.sentiment] += recency_weight  # type: ignore[index]

    # Break ties in favor of the latest customer sentiment.
    overall_sentiment = max(
        weights.keys(),
        key=lambda label: (weights[label], 1 if label == latest.sentiment else 0),
    )

    if total < 2:
        trend = "insufficient_data"
    else:
        prev_score = _VALENCE_ORDER[analyzed[-2].sentiment]  # type: ignore[index]
        curr_score = _VALENCE_ORDER[latest.sentiment]  # type: ignore[index]
        if curr_score > prev_score:
            trend = "improving"
        elif curr_score < prev_score:
            trend = "declining"
        else:
            trend = "stable"

    return SentimentSummarySchema(
        latest_sentiment=latest.sentiment,  # type: ignore[arg-type]
        latest_confidence=latest.sentiment_confidence,
        latest_explanation=latest.sentiment_explanation,
        latest_emotional_indicators=list(latest.emotional_indicators or []),
        latest_recommended_strategy=latest.recommended_strategy,
        latest_analyzed_at=latest.analyzed_at,
        overall_sentiment=overall_sentiment,  # type: ignore[arg-type]
        sentiment_trend=trend,  # type: ignore[arg-type]
        analyzed_message_count=total,
    )
