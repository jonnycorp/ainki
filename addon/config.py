"""config layer over Anki's addonManager"""

from aqt import mw


def _pkg() -> str:
    """add-on package name, like the marketplace code"""
    return __name__.split(".")[0]

def _raw() -> dict:
    """raw current config dict, or {} if failed somehow"""
    return mw.addonManager.getConfig(_pkg()) or {}

def _save(cfg: dict) -> None:
    """update the config dict in Anki's addonManager"""
    mw.addonManager.writeConfig(_pkg(), cfg)


def get_hotkey() -> str:
    """the hotkey, default is Ctrl+Shift+E"""
    return _raw().get("hotkey")

def get_language() -> str:
    """add-on language"""
    return _raw().get("language")

def get_provider_name() -> str:
    """AI provider, currently only 'anthropic' is supported"""
    return _raw().get("provider")

def get_model() -> str:
    """AI model, currently only Anthropic's Claude is supported"""
    return _raw().get("model")

def get_api_key() -> str:
    """user inputted BYOK"""
    return _raw().get("api_key")

def get_level() -> str:
    """language level"""
    return _raw().get("level")

def get_num_sentences() -> int:
    """number of sentences to generate"""
    return _raw().get("num_sentences")

def get_style() -> str:
    """style of the generated sentences"""
    return _raw().get("style")

def get_sentence_length() -> str:
    """'short', 'medium', or 'long'"""
    return _raw().get("sentence_length")

def get_sentence_font_size() -> int:
    """font size of the generated sentences"""
    return _raw().get("sentence_font_size")

def get_write_mode() -> str:
    """how the sentence gets added to the field"""
    return _raw().get("write_mode")

def get_append_separator() -> str:
    """separator between sentences like newline"""
    return _raw().get("append_separator")

def get_furigana_mode() -> str:
    """the html display mode like ruby"""
    return _raw().get("furigana_mode")

def get_furigana_template() -> str:
    """display template"""
    return _raw().get("furigana_template")

def get_donation_url() -> str:
    """Donation URL :D"""
    return "https://ko-fi.com/yunjay"

def get_mapping(note_type_name: str) -> dict:
    cfg = _raw()
    mappings = cfg.get("field_mappings") or {}
    if note_type_name in mappings:
        return mappings[note_type_name]
    return cfg.get("default_mapping") or {}

def get_usage() -> dict:
    """lifetime tally of what generation has cost"""
    return _raw().get("usage") or {}

def add_usage(sentences: int, tokens: int, cost) -> None:
    """fold one generation into the lifetime tally, cost is None for unpriced models"""
    cfg = _raw()
    u = cfg.get("usage") or {}
    u["sentences"] = u.get("sentences", 0) + sentences
    u["tokens"] = u.get("tokens", 0) + tokens
    if cost is not None:
        u["cost"] = round(u.get("cost", 0.0) + cost, 6)
    cfg["usage"] = u
    _save(cfg)

def all_mappings() -> dict:
    return dict(_raw().get("field_mappings") or {})


def save_settings(updates: dict) -> None:
    cfg = _raw()
    cfg.update(updates)
    _save(cfg)

def defaults() -> dict:
    try:
        return mw.addonManager.addonConfigDefaults(_pkg()) or {}
    except Exception:
        return {}
