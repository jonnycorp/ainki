"""
Config layer. Wraps Anki's built-in addonManager so the rest of the code
doesn't have to know about it.
"""

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
