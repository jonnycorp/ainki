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
from ..i18n import tr

_MODEL_PRESETS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"]
_LEVEL_PRESETS = ["beginner", "intermediate", "advanced", "N5", "N4", "N3", "N2", "N1"]
_SEPARATOR_PRESETS = ["<br>", "<br><br>"]


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(tr("set.title"))
        self.setMinimumWidth(520)

        # Staged field mappings — edits accumulate here, written on Save.
        self._mappings = config.all_mappings()
        self._current_nt = None
        self._loading = False  # guards programmatic combo repopulation

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), tr("set.tab_general"))
        tabs.addTab(self._build_api_tab(), tr("set.tab_api"))
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
        layout.addWidget(QLabel(tr("set.intro")))

        # Donation placeholder — reserved space, blank until a URL is configured.
        layout.addWidget(self._build_donation_box())

        # Language — default follows Anki; override pins the add-on's language.
        lang_group = QGroupBox()
        lang_form = QFormLayout(lang_group)
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("set.language_auto"), "auto")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("日本語", "ja")
        lang_idx = self.language_combo.findData(config.get_language())
        self.language_combo.setCurrentIndex(lang_idx if lang_idx >= 0 else 0)
        lang_form.addRow(tr("set.language"), self.language_combo)
        layout.addWidget(lang_group)

        # Field mapping
        mapping_group = QGroupBox(tr("set.field_mapping"))
        mapping_form = QFormLayout(mapping_group)
        self.note_type_combo = QComboBox()
        qconnect(self.note_type_combo.currentTextChanged, self._on_note_type_changed)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        qconnect(self.source_combo.currentTextChanged, self._on_field_changed)
        qconnect(self.target_combo.currentTextChanged, self._on_field_changed)
        mapping_form.addRow(tr("set.note_type"), self.note_type_combo)
        mapping_form.addRow(tr("set.word_field"), self.source_combo)
        mapping_form.addRow(tr("set.append_to"), self.target_combo)
        layout.addWidget(mapping_group)

        # Append behaviour
        append_group = QGroupBox(tr("set.when_adding"))
        append_form = QFormLayout(append_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(tr("set.mode_append"), "append")
        self.mode_combo.addItem(tr("set.mode_overwrite"), "overwrite")
        mode_idx = self.mode_combo.findData(config.get_write_mode())
        self.mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.sep_combo = QComboBox()
        self.sep_combo.setEditable(True)
        self.sep_combo.addItems(_SEPARATOR_PRESETS)
        self.sep_combo.setCurrentText(config.get_append_separator())
        append_form.addRow(tr("set.mode"), self.mode_combo)
        append_form.addRow(tr("set.separator"), self.sep_combo)
        append_form.addRow("", QLabel(tr("set.separator_hint")))
        layout.addWidget(append_group)

        # Generation
        gen_group = QGroupBox(tr("set.generation"))
        gen_form = QFormLayout(gen_group)
        self.level_combo = QComboBox()
        self.level_combo.setEditable(True)
        self.level_combo.addItems(_LEVEL_PRESETS)
        self.level_combo.setCurrentText(config.get_level())
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(config.get_num_sentences())
        gen_form.addRow(tr("set.level"), self.level_combo)
        gen_form.addRow(tr("set.count"), self.count_spin)
        layout.addWidget(gen_group)

        # Furigana — readings on non-target kanji.
        fg_group = QGroupBox(tr("set.furigana"))
        fg_form = QFormLayout(fg_group)
        self.furigana_combo = QComboBox()
        self.furigana_combo.addItem(tr("set.furigana_off"), "off")
        self.furigana_combo.addItem(tr("set.furigana_ruby"), "ruby")
        self.furigana_combo.addItem(tr("set.furigana_custom"), "custom")
        fg_idx = self.furigana_combo.findData(config.get_furigana_mode())
        self.furigana_combo.setCurrentIndex(fg_idx if fg_idx >= 0 else 1)
        qconnect(self.furigana_combo.currentIndexChanged, self._on_furigana_mode_changed)
        self.furigana_template_edit = QLineEdit(config.get_furigana_template())
        fg_form.addRow(tr("set.mode"), self.furigana_combo)
        fg_form.addRow(tr("set.custom_wrapper"), self.furigana_template_edit)
        fg_form.addRow("", QLabel(tr("set.furigana_hint")))
        layout.addWidget(fg_group)
        self._on_furigana_mode_changed()  # set initial enabled state

        layout.addStretch()
        return tab

    def _on_furigana_mode_changed(self, *_):
        self.furigana_template_edit.setEnabled(self.furigana_combo.currentData() == "custom")

    def _build_donation_box(self) -> QWidget:
        box = QGroupBox(tr("set.support"))
        box.setObjectName("ainkiDonationBox")  # styling hook for later
        inner = QVBoxLayout(box)
        url = config.get_donation_url()
        if url:
            label = QLabel(f'<a href="{url}">{tr("set.donate")}</a>')
            label.setOpenExternalLinks(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        else:
            label = QLabel(tr("set.support_coming"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(label)
        return box

    # --- API Key tab ------------------------------------------------------

    def _build_api_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.api_key_edit = QLineEdit(config.get_raw_api_key())
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(tr("set.api_key"), self.api_key_edit)
        form.addRow("", QLabel(tr("set.api_key_note")))

        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(True)
        self.provider_combo.addItems(["anthropic"])
        self.provider_combo.setCurrentText(config.get_provider_name())
        form.addRow(tr("set.provider"), self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(_MODEL_PRESETS)
        self.model_combo.setCurrentText(config.get_model())
        form.addRow(tr("set.model"), self.model_combo)

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
                "language": self.language_combo.currentData(),
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
