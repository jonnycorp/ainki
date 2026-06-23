"""
BYOK LLM client. Provider-agnostic by design — `get_provider()` is the single
swap seam, so new providers slot in without the dialog or trigger knowing which
one is active.

Talks to the API with stdlib `urllib` only. The official SDKs pull in heavy,
platform-specific dependencies (httpx, pydantic-core) that can't ship cleanly
inside the add-on zip, so we hand-roll the request instead (CLAUDE.md hard
constraint #1).

The API key is plaintext BYOK config. Never log it, never put it in a URL.
"""

import json
import urllib.error
import urllib.request

from . import config
from .i18n import tr


class LLMError(Exception):
    """User-facing failure. The dialog catches this and shows the message."""


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT_SECONDS = 30
_MAX_TOKENS = 2048


class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, max_tokens: int = _MAX_TOKENS) -> str:
        """Single-turn completion. Returns the joined text of the response."""
        payload = json.dumps(
            {
                "model": self._model,
                "max_tokens": max_tokens,
                # No `thinking`: it's off by default on current models and adds
                # latency we don't want mid-review. (`budget_tokens` would 400.)
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            ANTHROPIC_URL,
            data=payload,
            method="POST",
            headers={
                "content-type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            raise _http_error(err) from err
        except urllib.error.URLError as err:
            raise LLMError(tr("err.network", reason=err.reason)) from err
        except TimeoutError as err:
            raise LLMError(tr("err.timeout")) from err

        return _extract_text(body)


def _http_error(err: urllib.error.HTTPError) -> LLMError:
    """Map an HTTP failure to a clear, key-safe message."""
    if err.code == 401:
        return LLMError(tr("err.bad_key"))
    if err.code == 429:
        return LLMError(tr("err.rate_limit"))

    # For 400 and other codes, surface the provider's own message when present.
    detail = ""
    try:
        parsed = json.loads(err.read().decode("utf-8"))
        detail = parsed.get("error", {}).get("message", "")
    except (ValueError, AttributeError, OSError):
        pass
    if detail:
        return LLMError(tr("err.api_detail", code=err.code, detail=detail))
    return LLMError(tr("err.api", code=err.code))


def _extract_text(body: dict) -> str:
    blocks = body.get("content", [])
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    if not text.strip():
        raise LLMError(tr("err.empty"))
    return text


def get_provider():
    """Build the configured provider. The one place new providers are added."""
    name = config.get_provider_name()
    if name == "anthropic":
        api_key = config.get_api_key()
        if not api_key:
            raise LLMError(tr("err.no_key"))
        return AnthropicProvider(api_key=api_key, model=config.get_model())
    raise LLMError(tr("err.unknown_provider", name=name))
