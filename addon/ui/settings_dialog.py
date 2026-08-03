"""
pop-up that appears when ainki settings is pressed
"""

from aqt import mw
from aqt.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Qt,
    qconnect,
)

from aqt.utils import saveGeom, restoreGeom

from .. import config
from ..i18n import tr, translate, resolve_lang

_GEOM_KEY = "ainkiSettings"

_MODEL_PRESETS = ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-8"]
_LEVEL_PRESETS = ["beginner", "intermediate", "advanced", "N5", "N4", "N3", "N2", "N1"]
_SEPARATOR_PRESETS = ["<br>", "<br><br>"]


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumWidth(440)

        self._i18n = []
        self._mappings = config.all_mappings()
        self._current_nt = None
        self._loading = False

        self._reg(self.setWindowTitle, "set.title")

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "")
        self._tabs.addTab(self._build_api_tab(), "")
        self._reg(lambda t: self._tabs.setTabText(0, t), "set.tab_general")
        self._reg(lambda t: self._tabs.setTabText(1, t), "set.tab_api")
        layout.addWidget(self._tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        restore_btn = buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        self._reg(restore_btn.setText, "set.restore_defaults")
        qconnect(restore_btn.clicked, self._restore_defaults)
        qconnect(buttons.accepted, self._on_save)
        qconnect(buttons.rejected, self.reject)
        layout.addWidget(buttons)

        self._load_note_types()
        self.resize(450, 480)
        restoreGeom(self, _GEOM_KEY)

    def done(self, result):
        saveGeom(self, _GEOM_KEY)
        super().done(result)

    def _reg(self, setter, key: str):
        """register a translatable setter and apply the current language now"""
        self._i18n.append((setter, key))
        setter(tr(key))

    def _retranslate(self, lang: str):
        """relabel every registered widget, no config write"""
        for setter, key in self._i18n:
            setter(translate(key, lang))

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(6)

        self.language_combo = QComboBox()
        self.language_combo.addItem("", "auto")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("日本語", "ja")
        self._reg(lambda t: self.language_combo.setItemText(0, t), "set.language_auto")
        lang_idx = self.language_combo.findData(config.get_language())
        self.language_combo.setCurrentIndex(lang_idx if lang_idx >= 0 else 0)
        qconnect(self.language_combo.currentIndexChanged, self._on_language_changed)
        self._add_row(form, "set.language", self.language_combo)

        self.hotkey_edit = QKeySequenceEdit(QKeySequence(config.get_hotkey()))
        self._add_row(form, "set.hotkey", self.hotkey_edit)

        self.note_type_combo = QComboBox()
        qconnect(self.note_type_combo.currentTextChanged, self._on_note_type_changed)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        qconnect(self.source_combo.currentTextChanged, self._on_field_changed)
        qconnect(self.target_combo.currentTextChanged, self._on_field_changed)
        self._add_row(form, "set.note_type", self.note_type_combo)
        self._add_row(form, "set.word_field", self.source_combo)
        self._add_row(form, "set.append_to", self.target_combo)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("", "append")
        self.mode_combo.addItem("", "overwrite")
        self._reg(lambda t: self.mode_combo.setItemText(0, t), "set.mode_append")
        self._reg(lambda t: self.mode_combo.setItemText(1, t), "set.mode_overwrite")
        mode_idx = self.mode_combo.findData(config.get_write_mode())
        self.mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.sep_combo = QComboBox()
        self.sep_combo.setEditable(True)
        self.sep_combo.addItems(_SEPARATOR_PRESETS)
        self.sep_combo.setCurrentText(config.get_append_separator())
        self._add_row(form, "set.mode", self.mode_combo)
        self._add_row(form, "set.separator", self.sep_combo)

        self.level_combo = QComboBox()
        self.level_combo.setEditable(True)
        self.level_combo.addItems(_LEVEL_PRESETS)
        self.level_combo.setCurrentText(config.get_level())
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(config.get_num_sentences())
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 48)
        self.font_spin.setValue(config.get_sentence_font_size())
        self.style_combo = QComboBox()
        for i, value in enumerate(("casual", "polite", "news", "business", "mixed")):
            self.style_combo.addItem("", value)
            self._reg(lambda t, i=i: self.style_combo.setItemText(i, t), f"set.style_{value}")
        style_idx = self.style_combo.findData(config.get_style())
        self.style_combo.setCurrentIndex(style_idx if style_idx >= 0 else 0)
        self._add_row(form, "set.level", self.level_combo)
        self._add_row(form, "set.style", self.style_combo)
        self._add_row(form, "set.count", self.count_spin)
        self._add_row(form, "set.font_size", self.font_spin)

        self.furigana_combo = QComboBox()
        for i, (value, key) in enumerate(
            (("off", "set.furigana_off"), ("ruby", "set.furigana_ruby"), ("custom", "set.furigana_custom"))
        ):
            self.furigana_combo.addItem("", value)
            self._reg(lambda t, i=i: self.furigana_combo.setItemText(i, t), key)
        fg_idx = self.furigana_combo.findData(config.get_furigana_mode())
        self.furigana_combo.setCurrentIndex(fg_idx if fg_idx >= 0 else 1)
        qconnect(self.furigana_combo.currentIndexChanged, self._on_furigana_mode_changed)
        self.furigana_template_edit = QLineEdit(config.get_furigana_template())
        self._add_row(form, "set.furigana", self.furigana_combo)
        self._add_row(form, "set.custom_wrapper", self.furigana_template_edit)

        layout.addLayout(form)
        layout.addSpacing(16)

        url = config.get_donation_url()
        donate = QLabel()
        self._reg(lambda t, u=url: donate.setText(f'<a href="{u}">{t}</a>'), "set.donate")
        donate.setOpenExternalLinks(True)
        donate.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        donate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(donate)

        layout.addStretch()
        self._on_furigana_mode_changed()
        return tab

    def _add_row(self, form, key: str, widget):
        """form row whose label is registered for retranslation"""
        label = QLabel()
        self._reg(label.setText, key)
        form.addRow(label, widget)

    def _on_furigana_mode_changed(self, *_):
        self.furigana_template_edit.setEnabled(self.furigana_combo.currentData() == "custom")

    def _build_api_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.api_key_edit = QLineEdit(config.get_api_key())
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._add_row(form, "set.api_key", self.api_key_edit)
        api_note = QLabel()
        self._reg(api_note.setText, "set.api_key_note")
        form.addRow("", api_note)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic"])
        self.provider_combo.setCurrentText(config.get_provider_name())
        self._add_row(form, "set.provider", self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(_MODEL_PRESETS)
        self.model_combo.setCurrentText(config.get_model())
        self._add_row(form, "set.model", self.model_combo)

        return tab

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
        if self._loading or not self._current_nt:
            return
        self._mappings[self._current_nt] = {
            "source": self.source_combo.currentText(),
            "target": self.target_combo.currentText(),
        }

    def _collect(self) -> dict:
        return {
            "language": self.language_combo.currentData(),
            "hotkey": self.hotkey_edit.keySequence().toString() or config.get_hotkey(),
            "provider": self.provider_combo.currentText().strip(),
            "model": self.model_combo.currentText().strip(),
            "api_key": self.api_key_edit.text(),
            "level": self.level_combo.currentText().strip(),
            "num_sentences": self.count_spin.value(),
            "sentence_font_size": self.font_spin.value(),
            "style": self.style_combo.currentData(),
            "write_mode": self.mode_combo.currentData(),
            "append_separator": self.sep_combo.currentText(),
            "furigana_mode": self.furigana_combo.currentData(),
            "furigana_template": self.furigana_template_edit.text(),
            "field_mappings": self._mappings,
        }

    def _on_save(self):
        config.save_settings(self._collect())
        from .. import rebind_hotkey

        rebind_hotkey()
        self.accept()

    def _on_language_changed(self, *_):
        if self._loading:
            return
        self._retranslate(resolve_lang(self.language_combo.currentData()))

    def _restore_defaults(self):
        d = config.defaults()
        if not d:
            return
        self._loading = True
        lang_idx = self.language_combo.findData(d["language"])
        self.language_combo.setCurrentIndex(lang_idx if lang_idx >= 0 else 0)
        self.hotkey_edit.setKeySequence(QKeySequence(d["hotkey"]))
        self.level_combo.setCurrentText(d["level"])
        style_idx = self.style_combo.findData(d["style"])
        self.style_combo.setCurrentIndex(style_idx if style_idx >= 0 else 0)
        self.count_spin.setValue(d["num_sentences"])
        self.font_spin.setValue(d["sentence_font_size"])
        mode_idx = self.mode_combo.findData(d["write_mode"])
        self.mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.sep_combo.setCurrentText(d["append_separator"])
        fg_idx = self.furigana_combo.findData(d["furigana_mode"])
        self.furigana_combo.setCurrentIndex(fg_idx if fg_idx >= 0 else 1)
        self.furigana_template_edit.setText(d["furigana_template"])
        self.model_combo.setCurrentText(d["model"])
        self._loading = False
        self._on_furigana_mode_changed()
        self._retranslate(resolve_lang(self.language_combo.currentData()))
