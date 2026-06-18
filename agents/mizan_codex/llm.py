"""Small LLM provider router for Mizan Codex.

No third-party Python dependencies are required. Providers are selected by
environment and CLI flags. Ollama is the default because it keeps sensitive
filings local on Khalid's Mac.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str


def call_llm(provider: str, model: str, system: str, user: str, timeout: int = 120) -> LLMResponse:
    provider = provider.lower().strip()
    if provider == "stub":
        return LLMResponse(text="", provider="stub", model="deterministic")
    if provider == "ollama":
        return _ollama(model, system, user, timeout)
    if provider == "gemini":
        return _gemini(model, system, user, timeout)
    if provider == "groq":
        return _openai_compatible(
            provider="groq",
            model=model,
            system=system,
            user=user,
            api_key=os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1/chat/completions",
            timeout=timeout,
        )
    if provider == "openrouter":
        return _openai_compatible(
            provider="openrouter",
            model=model,
            system=system,
            user=user,
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1/chat/completions",
            timeout=timeout,
            extra_headers={
                "HTTP-Referer": "http://localhost/uae-stocks-intelligence",
                "X-Title": "UAE Stocks Intelligence - Mizan Codex",
            },
        )
    raise LLMError(f"Unknown provider: {provider}")


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"HTTP {exc.code} from {url}: {body[:700]}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"Could not reach {url}: {exc.reason}") from exc


def _ollama(model: str, system: str, user: str, timeout: int) -> LLMResponse:
    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": 0.15, "num_ctx": 8192},
    }
    result = _post_json(f"{base}/api/chat", payload, timeout=timeout)
    text = result.get("message", {}).get("content", "")
    if not text:
        raise LLMError("Ollama returned no message content")
    return LLMResponse(text=text, provider="ollama", model=model)


def _gemini(model: str, system: str, user: str, timeout: int) -> LLMResponse:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set")
    model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.15, "responseMimeType": "application/json"},
    }
    result = _post_json(url, payload, timeout=timeout)
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected Gemini response: {json.dumps(result)[:700]}") from exc
    return LLMResponse(text=text, provider="gemini", model=model)


def _openai_compatible(
    provider: str,
    model: str,
    system: str,
    user: str,
    api_key: str,
    base_url: str,
    timeout: int,
    extra_headers: dict[str, str] | None = None,
) -> LLMResponse:
    if not api_key:
        raise LLMError(f"{provider.upper()} API key is not set")
    payload = {
        "model": model,
        "temperature": 0.15,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", **(extra_headers or {})}
    result = _post_json(base_url, payload, headers=headers, timeout=timeout)
    try:
        text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected {provider} response: {json.dumps(result)[:700]}") from exc
    return LLMResponse(text=text, provider=provider, model=model)
