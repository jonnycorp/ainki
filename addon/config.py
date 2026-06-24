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


def get_language() -> str:
    """UI language: 'auto' (follow Anki), or a base code like 'en' / 'ja'."""
    return _raw().get("language", "auto")


def get_provider_name() -> str:
    return _raw().get("provider", "anthropic")


def get_model() -> str:
    return _raw().get("model", "claude-haiku-4-5")


def get_api_key() -> str:
    """
    Plaintext BYOK key. Config value wins; falls back to the ANTHROPIC_API_KEY
    env var (a dev/testing convenience — only inherited when Anki is launched
    from the terminal that exported it). Never log this value.
    """
    return _raw().get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")


def get_raw_api_key() -> str:
    """The configured key only (no env fallback) — for prefilling the settings
    field, so an env-supplied secret is never rendered into the UI."""
    return _raw().get("api_key", "")


def get_level() -> str:
    """Learner level injected into the prompt (free text, e.g. 'intermediate' or 'N4')."""
    return _raw().get("level", "intermediate")


def get_num_sentences() -> int:
    return _raw().get("num_sentences", 5)


def get_style() -> str:
    """Register injected into the prompt: casual / polite / news / business / mixed."""
    return _raw().get("style", "casual")


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


def defaults() -> dict:
    """The add-on's config.json defaults (for 'Restore defaults')."""
    try:
        return mw.addonManager.addonConfigDefaults(_pkg()) or {}
    except Exception:
        return {}
