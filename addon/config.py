"""config layer over Anki's addonManager"""

from aqt import mw


"""add-on package name, like the marketplace code"""
def _pkg() -> str:
    return __name__.split(".")[0]

"""raw current config dict, or {} if failed somehow"""
def _raw() -> dict:
    return mw.addonManager.getConfig(_pkg()) or {}

"""update the config dict in Anki's addonManager"""
def _save(cfg: dict) -> None:
    mw.addonManager.writeConfig(_pkg(), cfg)

"""the hotkey, default is Ctrl+Shift+E"""
def get_hotkey() -> str:
    return _raw().get("hotkey")

"""add-on language"""
def get_language() -> str:
    return _raw().get("language")

"""AI provider, currently only 'anthropic' is supported"""
def get_provider_name() -> str:
    return _raw().get("provider")

"""AI model, currently only Anthropic's Claude is supported"""
def get_model() -> str:
    return _raw().get("model")

"""user inputted BYOK"""
def get_api_key() -> str:
    return _raw().get("api_key")

"""language level"""
def get_level() -> str:
    return _raw().get("level")

"""number of sentences to generate"""
def get_num_sentences() -> int:
    return _raw().get("num_sentences")

"""style of the generated sentences"""
def get_style() -> str:
    return _raw().get("style")

"""font size of the generated sentences"""
def get_sentence_font_size() -> int:
    return _raw().get("sentence_font_size")

"""how the sentence gets added to the field"""
def get_write_mode() -> str:
    return _raw().get("write_mode")

"""separator between sentences like newline"""
def get_append_separator() -> str:
    return _raw().get("append_separator")

"""the html display mode like ruby"""
def get_furigana_mode() -> str:
    return _raw().get("furigana_mode")

"""display template"""
def get_furigana_template() -> str:
    return _raw().get("furigana_template")

"""Donation URL :D"""
def get_donation_url() -> str:
    return "https://ko-fi.com/yunjay"

def get_mapping(note_type_name: str) -> dict:
    cfg = _raw()
    mappings = cfg.get("field_mappings") or {}
    if note_type_name in mappings:
        return mappings[note_type_name]
    return cfg.get("default_mapping") or {}

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
