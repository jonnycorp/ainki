"""
BYOK LLM client. Provider-agnostic by design — `get_provider()` is the single
swap seam, so the dialog and generation pipeline never know which provider is
active. Each provider speaks `complete(system, user, max_tokens) -> str`.

Talks to every API with stdlib `urllib` only. The official SDKs pull in heavy,
platform-specific dependencies (httpx, pydantic-core) that can't ship cleanly
inside the add-on zip, so we hand-roll the requests (CLAUDE.md hard constraint #1).

The API key is plaintext BYOK config. Never log it, never put it in a URL.
"""

import json
import urllib.error
import urllib.request

from . import config


class LLMError(Exception):
    """User-facing failure. The dialog catches this and shows the message."""


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_TIMEOUT_SECONDS = 30
_MAX_TOKENS = 2048


# --- shared transport -------------------------------------------------------


def _post(url: str, headers: dict, payload: dict) -> dict:
    """POST JSON and return the parsed response, mapping failures to LLMError."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"content-type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise _http_error(err) from err
    except urllib.error.URLError as err:
        raise LLMError(f"Network error reaching the API: {err.reason}") from err
    except TimeoutError as err:
        raise LLMError("The request timed out. Check your connection and retry.") from err


def _http_error(err: urllib.error.HTTPError) -> LLMError:
    """Map an HTTP failure to a clear, key-safe message. Anthropic, OpenAI, and
    Gemini all return {"error": {"message": ...}}, so this is shared."""
    if err.code == 401:
        return LLMError("Invalid or expired API key. Check it in the add-on settings.")
    if err.code == 429:
        return LLMError("Rate limited by the API. Wait a moment and try again.")
    detail = ""
    try:
        parsed = json.loads(err.read().decode("utf-8"))
        detail = parsed.get("error", {}).get("message", "")
    except (ValueError, AttributeError, OSError):
        pass
    return LLMError(f"API error ({err.code}): {detail}" if detail else f"API error ({err.code}).")


def _require(text: str) -> str:
    if not text or not text.strip():
        raise LLMError("The model returned an empty response.")
    return text


# --- providers --------------------------------------------------------------


class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, max_tokens: int = _MAX_TOKENS) -> str:
        body = _post(
            ANTHROPIC_URL,
            {"x-api-key": self._api_key, "anthropic-version": ANTHROPIC_VERSION},
            {
                # No `thinking`: off by default on current models; keeps latency low.
                "model": self._model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        blocks = body.get("content", [])
        return _require("".join(b.get("text", "") for b in blocks if b.get("type") == "text"))


class OpenAIProvider:
    """OpenAI Chat Completions. Also serves any OpenAI-compatible backend
    (OpenRouter, Groq, DeepSeek, Together, local Ollama/LM Studio) via base_url."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self._api_key = api_key
        self._model = model
        self._base_url = (base_url or "").rstrip("/")

    def complete(self, system: str, user: str, max_tokens: int = _MAX_TOKENS) -> str:
        if not self._base_url:
            raise LLMError("No base URL set for this provider. Set it in the add-on settings.")
        body = _post(
            f"{self._base_url}/chat/completions",
            {"authorization": f"Bearer {self._api_key}"},
            {
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        choices = body.get("choices") or []
        text = choices[0].get("message", {}).get("content", "") if choices else ""
        return _require(text)


class GoogleProvider:
    """Google Gemini (generateContent). Key goes in the x-goog-api-key header,
    never the URL."""

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, max_tokens: int = _MAX_TOKENS) -> str:
        body = _post(
            GOOGLE_URL.format(model=self._model),
            {"x-goog-api-key": self._api_key},
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        candidates = body.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return _require("".join(p.get("text", "") for p in parts))


# --- factory ----------------------------------------------------------------


def get_provider():
    """Build the active provider from config. The one place new providers slot in."""
    name = config.get_active_provider()
    pc = config.get_provider_config(name)
    if not pc.get("api_key"):
        raise LLMError(f"No API key set for '{name}'. Add it in the add-on settings.")
    if not pc.get("model"):
        raise LLMError(f"No model set for '{name}'. Set it in the add-on settings.")

    if name == "anthropic":
        return AnthropicProvider(pc["api_key"], pc["model"])
    if name in ("openai", "openai_compatible"):
        return OpenAIProvider(pc["api_key"], pc["model"], pc.get("base_url", ""))
    if name == "google":
        return GoogleProvider(pc["api_key"], pc["model"])
    raise LLMError(f"Unknown provider '{name}'. Set it in the add-on settings.")
