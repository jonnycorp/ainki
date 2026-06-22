"""
Settings dialog — the configuration surface for non-coders. Opened from
Tools → ainki Settings (and the add-on's Config button), so the user never has
to hand-edit JSON or guess their note type's field names.

Tabs:
- General — donation placeholder, per-note-type field mapping (real fields via
  dropdowns), append behaviour, and generation parameters.
- API Key — the BYOK key (masked), provider, and model.

Plain aqt.qt widgets and group boxes: intentionally restrained styling, named so
later visual polish (stylesheets) has clean hooks.
"""

from aqt import mw
from aqt.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Qt,
    qconnect,
)

from .. import config

_MODEL_PRESETS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"]
_LEVEL_PRESETS = ["beginner", "intermediate", "advanced", "N5", "N4", "N3", "N2", "N1"]
_SEPARATOR_PRESETS = ["<br>", "<br><br>"]


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("ainki Settings")
        self.setMinimumWidth(520)

        # Staged field mappings — edits accumulate here, written on Save.
        self._mappings = config.all_mappings()
        self._current_nt = None
        self._loading = False  # guards programmatic combo repopulation

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_api_tab(), "API Key")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        qconnect(buttons.accepted, self._on_save)
        qconnect(buttons.rejected, self.reject)
        layout.addWidget(buttons)

        self._load_note_types()

    # --- General tab ------------------------------------------------------

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Top line
        layout.addWidget(QLabel("<b>ainki</b> — AI example sentences for your reviews."))

        # Donation placeholder — reserved space, blank until a URL is configured.
        layout.addWidget(self._build_donation_box())

        # Field mapping
        mapping_group = QGroupBox("Field mapping")
        mapping_form = QFormLayout(mapping_group)
        self.note_type_combo = QComboBox()
        qconnect(self.note_type_combo.currentTextChanged, self._on_note_type_changed)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        qconnect(self.source_combo.currentTextChanged, self._on_field_changed)
        qconnect(self.target_combo.currentTextChanged, self._on_field_changed)
        mapping_form.addRow("Note type:", self.note_type_combo)
        mapping_form.addRow("Word field:", self.source_combo)
        mapping_form.addRow("Append sentences to:", self.target_combo)
        layout.addWidget(mapping_group)

        # Append behaviour
        append_group = QGroupBox("When adding a sentence")
        append_form = QFormLayout(append_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Append to existing content", "append")
        self.mode_combo.addItem("Overwrite the field", "overwrite")
        mode_idx = self.mode_combo.findData(config.get_write_mode())
        self.mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.sep_combo = QComboBox()
        self.sep_combo.setEditable(True)
        self.sep_combo.addItems(_SEPARATOR_PRESETS)
        self.sep_combo.setCurrentText(config.get_append_separator())
        append_form.addRow("Mode:", self.mode_combo)
        append_form.addRow("Separator (HTML):", self.sep_combo)
        append_form.addRow(
            "", QLabel("<span style='color:gray;'>Fields are HTML — use &lt;br&gt; for a line break.</span>")
        )
        layout.addWidget(append_group)

        # Generation
        gen_group = QGroupBox("Generation")
        gen_form = QFormLayout(gen_group)
        self.level_combo = QComboBox()
        self.level_combo.setEditable(True)
        self.level_combo.addItems(_LEVEL_PRESETS)
        self.level_combo.setCurrentText(config.get_level())
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(config.get_num_sentences())
        gen_form.addRow("Learner level:", self.level_combo)
        gen_form.addRow("Sentences per generation:", self.count_spin)
        layout.addWidget(gen_group)

        # Furigana — readings on non-target kanji.
        fg_group = QGroupBox("Furigana")
        fg_form = QFormLayout(fg_group)
        self.furigana_combo = QComboBox()
        self.furigana_combo.addItem("Off", "off")
        self.furigana_combo.addItem("Ruby (HTML, works on any template)", "ruby")
        self.furigana_combo.addItem("Custom wrapper", "custom")
        fg_idx = self.furigana_combo.findData(config.get_furigana_mode())
        self.furigana_combo.setCurrentIndex(fg_idx if fg_idx >= 0 else 1)
        qconnect(self.furigana_combo.currentIndexChanged, self._on_furigana_mode_changed)
        self.furigana_template_edit = QLineEdit(config.get_furigana_template())
        fg_form.addRow("Mode:", self.furigana_combo)
        fg_form.addRow("Custom wrapper:", self.furigana_template_edit)
        fg_form.addRow(
            "",
            QLabel(
                "<span style='color:gray;'>Use {kanji} and {reading}. "
                "e.g. <code>{kanji}[{reading}]</code> or "
                "<code>&lt;ruby&gt;{kanji}&lt;rt&gt;{reading}&lt;/rt&gt;&lt;/ruby&gt;</code>. "
                "The target word is always left bare.</span>"
            ),
        )
        layout.addWidget(fg_group)
        self._on_furigana_mode_changed()  # set initial enabled state

        layout.addStretch()
        return tab

    def _on_furigana_mode_changed(self, *_):
        self.furigana_template_edit.setEnabled(self.furigana_combo.currentData() == "custom")

    def _build_donation_box(self) -> QWidget:
        box = QGroupBox("Support")
        box.setObjectName("ainkiDonationBox")  # styling hook for later
        inner = QVBoxLayout(box)
        url = config.get_donation_url()
        if url:
            label = QLabel(f'<a href="{url}">Buy me a coffee ☕</a>')
            label.setOpenExternalLinks(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        else:
            label = QLabel("<span style='color:gray;'>(support link coming soon)</span>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(label)
        return box

    # --- API Key tab ------------------------------------------------------

    def _build_api_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.api_key_edit = QLineEdit(config.get_raw_api_key())
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API key:", self.api_key_edit)
        form.addRow(
            "",
            QLabel(
                "<span style='color:gray;'>Stored in plaintext on disk. Use a key "
                "scoped to this purpose.</span>"
            ),
        )

        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(True)
        self.provider_combo.addItems(["anthropic"])
        self.provider_combo.setCurrentText(config.get_provider_name())
        form.addRow("Provider:", self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(_MODEL_PRESETS)
        self.model_combo.setCurrentText(config.get_model())
        form.addRow("Model:", self.model_combo)

        return tab

    # --- field-mapping wiring --------------------------------------------

    def _load_note_types(self):
        if mw.col is None:
            return
        names = sorted(nt["name"] for nt in mw.col.models.all())
        self._loading = True
        self.note_type_combo.addItems(names)
        self._loading = False
        current = self._current_card_note_type()
        if current and current in names:
            self.note_type_combo.setCurrentText(current)
        # Ensure the field combos populate even if the index didn't change.
        self._on_note_type_changed(self.note_type_combo.currentText())

    def _current_card_note_type(self):
        try:
            if mw.reviewer and mw.reviewer.card:
                return mw.reviewer.card.note().note_type()["name"]
        except Exception:
            pass
        return None

    def _field_names(self, note_type_name: str) -> list:
        nt = mw.col.models.by_name(note_type_name) if mw.col else None
        return [f["name"] for f in nt["flds"]] if nt else []

    def _on_note_type_changed(self, name: str):
        if not name:
            return
        self._loading = True
        fields = self._field_names(name)
        for combo in (self.source_combo, self.target_combo):
            combo.clear()
            combo.addItems(fields)

        mapping = self._mappings.get(name) or config.get_mapping(name)
        if mapping.get("source") in fields:
            self.source_combo.setCurrentText(mapping["source"])
        if mapping.get("target") in fields:
            self.target_combo.setCurrentText(mapping["target"])

        self._current_nt = name
        self._loading = False

    def _on_field_changed(self, _text: str):
        # Only genuine user edits stage a mapping — programmatic repopulation
        # (note-type switches) runs under _loading and is ignored.
        if self._loading or not self._current_nt:
            return
        self._mappings[self._current_nt] = {
            "source": self.source_combo.currentText(),
            "target": self.target_combo.currentText(),
        }

    # --- save -------------------------------------------------------------

    def _on_save(self):
        config.save_settings(
            {
                "provider": self.provider_combo.currentText().strip(),
                "model": self.model_combo.currentText().strip(),
                "api_key": self.api_key_edit.text(),
                "level": self.level_combo.currentText().strip(),
                "num_sentences": self.count_spin.value(),
                "write_mode": self.mode_combo.currentData(),
                "append_separator": self.sep_combo.currentText(),
                "furigana_mode": self.furigana_combo.currentData(),
                "furigana_template": self.furigana_template_edit.text(),
                "field_mappings": self._mappings,
            }
        )
        self.accept()
