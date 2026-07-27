"""
Entry point: registers the reviewer hotkey and the settings menu action.
The shortcut is bound once per session — a hotkey change takes effect on restart.
"""

from aqt import mw, gui_hooks
from aqt.qt import QShortcut, QKeySequence, QAction, qconnect
from aqt.utils import showWarning, tooltip
from anki.utils import html_to_text_line

from . import config
from .i18n import tr
from .ui.sentence_dialog import SentenceDialog


# Keep a reference so the QShortcut isn't garbage collected
_shortcut_ref = None
_conflict_checked = False  # warn about a hotkey clash at most once per session


def _on_hotkey():
    reviewer = mw.reviewer
    card = reviewer.card
    if card is None:
        return

    note = card.note()
    note_type_name = note.note_type()["name"]
    mapping = config.get_mapping(note_type_name)
    source_field = mapping["source"]

    if source_field not in note:
        showWarning(
            tr(
                "err.field_not_found",
                field=source_field,
                note_type=note_type_name,
                fields=", ".join(note.keys()),
            )
        )
        return

    vocab_word = html_to_text_line(note[source_field].strip())

    dialog = SentenceDialog(
        parent=mw,
        vocab_word=vocab_word,
        note_type_name=note_type_name,
        note=note,
        target_field=mapping["target"],
    )
    dialog.exec()


def _install_shortcut(_card):
    global _shortcut_ref
    if _shortcut_ref is not None:
        return

    hotkey = config.get_hotkey()
    _shortcut_ref = QShortcut(QKeySequence(hotkey), mw.reviewer.web)
    _shortcut_ref.activated.connect(_on_hotkey)
    _warn_if_hotkey_conflicts(hotkey)


def _conflicting_reviewer_key(hotkey: str):
    """The built-in reviewer key our hotkey collides with, or None."""
    seq = QKeySequence(hotkey)
    try:
        # Entries are (key, callback[, ...]); key is the first item.
        for entry in mw.reviewer._shortcutKeys():
            key = entry[0] if isinstance(entry, (tuple, list)) else entry
            if isinstance(key, str) and QKeySequence(key) == seq:
                return key
    except Exception:
        return None  # private API — fail quiet rather than break review
    return None


def _warn_if_hotkey_conflicts(hotkey: str):
    """Warn only — the user decides; we never block or rebind."""
    global _conflict_checked
    if _conflict_checked:
        return
    _conflict_checked = True
    clash = _conflicting_reviewer_key(hotkey)
    if clash:
        tooltip(tr("hotkey.conflict", hotkey=hotkey, conflict=clash))


gui_hooks.reviewer_did_show_question.append(_install_shortcut)
gui_hooks.reviewer_did_show_answer.append(_install_shortcut)


def _open_settings():
    # Lazy import: the dialog enumerates note types, which needs a loaded collection.
    from .ui.settings_dialog import SettingsDialog

    SettingsDialog(parent=mw).exec()


_settings_action = QAction(tr("menu.settings"), mw)
qconnect(_settings_action.triggered, _open_settings)
mw.form.menuTools.addAction(_settings_action)
mw.addonManager.setConfigAction(__name__, _open_settings)
