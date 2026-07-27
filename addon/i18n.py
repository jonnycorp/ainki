"""
Localization for the add-on's own UI text (plain dicts, no deps).
Follows Anki's language unless overridden; missing keys fall back to English,
then to the key name, so a gap never crashes or shows blank.
"""

from . import config

_DEFAULT = "en"

CATALOG = {
    "en": {
        # menu / entry
        "menu.settings": "ainki Settings",
        "hotkey.conflict": (
            "ainki: hotkey '{hotkey}' clashes with Anki's reviewer key '{conflict}' — it "
            "may not fire reliably. Change it in the add-on config."
        ),
        # errors (llm / generation)
        "err.bad_key": "Invalid or expired API key. Check it in the add-on config.",
        "err.rate_limit": "Rate limited by the API. Wait a moment and try again.",
        "err.api_detail": "API error ({code}): {detail}",
        "err.api": "API error ({code}).",
        "err.network": "Network error reaching the API: {reason}",
        "err.timeout": "The request timed out. Check your connection and retry.",
        "err.empty": "The model returned an empty response.",
        "err.no_key": "No API key set. Add your key in the add-on config.",
        "err.unknown_provider": "Unknown provider '{name}'. Set 'provider' in the add-on config.",
        "err.bad_format": "The model returned an unexpected format.",
        "err.no_sentences": "The model returned no usable sentences.",
        "err.field_not_found": (
            "Field '{field}' not found on note type '{note_type}'.\n\n"
            "Available fields: {fields}\n\n"
            "Configure field mappings in the add-on settings."
        ),
        "err.target_not_found": (
            "Target field '{field}' not found on note type '{note_type}'.\n\n"
            "Available fields: {fields}\n\n"
            "Configure field mappings in the add-on settings."
        ),
        # generation dialog
        "dlg.title": "AI Sentence Generator",
        "dlg.note_type": "Note type: <b>{name}</b>",
        "dlg.vocab_word": "Vocab word:",
        "dlg.target_field": "Adds to: <b>{field}</b>",
        "dlg.select_hint": "Click to toggle a sentence, Shift for a range.",
        "dlg.list_tooltip": "Double-click to edit a sentence · right-click to revert it.",
        "dlg.generate": "Generate",
        "dlg.generate_more": "Generate More",
        "dlg.select_all": "Select all",
        "dlg.add_to_card": "Add to Card",
        "dlg.cancel": "Cancel",
        "dlg.enter_vocab": "Enter a vocab word to generate sentences for.",
        "dlg.generating": "Generating sentences…",
        "dlg.revert": "Revert to original",
        # settings dialog
        "set.title": "ainki Settings",
        "set.tab_general": "General",
        "set.tab_api": "API Key",
        "set.donate": "Buy me a coffee ☕",
        "set.note_type": "Note type:",
        "set.word_field": "Word field:",
        "set.append_to": "Append sentences to:",
        "set.mode": "Mode:",
        "set.mode_append": "Append to existing content",
        "set.mode_overwrite": "Overwrite the field",
        "set.separator": "Separator (HTML):",
        "set.level": "Learner level:",
        "set.count": "Sentences per generation:",
        "set.font_size": "Sentence font size:",
        "set.style": "Style:",
        "set.style_casual": "Casual / spoken",
        "set.style_polite": "Polite (です/ます)",
        "set.style_news": "Formal / news",
        "set.style_business": "Business",
        "set.style_mixed": "Mixed",
        "set.furigana": "Furigana",
        "set.furigana_off": "Off",
        "set.furigana_ruby": "Ruby (HTML, works on any template)",
        "set.furigana_custom": "Custom wrapper",
        "set.custom_wrapper": "Custom wrapper:",
        "set.api_key": "API key:",
        "set.api_key_note": (
            "<span style='color:gray;'>Stored in plaintext on disk. "
            "Use a key scoped to this purpose.</span>"
        ),
        "set.provider": "Provider:",
        "set.model": "Model:",
        "set.language": "Language:",
        "set.language_auto": "Auto (follow Anki)",
        "set.restore_defaults": "Restore defaults",
    },
    "ja": {
        "menu.settings": "ainki 設定",
        "hotkey.conflict": (
            "ainki：ホットキー「{hotkey}」がAnkiのレビュー用キー「{conflict}」と競合しています。"
            "正しく動作しない場合があります。アドオン設定で変更してください。"
        ),
        "err.bad_key": "APIキーが無効か期限切れです。アドオン設定で確認してください。",
        "err.rate_limit": "APIのレート制限に達しました。少し待ってから再試行してください。",
        "err.api_detail": "APIエラー（{code}）：{detail}",
        "err.api": "APIエラー（{code}）。",
        "err.network": "APIへの接続中にネットワークエラーが発生しました：{reason}",
        "err.timeout": "リクエストがタイムアウトしました。接続を確認して再試行してください。",
        "err.empty": "モデルが空の応答を返しました。",
        "err.no_key": "APIキーが設定されていません。アドオン設定でキーを追加してください。",
        "err.unknown_provider": "不明なプロバイダー「{name}」です。アドオン設定でプロバイダーを設定してください。",
        "err.bad_format": "モデルが予期しない形式を返しました。",
        "err.no_sentences": "モデルが使用可能な文を返しませんでした。",
        "err.field_not_found": (
            "フィールド「{field}」がノートタイプ「{note_type}」に見つかりません。\n\n"
            "利用可能なフィールド：{fields}\n\n"
            "アドオン設定でフィールドの対応を設定してください。"
        ),
        "err.target_not_found": (
            "追加先フィールド「{field}」がノートタイプ「{note_type}」に見つかりません。\n\n"
            "利用可能なフィールド：{fields}\n\n"
            "アドオン設定でフィールドの対応を設定してください。"
        ),
        "dlg.title": "AI例文ジェネレーター",
        "dlg.note_type": "ノートタイプ：<b>{name}</b>",
        "dlg.vocab_word": "単語：",
        "dlg.target_field": "追加先：<b>{field}</b>",
        "dlg.select_hint": "クリックで選択を切り替え、Shiftで範囲選択。",
        "dlg.list_tooltip": "ダブルクリックで編集・右クリックで元に戻す。",
        "dlg.generate": "生成",
        "dlg.generate_more": "さらに生成",
        "dlg.select_all": "すべて選択",
        "dlg.add_to_card": "カードに追加",
        "dlg.cancel": "キャンセル",
        "dlg.enter_vocab": "例文を生成する単語を入力してください。",
        "dlg.generating": "例文を生成中…",
        "dlg.revert": "元に戻す",
        "set.title": "ainki 設定",
        "set.tab_general": "一般",
        "set.tab_api": "APIキー",
        "set.donate": "開発者を応援する ☕",
        "set.note_type": "ノートタイプ：",
        "set.word_field": "単語フィールド：",
        "set.append_to": "例文の追加先：",
        "set.mode": "モード：",
        "set.mode_append": "既存の内容に追加",
        "set.mode_overwrite": "フィールドを上書き",
        "set.separator": "区切り（HTML）：",
        "set.level": "学習レベル：",
        "set.count": "1回の生成数：",
        "set.font_size": "文の文字サイズ：",
        "set.style": "文体：",
        "set.style_casual": "カジュアル（話し言葉）",
        "set.style_polite": "丁寧（です・ます）",
        "set.style_news": "硬め・ニュース",
        "set.style_business": "ビジネス",
        "set.style_mixed": "ミックス",
        "set.furigana": "ふりがな",
        "set.furigana_off": "なし",
        "set.furigana_ruby": "ルビ（HTML・どのテンプレートでも動作）",
        "set.furigana_custom": "カスタム書式",
        "set.custom_wrapper": "カスタム書式：",
        "set.api_key": "APIキー：",
        "set.api_key_note": (
            "<span style='color:gray;'>キーはディスクに平文で保存されます。"
            "用途を限定したキーを使用してください。</span>"
        ),
        "set.provider": "プロバイダー：",
        "set.model": "モデル：",
        "set.language": "言語：",
        "set.language_auto": "自動（Ankiに従う）",
        "set.restore_defaults": "デフォルトに戻す",
    },
}


def _detect_anki_lang() -> str:
    """Anki's active UI language as a base code (e.g. 'ja' from 'ja_JP')."""
    code = None
    try:
        from anki.lang import current_lang

        code = current_lang
    except Exception:
        code = None
    if not code:
        try:
            from aqt import mw

            code = mw.pm.meta.get("defaultLang")
        except Exception:
            code = None
    if not code:
        return _DEFAULT
    return code.replace("-", "_").split("_")[0].lower()


def resolve_lang(code: str) -> str:
    """An override code → a concrete language ('auto' resolves to Anki's)."""
    if code and code != "auto":
        return code
    return _detect_anki_lang()


def current_lang() -> str:
    """The language the add-on should render in: the config override, or Anki's."""
    return resolve_lang(config.get_language())


def translate(key: str, lang: str, **kwargs) -> str:
    """Translate `key` into an explicit language (used for live preview, where
    the chosen language isn't saved yet). Interpolates only when kwargs are
    passed, so plain strings can safely contain literal braces."""
    text = CATALOG.get(lang, {}).get(key) or CATALOG[_DEFAULT].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def tr(key: str, **kwargs) -> str:
    """Translate `key` for the active language."""
    return translate(key, current_lang(), **kwargs)
