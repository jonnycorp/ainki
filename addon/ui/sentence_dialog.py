"""
Popup shown when the hotkey fires during review.

Current features:
- Multi-select; checkbox mirrors selection, can pick with normal click / Ctrl-click / Shift-range
  on the entire row, or just click the checkbox.
    TODO: click commands such as normal and ctrl-click on the row should also deselect it, like a checkbox
    TODO: sentence font should be able to be changed from settings, different devices have different needs

- Double-click to edit a sentence, right-click to revert to original.
    TODO: find place to maybe write this info, create tooltip

- Add to Card appends every selected sentence (in list order) using the configured separator.
    TODO: consider adding at least an indicator on which field is being written to, 
          maybe even a preview of the result, or a way to choose the field right there (might be too much for a popup)
"""

from aqt import mw
from aqt.operations import QueryOp
from aqt.operations.note import update_note
from aqt.qt import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    Qt,
    qconnect,
)
from aqt.utils import showWarning

from .. import config, generation
from ..i18n import tr

_ITEM_FLAGS = (
    Qt.ItemFlag.ItemIsSelectable
    | Qt.ItemFlag.ItemIsEnabled
    | Qt.ItemFlag.ItemIsUserCheckable
    | Qt.ItemFlag.ItemIsEditable
)


class SentenceDialog(QDialog):
    def __init__(
        self,
        parent,
        vocab_word: str,
        note_type_name: str,
        note,
        target_field: str,
    ):
        super().__init__(parent)
        self.note = note
        self.target_field = target_field
        self._items: list[dict] = []  # row-aligned with the list; "jp" is the original
        self._vocab = vocab_word
        self._syncing = False  # guards selection<->checkbox mirroring

        self.setWindowTitle(tr("dlg.title"))
        self.setMinimumWidth(540)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(tr("dlg.note_type", name=note_type_name)))

        layout.addWidget(QLabel(tr("dlg.vocab_word")))
        self.word_input = QLineEdit(vocab_word)
        layout.addWidget(self.word_input)

        layout.addWidget(QLabel(tr("dlg.select_hint")))
        self.sentence_list = QListWidget()
        list_font = self.sentence_list.font()
        list_font.setPointSize(18)
        self.sentence_list.setFont(list_font)
        self.sentence_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.sentence_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        qconnect(self.sentence_list.itemSelectionChanged, self._on_selection_changed)
        qconnect(self.sentence_list.itemChanged, self._on_item_changed)
        qconnect(self.sentence_list.customContextMenuRequested, self._show_context_menu)
        self.sentence_list.setEnabled(False)
        layout.addWidget(self.sentence_list)

        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton(tr("dlg.generate"))
        self.generate_btn.setDefault(True)
        self.select_all_btn = QPushButton(tr("dlg.select_all"))
        self.select_all_btn.setEnabled(False)
        self.add_btn = QPushButton(tr("dlg.add_to_card"))
        self.add_btn.setEnabled(False)
        self.cancel_btn = QPushButton(tr("dlg.cancel"))

        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.select_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        qconnect(self.generate_btn.clicked, self._on_generate)
        qconnect(self.select_all_btn.clicked, lambda: self.sentence_list.selectAll())
        qconnect(self.add_btn.clicked, self._on_add)
        qconnect(self.cancel_btn.clicked, self.reject)

    # --- generation -------------------------------------------------------

    def _on_generate(self):
        vocab = self.word_input.text().strip()
        if not vocab:
            showWarning(tr("dlg.enter_vocab"))
            return
        self._vocab = vocab

        self._set_busy(True)
        level = config.get_level()
        n = config.get_num_sentences()

        op = QueryOp(
            parent=self,
            # Runs off the main thread; ignores `col`, only does network work.
            op=lambda col: generation.generate_sentences(vocab, level, n),
            success=self._on_generated,
        )
        op.failure(self._on_error).with_progress(tr("dlg.generating")).run_in_background()

    def _on_generated(self, items: list[dict]):
        self._set_busy(False)
        was_empty = not self._items

        self._syncing = True
        self.sentence_list.blockSignals(True)
        for item in items:
            self._items.append(item)
            li = QListWidgetItem(item["jp"])
            li.setFlags(_ITEM_FLAGS)
            li.setCheckState(Qt.CheckState.Unchecked)
            if item.get("en"):
                li.setToolTip(item["en"])
            self.sentence_list.addItem(li)
        self.sentence_list.blockSignals(False)
        self._syncing = False

        self.sentence_list.setEnabled(True)
        self.select_all_btn.setEnabled(bool(self._items))
        self.generate_btn.setText(tr("dlg.generate_more"))
        if was_empty and self._items:
            self.sentence_list.setCurrentRow(0)  # auto-select first → enables Add

    def _on_error(self, exc: Exception):
        self._set_busy(False)
        showWarning(str(exc))

    def _set_busy(self, busy: bool):
        self.generate_btn.setEnabled(not busy)

    # --- selection <-> checkbox mirroring --------------------------------

    def _on_selection_changed(self):
        if self._syncing:
            return
        self._syncing = True
        self.sentence_list.blockSignals(True)
        for i in range(self.sentence_list.count()):
            it = self.sentence_list.item(i)
            it.setCheckState(
                Qt.CheckState.Checked if it.isSelected() else Qt.CheckState.Unchecked
            )
        self.sentence_list.blockSignals(False)
        self._syncing = False
        self._update_add_enabled()

    def _on_item_changed(self, item: QListWidgetItem):
        # Fires for a checkbox toggle or a committed text edit. Keep selection in
        # step with the checkbox; edit state is derived later at add time.
        if self._syncing:
            return
        self._syncing = True
        self.sentence_list.blockSignals(True)
        item.setSelected(item.checkState() == Qt.CheckState.Checked)
        self.sentence_list.blockSignals(False)
        self._syncing = False
        self._update_add_enabled()

    def _update_add_enabled(self):
        self.add_btn.setEnabled(bool(self.sentence_list.selectedItems()))

    # --- edit / revert ----------------------------------------------------

    def _show_context_menu(self, pos):
        item = self.sentence_list.itemAt(pos)
        if item is None:
            return
        row = self.sentence_list.row(item)
        menu = QMenu(self)
        revert = menu.addAction(tr("dlg.revert"))
        revert.setEnabled(item.text() != self._items[row]["jp"])
        chosen = menu.exec(self.sentence_list.mapToGlobal(pos))
        if chosen is revert:
            self._syncing = True
            self.sentence_list.blockSignals(True)
            item.setText(self._items[row]["jp"])
            self.sentence_list.blockSignals(False)
            self._syncing = False

    # --- injection --------------------------------------------------------

    def _on_add(self):
        rows = sorted(self.sentence_list.row(it) for it in self.sentence_list.selectedItems())
        if not rows:
            return

        if self.target_field not in self.note:
            showWarning(
                tr(
                    "err.target_not_found",
                    field=self.target_field,
                    note_type=self.note.note_type()["name"],
                    fields=", ".join(self.note.keys()),
                )
            )
            return

        sep = config.get_append_separator()
        block = sep.join(self._content_for_row(r) for r in rows)

        existing = self.note[self.target_field]
        if config.get_write_mode() == "append" and existing.strip():
            self.note[self.target_field] = existing + sep + block
        else:
            self.note[self.target_field] = block

        update_note(parent=mw, note=self.note).success(
            lambda _out: self._after_inject()
        ).run_in_background()

    def _content_for_row(self, row: int) -> str:
        item = self.sentence_list.item(row)
        text = item.text()
        data = self._items[row]
        edited = text != data["jp"]
        tokens = data.get("tokens")
        # Edited text can't be re-furiganated reliably; write it verbatim.
        if edited or not tokens or config.get_furigana_mode() == "off":
            return text
        return generation.render(tokens, self._vocab)

    def _after_inject(self):
        # Reflect the saved change in the reviewer's current card.
        try:
            mw.reviewer.card.load()
            if mw.reviewer.state == "answer":
                mw.reviewer._showAnswer()
            else:
                mw.reviewer._showQuestion()
        except Exception:
            # Persisted regardless; a refresh hiccup shouldn't crash the flow.
            pass
        self.accept()
