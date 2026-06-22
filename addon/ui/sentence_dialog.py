"""
Popup shown when the hotkey fires during review.

Stub for now — Generate is a no-op. Next iteration wires the AI call.
"""

from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    Qt,
)


class SentenceDialog(QDialog):
    def __init__(self, parent, vocab_word: str, note_type_name: str, mapping_is_default: bool):
        super().__init__(parent)
        self.setWindowTitle("AI Sentence Generator")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)

        # Note type info
        info_label = QLabel(f"Note type: <b>{note_type_name}</b>")
        if mapping_is_default:
            info_label.setText(
                info_label.text()
                + ' <span style="color:#c80;">(using default field mapping — configure in settings)</span>'
            )
        layout.addWidget(info_label)

        # Editable vocab word — catches misconfigured fields
        layout.addWidget(QLabel("Vocab word:"))
        self.word_input = QLineEdit(vocab_word)
        layout.addWidget(self.word_input)

        # Placeholder for generated sentences
        self.sentence_list = QListWidget()
        self.sentence_list.addItem("(sentences will appear here after Generate)")
        self.sentence_list.setEnabled(False)
        layout.addWidget(self.sentence_list)

        # Buttons
        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_more_btn = QPushButton("Generate More")
        self.generate_more_btn.setEnabled(False)
        self.add_btn = QPushButton("Add to Card")
        self.add_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")

        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.generate_more_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.generate_btn.clicked.connect(self._on_generate_stub)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_generate_stub(self):
        """Placeholder — real AI call comes next iteration."""
        self.sentence_list.clear()
        self.sentence_list.addItem(f"[stub] would generate sentences for: {self.word_input.text()}")
        self.sentence_list.setEnabled(True)
