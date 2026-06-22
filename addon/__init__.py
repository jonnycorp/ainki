"""
Entry point. Registers the hotkey on the Reviewer window.

- Anki uses a hook system (`gui_hooks`). We attach to reviewer lifecycle
  hooks to install a QShortcut bound to the reviewer's web view.
- The shortcut only fires during review, not in browser/editor.
"""

from aqt import mw, gui_hooks
from aqt.qt import QShortcut, QKeySequence, QAction, qconnect
from aqt.utils import showWarning
from anki.utils import html_to_text_line

from . import config
from .ui.sentence_dialog import SentenceDialog


# Keep a reference so the QShortcut isn't garbage collected
_shortcut_ref = None


def _on_hotkey():
    """Fired when the user presses the configured hotkey during review."""
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
            f"Field '{source_field}' not found on note type '{note_type_name}'.\n\n"
            f"Available fields: {', '.join(note.keys())}\n\n"
            "Configure field mappings in the add-on settings."
        )
        return

    vocab_word = html_to_text_line(note[source_field].strip())

    dialog = SentenceDialog(
        parent=mw,
        vocab_word=vocab_word,
        note_type_name=note_type_name,
        mapping_is_default=not config.has_mapping(note_type_name),
        note=note,
        target_field=mapping["target"],
    )
    dialog.exec()


def _install_shortcut(_card):
    """Install the shortcut on the reviewer web view once it's ready."""
    global _shortcut_ref
    if _shortcut_ref is not None:
        return

    hotkey = config.get_hotkey()
    _shortcut_ref = QShortcut(QKeySequence(hotkey), mw.reviewer.web)
    _shortcut_ref.activated.connect(_on_hotkey)


gui_hooks.reviewer_did_show_question.append(_install_shortcut)
gui_hooks.reviewer_did_show_answer.append(_install_shortcut)


def _open_settings():
    # Imported lazily: building the dialog enumerates note types, which needs a
    # loaded collection (guaranteed once a profile is open).
    from .ui.settings_dialog import SettingsDialog

    SettingsDialog(parent=mw).exec()


# Tools → ainki Settings, plus the add-on's Config button → same dialog.
_settings_action = QAction("ainki Settings", mw)
qconnect(_settings_action.triggered, _open_settings)
mw.form.menuTools.addAction(_settings_action)
mw.addonManager.setConfigAction(__name__, _open_settings)
