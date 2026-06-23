"""
Lightweight localization for the add-on's own UI text.

Selection is automatic: by default we follow Anki's UI language. A "language"
config override ("auto" | "en" | "ja" | ...) lets a user pin the add-on to a
different language than Anki itself. Missing keys/languages fall back to English,
then to the key name, so a gap never crashes or shows blank.

Only the add-on's chrome is localized — the generated Japanese sentences are
content and stay untouched. Dependency-free (plain dicts), per CLAUDE.md.

Japanese strings here are an initial draft and want a native-speaker pass before
shipping.
"""

from . import config

_DEFAULT = "en"

CATALOG = {
    "en": {
        # menu / entry
        "menu.settings": "ainki Settings",
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
        "dlg.default_mapping": (
            ' <span style="color:#c80;">(using default field mapping — configure in settings)</span>'
        ),
        "dlg.vocab_word": "Vocab word:",
        "dlg.select_hint": "Select one or more (click, Ctrl-click, Shift-range; double-click to edit):",
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
        "set.intro": "<b>ainki</b> — AI example sentences for your reviews.",
        "set.support": "Support",
        "set.support_coming": "<span style='color:gray;'>(support link coming soon)</span>",
        "set.donate": "Buy me a coffee ☕",
        "set.field_mapping": "Field mapping",
        "set.note_type": "Note type:",
        "set.word_field": "Word field:",
        "set.append_to": "Append sentences to:",
        "set.when_adding": "When adding a sentence",
        "set.mode": "Mode:",
        "set.mode_append": "Append to existing content",
        "set.mode_overwrite": "Overwrite the field",
        "set.separator": "Separator (HTML):",
        "set.separator_hint": "<span style='color:gray;'>Fields are HTML — use &lt;br&gt; for a line break.</span>",
        "set.generation": "Generation",
        "set.level": "Learner level:",
        "set.count": "Sentences per generation:",
        "set.furigana": "Furigana",
        "set.furigana_off": "Off",
        "set.furigana_ruby": "Ruby (HTML, works on any template)",
        "set.furigana_custom": "Custom wrapper",
        "set.custom_wrapper": "Custom wrapper:",
        "set.furigana_hint": (
            "<span style='color:gray;'>Use {kanji} and {reading}. "
            "e.g. <code>{kanji}[{reading}]</code> or "
            "<code>&lt;ruby&gt;{kanji}&lt;rt&gt;{reading}&lt;/rt&gt;&lt;/ruby&gt;</code>. "
            "The target word is always left bare.</span>"
        ),
        "set.api_key": "API key:",
        "set.api_key_note": (
            "<span style='color:gray;'>Stored in plaintext on disk. "
            "Use a key scoped to this purpose.</span>"
        ),
        "set.provider": "Provider:",
        "set.model": "Model:",
        "set.language": "Language:",
        "set.language_auto": "Auto (follow Anki)",
    },
    # --- Japanese (draft — needs native-speaker review) ---------------------
    "ja": {
        "menu.settings": "ainki 設定",
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
        "dlg.default_mapping": (
            ' <span style="color:#c80;">（デフォルトのフィールド対応を使用中 — 設定で変更できます）</span>'
        ),
        "dlg.vocab_word": "単語：",
        "dlg.select_hint": "1つ以上選択してください（クリック、Ctrl+クリック、Shift+範囲選択／ダブルクリックで編集）：",
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
        "set.intro": "<b>ainki</b> — レビュー用のAI例文。",
        "set.support": "サポート",
        "set.support_coming": "<span style='color:gray;'>（サポートリンクは近日公開）</span>",
        "set.donate": "開発者を応援する ☕",
        "set.field_mapping": "フィールド対応",
        "set.note_type": "ノートタイプ：",
        "set.word_field": "単語フィールド：",
        "set.append_to": "例文の追加先：",
        "set.when_adding": "例文を追加するとき",
        "set.mode": "モード：",
        "set.mode_append": "既存の内容に追加",
        "set.mode_overwrite": "フィールドを上書き",
        "set.separator": "区切り（HTML）：",
        "set.separator_hint": "<span style='color:gray;'>フィールドはHTMLです — 改行には &lt;br&gt; を使います。</span>",
        "set.generation": "生成",
        "set.level": "学習レベル：",
        "set.count": "1回の生成数：",
        "set.furigana": "ふりがな",
        "set.furigana_off": "なし",
        "set.furigana_ruby": "ルビ（HTML・どのテンプレートでも動作）",
        "set.furigana_custom": "カスタム書式",
        "set.custom_wrapper": "カスタム書式：",
        "set.furigana_hint": (
            "<span style='color:gray;'>{kanji} と {reading} を使います。"
            "例：<code>{kanji}[{reading}]</code> または "
            "<code>&lt;ruby&gt;{kanji}&lt;rt&gt;{reading}&lt;/rt&gt;&lt;/ruby&gt;</code>。"
            "対象の単語には常にふりがなを付けません。</span>"
        ),
        "set.api_key": "APIキー：",
        "set.api_key_note": (
            "<span style='color:gray;'>キーはディスクに平文で保存されます。"
            "用途を限定したキーを使用してください。</span>"
        ),
        "set.provider": "プロバイダー：",
        "set.model": "モデル：",
        "set.language": "言語：",
        "set.language_auto": "自動（Ankiに従う）",
    },
}


def _detect_anki_lang() -> str:
    """Anki's active UI language as a base code (e.g. 'ja' from 'ja_JP')."""
    code = None
    try:
        from anki.lang import current_lang  # set to Anki's active language

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


def current_lang() -> str:
    """The language the add-on should render in: the config override, or Anki's."""
    override = config.get_language()
    if override and override != "auto":
        return override
    return _detect_anki_lang()


def tr(key: str, **kwargs) -> str:
    """Translate `key` for the active language, with English then key-name fallback.

    Only interpolates when kwargs are passed, so catalog strings that contain
    literal braces (the furigana hint's {kanji}/{reading}) are left intact.
    """
    lang = current_lang()
    text = CATALOG.get(lang, {}).get(key) or CATALOG[_DEFAULT].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
