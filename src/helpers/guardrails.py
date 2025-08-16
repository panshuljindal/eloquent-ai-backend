from __future__ import annotations
import functools
import html
import re
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from guardrails import Guard
from pydantic import BaseModel


class AssistantOutput(BaseModel):
    answer: str


class GuardrailsHelper:
    """Security guardrails for inputs, context, and model outputs."""

    _INJECTION_PATTERNS = [
        r"ignore\s+(all|any|previous)\s+instructions",
        r"disregard\s+previous\s+instructions",
        r"system\s+prompt",
        r"you\s+are\s+chatgpt",
        r"override\s+the\s+(rules|instructions)",
        r"act\s+as\s+an?\s+(.+)",
    ]

    _EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    _PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b")
    _SECRET_RES = [
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"ghp_[A-Za-z0-9]{36}"),
        re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
        re.compile(r"AIzaSy[0-9A-Za-z\-_]{35}"),
    ]

    def __init__(self) -> None:
        self._guard = Guard

    def validate_text(self, text: str) -> Tuple[bool, str]:
        if self._looks_like_injection(text):
            return False, "Possible prompt injection detected"
        for regex in self._SECRET_RES:
            if regex.search(text):
                return False, "Possible secret detected"
        return True, "OK"

    def sanitize_user_text(self, text: str) -> Tuple[bool, str]:
        ok, reason = self.validate_text(text)
        if not ok:
            return False, reason
        redacted = self._redact_pii_and_secrets(text)
        return True, redacted

    def validate_output(self, text: str) -> AssistantOutput:
        candidate = text.strip()
        try:
            import json
            data = json.loads(candidate)
            if isinstance(data, dict) and "answer" in data and isinstance(data["answer"], str):
                answer = data["answer"]
            else:
                answer = candidate
        except Exception:
            answer = candidate
        answer = self._strip_active_content(answer)
        answer = self._redact_pii_and_secrets(answer)
        return AssistantOutput(answer=answer)

    def _looks_like_injection(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(pat, lowered) for pat in self._INJECTION_PATTERNS)

    def _strip_active_content(self, text: str) -> str:
        without_scripts = re.sub(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", " ", text, flags=re.I | re.S)
        without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
        return html.unescape(without_tags)

    def _redact_pii_and_secrets(self, text: str) -> str:
        redacted = self._EMAIL_RE.sub("[redacted-email]", text)
        redacted = self._PHONE_RE.sub("[redacted-phone]", redacted)
        for regex in self._SECRET_RES:
            redacted = regex.sub("[redacted-secret]", redacted)
        return redacted

@functools.lru_cache(maxsize=1)
def get_guardrails_helper() -> GuardrailsHelper:
    return GuardrailsHelper()


