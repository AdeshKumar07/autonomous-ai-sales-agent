"""Google Gen AI SDK client wrapper for sales replies and structured lead extraction."""

import asyncio
import json
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError
from app.agents.sales_agent import (
    build_gemini_contents,
    build_lead_aware_system_instruction,
    format_lead_context,
)
from app.core.config import Settings, validate_gemini_config
from app.models.lead import Lead
from app.schemas.chat_schema import ChatHistoryItem
from app.schemas.lead_schema import LeadExtractionResult
from app.schemas.sentiment_schema import SentimentAnalysisResult


class GeminiServiceError(Exception):
    """Base exception for sanitized Gemini service errors."""


class GeminiConfigError(GeminiServiceError):
    """Raised when Gemini API credentials are missing or invalid."""


class GeminiModelError(GeminiServiceError):
    """Raised when the configured Gemini model is unavailable."""


class GeminiRateLimitError(GeminiServiceError):
    """Raised when Gemini rate limits or quotas are exceeded."""


class GeminiTimeoutError(GeminiServiceError):
    """Raised when Gemini does not respond within the configured timeout."""


class GeminiEmptyResponseError(GeminiServiceError):
    """Raised when Gemini returns an empty or unreadable response."""


LEAD_EXTRACTION_SYSTEM_INSTRUCTION = """You are a precise CRM data extraction and lead qualification engine.
Analyze the existing saved lead profile and the latest customer message.
Extract EVERY relevant fact from the latest customer message into the structured JSON fields:
- customer_name
- company_name
- email
- phone
- business_type
- requirements
- budget
- purchase_timeline
- interest_level ("High", "Medium", or "Low")
- qualification_status ("NEW", "HOT", "WARM", or "COLD")
- qualification_reason (concise 1-sentence explanation)
- cleared_fields (array of field names ONLY if the customer explicitly asks to delete/remove an earlier value)

Strict extraction rules:
1. NOT MENTIONED: If a field is NOT mentioned in the latest customer message, return null for that field (existing saved values will be preserved automatically).
2. EXPLICIT CORRECTION: If the customer corrects an earlier value (e.g. changes budget or company name), output the NEW corrected value.
3. EXPLICITLY DECLINED: If the customer declines to share a field (e.g. "I prefer not to share my email"), return null for that field and do NOT invent anything.
4. MULTI-FACT MESSAGES: Carefully capture all facts when a single message contains multiple details (for example: requirements + budget + purchase_timeline).
5. QUALIFICATION LOGIC: Evaluate buying intent, requirements, and purchase timeline together — NEVER classify based only on budget:
   - HOT: Strong buying intent, clear business requirements, AND a near-term purchase timeline (e.g. immediate, this month, within 30-60 days).
   - WARM: Interested or has requirements/budget, but still evaluating options or has a medium/unclear timeline.
   - COLD: Low buying intent, explicitly not interested, or no immediate requirement.
   - NEW: Insufficient information to qualify yet.
"""


def parse_extraction_json(raw_text: str) -> LeadExtractionResult | None:
    """Validate raw JSON text into LeadExtractionResult; return None if invalid."""
    if not raw_text or not raw_text.strip():
        return None
    try:
        parsed = json.loads(raw_text.strip())
        if not isinstance(parsed, dict):
            return None
        return LeadExtractionResult.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError):
        return None


class GeminiService:
    """Asynchronous wrapper around the official Google Gen AI Python SDK."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = validate_gemini_config(settings)
        self._client = genai.Client(api_key=self._settings.gemini_api_key)

    @property
    def model_name(self) -> str:
        return self._settings.gemini_model

    async def generate_sales_reply(
        self,
        message: str,
        history: list[ChatHistoryItem],
        lead: Lead | None = None,
        rag_chunks: list[dict] | None = None,
        sentiment: SentimentAnalysisResult | None = None,
        booking_context: str | None = None,
    ) -> str:
        """Send conversation context, lead profile, sentiment, booking, and RAG chunks to Gemini."""
        contents = build_gemini_contents(
            history=history,
            latest_message=message,
            max_turns=self._settings.max_history_turns,
        )

        config = types.GenerateContentConfig(
            system_instruction=build_lead_aware_system_instruction(
                lead=lead,
                rag_chunks=rag_chunks,
                sentiment=sentiment,
                booking_context=booking_context,
            ),
            temperature=0.7,
            max_output_tokens=512,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._settings.gemini_model,
                    contents=contents,
                    config=config,
                ),
                timeout=self._settings.gemini_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise GeminiTimeoutError(
                "The AI assistant took too long to respond. Please try again."
            ) from exc
        except genai_errors.APIError as exc:
            status_code = getattr(exc, "code", None)
            if status_code in (401, 403):
                raise GeminiConfigError(
                    "AI service authentication failed. Please check the backend API configuration."
                ) from exc
            if status_code == 404:
                raise GeminiModelError(
                    "The configured AI model is currently unavailable."
                ) from exc
            if status_code == 429:
                raise GeminiRateLimitError(
                    "AI service rate limit reached. Please wait a moment and try again."
                ) from exc
            raise GeminiServiceError(
                "The AI service encountered an error while generating a response."
            ) from exc
        except Exception as exc:
            raise GeminiServiceError(
                "Unable to reach the AI service right now. Please try again shortly."
            ) from exc

        reply_text = (getattr(response, "text", None) or "").strip()
        if not reply_text:
            raise GeminiEmptyResponseError(
                "The AI assistant returned an empty response. Please try rephrasing your message."
            )

        return reply_text

    async def _call_extraction_once(self, prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=LEAD_EXTRACTION_SYSTEM_INSTRUCTION,
            temperature=0.1,
            max_output_tokens=800,
            response_mime_type="application/json",
            response_schema=LeadExtractionResult,
        )
        response = await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=config,
            ),
            timeout=self._settings.gemini_timeout_seconds,
        )
        return (getattr(response, "text", None) or "").strip()

    async def extract_lead_updates(
        self,
        message: str,
        assistant_reply: str,
        existing_lead: Lead | None,
    ) -> LeadExtractionResult | None:
        """Extract and validate structured lead updates with at most one controlled retry."""
        base_prompt = (
            f"{format_lead_context(existing_lead)}\n\n"
            f"Latest Customer Message:\n{message.strip()}\n\n"
            f"Assistant Reply:\n{assistant_reply.strip()}"
        )

        # Attempt 1 + at most 1 controlled retry if JSON is invalid/incomplete.
        for attempt in range(2):
            prompt = (
                base_prompt
                if attempt == 0
                else f"{base_prompt}\n\nIMPORTANT: Return ONLY a complete, valid JSON object."
            )
            try:
                raw_text = await self._call_extraction_once(prompt)
            except Exception:
                return None

            validated = parse_extraction_json(raw_text)
            if validated is not None:
                return validated

        return None
