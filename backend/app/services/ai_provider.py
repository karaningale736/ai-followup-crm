"""
AI provider abstraction.

The business logic (followup_engine.py) already decided the stage, timing,
template category, tone, and priority. This module ONLY personalizes the
already-selected template's text and classifies inbound replies. It never
makes CRM decisions.

Two implementations:
  - MockAIProvider: deterministic, no network calls -- used automatically
    when GEMINI_API_KEY is not set, and always used in tests.
  - GeminiAIProvider: calls the real Gemini API via google-genai SDK.

Swap in an OpenAI provider later by implementing the same AIProvider
interface.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIProvider(ABC):
    @abstractmethod
    def personalize_email(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Return {"subject": ..., "email_body": ..., "cta": ...}."""

    @abstractmethod
    def classify_response(self, message_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return classification dict per the response classifier spec."""


PLACEHOLDER_PATTERN = re.compile(r"\{(\w+)\}")


class MockAIProvider(AIProvider):
    """
    Deterministic stand-in for Gemini. Fills the approved template's
    placeholders from the supplied context and leaves an explicit
    "[MISSING: field]" marker for anything not provided -- it never
    invents facts, prices, or dates, matching the AI rules in the spec.
    """

    def personalize_email(self, context: Dict[str, Any]) -> Dict[str, str]:
        template_subject = context.get("template_subject", "")
        template_body = context.get("template_body", "")
        variables: Dict[str, Any] = context.get("variables", {})

        def fill(text: str) -> str:
            def repl(match: "re.Match[str]") -> str:
                key = match.group(1)
                if key in variables and variables[key] not in (None, ""):
                    return str(variables[key])
                return f"[MISSING: {key}]"
            return PLACEHOLDER_PATTERN.sub(repl, text)

        subject = fill(template_subject)
        body = fill(template_body)
        cta = context.get("cta_hint") or "Please let us know your thoughts and how you'd like to proceed."

        return {"subject": subject, "email_body": body, "cta": cta}

    def classify_response(self, message_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = (message_text or "").lower()

        rules = [
            ("declined", "DECLINED", "AGREEMENT_DECLINED" if "agreement" in text else "DECLINED"),
            ("not interested", "NOT_INTERESTED", "DECLINED"),
            ("budget", "BUDGET_CONCERN", "BUDGET_OBJECTION"),
            ("price", "BUDGET_CONCERN", "BUDGET_OBJECTION"),
            ("sign", "READY_TO_SIGN", "AGREEMENT_PENDING_SIGNATURE"),
            ("meeting", "MEETING_REQUEST", "MEETING_REQUESTED"),
            ("call", "MEETING_REQUEST", "MEETING_REQUESTED"),
            ("more information", "NEEDS_MORE_INFORMATION", "INTERESTED"),
            ("more details", "NEEDS_MORE_INFORMATION", "INTERESTED"),
            ("next week", "NEEDS_TIME", "INITIAL_FOLLOW_UP"),
            ("later", "NEEDS_TIME", "INITIAL_FOLLOW_UP"),
            ("interested", "INTERESTED", "INTERESTED"),
            ("agreement", "AGREEMENT_QUESTION", "AGREEMENT_SENT"),
        ]

        for keyword, classification, recommended_stage in rules:
            if keyword in text:
                return {
                    "classification": classification,
                    "confidence": 0.7,
                    "recommended_stage": recommended_stage,
                    "recommended_action": f"Review reply and confirm move to {recommended_stage}.",
                    "reason": f"Keyword match: '{keyword}' found in client reply.",
                }

        if not text.strip():
            return {
                "classification": "NO_RESPONSE",
                "confidence": 0.99,
                "recommended_stage": None,
                "recommended_action": "Continue standard follow-up sequence.",
                "reason": "Empty message body.",
            }

        return {
            "classification": "OTHER",
            "confidence": 0.4,
            "recommended_stage": None,
            "recommended_action": "Manual review recommended -- no confident keyword match.",
            "reason": "No rule matched the reply text.",
        }


class GeminiAIProvider(AIProvider):
    """Real Gemini-backed provider. Only imports google-genai when actually used."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiAIProvider")
        self.model = model
        from google import genai  # imported lazily so tests never need this package
        self._client = genai.Client(api_key=self.api_key)

    def _generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self._client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt}\n\n{user_prompt}",
        )
        text = response.text.strip()
        text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)

    def personalize_email(self, context: Dict[str, Any]) -> Dict[str, str]:
        system_prompt = (
            "You personalize an ALREADY-APPROVED email template. "
            "Never invent facts, prices, discounts, dates, meeting times, deadlines, "
            "company details, client statements, or limited availability. "
            "Use '[MISSING: field]' for any required info not supplied. "
            "Respond ONLY with JSON: {\"subject\": str, \"email_body\": str, \"cta\": str}."
        )
        user_prompt = json.dumps(context)
        try:
            return self._generate_json(system_prompt, user_prompt)
        except Exception:
            # Fail safe to the deterministic mock rather than send a broken email.
            return MockAIProvider().personalize_email(context)

    def classify_response(self, message_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "Classify a client's email reply into exactly one of: INTERESTED, NOT_INTERESTED, "
            "NEEDS_MORE_INFORMATION, BUDGET_CONCERN, NEEDS_TIME, MEETING_REQUEST, "
            "AGREEMENT_QUESTION, READY_TO_SIGN, DECLINED, NO_RESPONSE, OTHER. "
            "Respond ONLY with JSON: {\"classification\": str, \"confidence\": float, "
            "\"recommended_stage\": str|null, \"recommended_action\": str, \"reason\": str}."
        )
        user_prompt = json.dumps({"message": message_text, "context": context})
        try:
            return self._generate_json(system_prompt, user_prompt)
        except Exception:
            return MockAIProvider().classify_response(message_text, context)


def get_ai_provider() -> AIProvider:
    """Factory: real Gemini provider if GEMINI_API_KEY is set, else the mock."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return GeminiAIProvider(api_key=api_key)
        except Exception:
            return MockAIProvider()
    return MockAIProvider()
