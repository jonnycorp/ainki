"""
Config layer. Wraps Anki's built-in addonManager so the rest of the code
doesn't have to know about it.
"""

import os

from aqt import mw


def _pkg() -> str:
    """The add-on's package name as Anki sees it (the folder name in addons21/)."""
    return __name__.split(".")[0]


def _raw() -> dict:
    return mw.addonManager.getConfig(_pkg()) or {}


def _save(cfg: dict) -> None:
    mw.addonManager.writeConfig(_pkg(), cfg)


def get_hotkey() -> str:
    return _raw().get("hotkey", "Ctrl+E")


# --- providers --------------------------------------------------------------

# Per-provider defaults, also the source of truth for which providers exist.
# `base_url` is "" for providers whose endpoint is fixed (anthropic, google).
PROVIDER_DEFAULTS = {
    "anthropic": {"model": "claude-haiku-4-5", "api_key": "", "base_url": ""},
    "openai": {"model": "gpt-4o-mini", "api_key": "", "base_url": "https://api.openai.com/v1"},
    "google": {"model": "gemini-2.0-flash", "api_key": "", "base_url": ""},
    "openai_compatible": {"model": "", "api_key": "", "base_url": ""},
}

# Per-provider env-var fallback for the key (dev/testing convenience; only
# inherited when Anki is launched from the terminal that exported it).
_PROVIDER_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def get_active_provider() -> str:
    raw = _raw()
    # Fall back to the legacy flat "provider" key for pre-multi-provider installs.
    return raw.get("active_provider") or raw.get("provider", "anthropic")


# Backwards-compatible alias.
def get_provider_name() -> str:
    return get_active_provider()


def get_provider_config(name: str) -> dict:
    """Effective {model, api_key, base_url} for a provider.

    Order for the key: stored slot → legacy flat key (anthropic only, for
    pre-multi-provider installs) → env var. Never log the result.
    """
    raw = _raw()
    cfg = dict(PROVIDER_DEFAULTS.get(name, {"model": "", "api_key": "", "base_url": ""}))
    stored = (raw.get("providers") or {}).get(name, {})
    cfg.update({k: v for k, v in stored.items() if v is not None})

    key = cfg.get("api_key", "")
    if not key and name == "anthropic":
        key = raw.get("api_key", "")  # legacy migration
    if not key and name in _PROVIDER_ENV:
        key = os.environ.get(_PROVIDER_ENV[name], "")
    cfg["api_key"] = key
    return cfg


def all_providers_config() -> dict:
    """Every provider's stored config (for the settings dialog to stage)."""
    return {name: get_provider_config(name) for name in PROVIDER_DEFAULTS}


def get_raw_api_key(name: str) -> str:
    """A provider's stored key only (no env fallback) — for prefilling the
    settings field, so an env-supplied secret is never rendered into the UI."""
    stored = (_raw().get("providers") or {}).get(name, {}).get("api_key", "")
    if not stored and name == "anthropic":
        stored = _raw().get("api_key", "")  # legacy
    return stored


def get_model() -> str:
    return get_provider_config(get_active_provider())["model"]


def get_api_key() -> str:
    """Active provider's key (stored → legacy → env). Never log this value."""
    return get_provider_config(get_active_provider())["api_key"]


def get_level() -> str:
    """Learner level injected into the prompt (free text, e.g. 'intermediate' or 'N4')."""
    return _raw().get("level", "intermediate")


def get_num_sentences() -> int:
    return _raw().get("num_sentences", 5)


def get_write_mode() -> str:
    """How a chosen sentence lands in the target field: 'append' or 'overwrite'."""
    return _raw().get("write_mode", "append")


def get_append_separator() -> str:
    """HTML inserted between accumulated sentences. Anki fields are HTML, so the
    default is '<br>' (a literal '\\n' would not render as a line break)."""
    return _raw().get("append_separator", "<br>")


def get_donation_url() -> str:
    """Optional support/donation link shown in settings. Blank by default."""
    return _raw().get("donation_url", "")


def get_furigana_mode() -> str:
    """How readings are rendered on non-target kanji: 'off', 'ruby', or 'custom'."""
    return _raw().get("furigana_mode", "ruby")


def get_furigana_template() -> str:
    """Wrapper used when furigana_mode == 'custom'. Placeholders: {kanji}, {reading}."""
    return _raw().get("furigana_template", "{kanji}[{reading}]")


def get_mapping(note_type_name: str) -> dict:
    """
    Return {source, target} field mapping for a note type.
    Falls back to default_mapping if this note type isn't configured.
    """
    cfg = _raw()
    mappings = cfg.get("field_mappings", {})
    if note_type_name in mappings:
        return mappings[note_type_name]
    return cfg.get("default_mapping", {"source": "Front", "target": "Back"})


def set_mapping(note_type_name: str, source: str, target: str) -> None:
    cfg = _raw()
    cfg.setdefault("field_mappings", {})[note_type_name] = {
        "source": source,
        "target": target,
    }
    _save(cfg)


def has_mapping(note_type_name: str) -> bool:
    """True if user has explicitly configured this note type."""
    return note_type_name in _raw().get("field_mappings", {})


def all_mappings() -> dict:
    """All explicit per-note-type mappings: {note_type: {source, target}}."""
    return dict(_raw().get("field_mappings", {}))


def remove_mapping(note_type_name: str) -> None:
    cfg = _raw()
    cfg.get("field_mappings", {}).pop(note_type_name, None)
    _save(cfg)


def save_settings(updates: dict) -> None:
    """Merge `updates` into the config and persist in a single write."""
    cfg = _raw()
    cfg.update(updates)
    _save(cfg)
