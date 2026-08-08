"""
llm client, thin wrapper around provider API, only Anthropic for now
"""

import json
import urllib.error
import urllib.request

from . import config
from .i18n import tr


class LLMError(Exception):
    """user-facing failure, dialog catches and shows the message"""


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT_SECONDS = 60
_MAX_TOKENS = 2048

_PRICING = {
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-4-5": (3.00, 15.00),
}


def cost_usd(input_tokens: int, output_tokens: int, model: str):
    """usd for one call, or None when we have no price for the model"""
    rate = _PRICING.get(model)
    if rate is None:
        return None
    return (input_tokens * rate[0] + output_tokens * rate[1]) / 1_000_000


class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, max_tokens: int = _MAX_TOKENS) -> tuple:
        """single turn completion, returns (text, usage)

        thinking is disabled explicitly, not by omission: newer models default it
        on and it shares the max_tokens budget, which truncates the json
        """
        payload = json.dumps(
            {
                "model": self._model,
                "max_tokens": max_tokens,
                "thinking": {"type": "disabled"},
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

        return _extract_text(body), body.get("usage") or {}

def _http_error(err: urllib.error.HTTPError) -> LLMError:
    if err.code == 401:
        return LLMError(tr("err.bad_key"))
    if err.code == 429:
        return LLMError(tr("err.rate_limit"))

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
    name = config.get_provider_name()
    if name == "anthropic":
        api_key = config.get_api_key()
        if not api_key:
            raise LLMError(tr("err.no_key"))
        return AnthropicProvider(api_key=api_key, model=config.get_model())
    raise LLMError(tr("err.unknown_provider", name=name))
