# -*- coding: utf-8 -*-
"""设置页：外观主题（横排）+ API。模型可搜索下拉；Key 可显示/隐藏；仅保存。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    RadioButton,
    SearchLineEdit,
    SubtitleLabel,
)

from ..config.secrets import SecretStore
from ..config.settings import PROVIDER_PRESETS, SettingsManager, list_models, preset_base_url
from ..config.theme_manager import ThemeManager, ThemeMode


class SettingsPage(QWidget):
    themePersisted = pyqtSignal(str)

    def __init__(self, settings: SettingsManager | None = None, secrets: SecretStore | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.settings = settings or SettingsManager()
        self.secrets = secrets or SecretStore()
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.addWidget(SubtitleLabel("设置"))

        card = CardWidget(self)
        lay = QVBoxLayout(card)
        lay.addWidget(SubtitleLabel("外观"))
        row = QHBoxLayout()
        row.addWidget(BodyLabel("主题"))
        self.radio_dark = RadioButton("深色")
        self.radio_light = RadioButton("浅色")
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.radio_dark)
        self.theme_group.addButton(self.radio_light)
        row.addWidget(self.radio_dark)
        row.addWidget(self.radio_light)
        row.addStretch()
        lay.addLayout(row)
        root.addWidget(card)

        api = CardWidget(self)
        a = QVBoxLayout(api)
        a.addWidget(SubtitleLabel("API"))
        a.addWidget(BodyLabel("Provider"))
        self.combo_provider = ComboBox()
        for key, label, _url in PROVIDER_PRESETS:
            self.combo_provider.addItem(label, userData=key)
        a.addWidget(self.combo_provider)
        a.addWidget(BodyLabel("Base URL"))
        self.edit_base = LineEdit()
        a.addWidget(self.edit_base)
        a.addWidget(BodyLabel("模型"))
        self.search_model = SearchLineEdit()
        self.search_model.setPlaceholderText("搜索模型")
        a.addWidget(self.search_model)
        self.combo_model = ComboBox()
        a.addWidget(self.combo_model)
        a.addWidget(BodyLabel("API Key"))
        self.edit_key = PasswordLineEdit()
        self.edit_key.setPlaceholderText("输入 API Key")
        a.addWidget(self.edit_key)
        self.btn_save = PrimaryPushButton("保存")
        self.btn_save.clicked.connect(self._save_all)
        a.addWidget(self.btn_save)
        root.addWidget(api)
        root.addStretch()

        self.theme_group.buttonClicked.connect(self._apply_theme_preview)
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        self.search_model.textChanged.connect(self._on_model_search)
        self.search_model.searchSignal.connect(self._on_model_search)

    def _load(self):
        cfg = self.settings.load()
        self.radio_dark.blockSignals(True)
        self.radio_light.blockSignals(True)
        if cfg.normalized_theme() == "light":
            self.radio_light.setChecked(True)
        else:
            self.radio_dark.setChecked(True)
        self.radio_dark.blockSignals(False)
        self.radio_light.blockSignals(False)
        self.combo_provider.blockSignals(True)
        idx = 0
        for i, (key, _label, _url) in enumerate(PROVIDER_PRESETS):
            if key == cfg.provider:
                idx = i
                break
        self.combo_provider.setCurrentIndex(idx)
        self.combo_provider.blockSignals(False)
        self.edit_base.setText(cfg.base_url)
        self.search_model.blockSignals(True)
        self.search_model.setText("")
        self.search_model.blockSignals(False)
        self._refill_models(selected=cfg.model_id)
        key = self.secrets.load_key()
        self.edit_key.setText(key)

    def _provider_key(self) -> str:
        data = self.combo_provider.currentData()
        return str(data or "openrouter")

    def _on_provider_changed(self, _index: int = 0):
        url = preset_base_url(self._provider_key())
        if url:
            self.edit_base.setText(url)
        self.search_model.setText("")
        self._refill_models()

    def _on_model_search(self, text: str = ""):
        self._refill_models(query=self.search_model.text())

    def _refill_models(self, query: str = "", selected: str | None = None):
        current = selected if selected is not None else self.combo_model.currentText()
        models = list_models(self._provider_key(), query)
        if current and current not in models and not query:
            models = [current] + models
        self.combo_model.blockSignals(True)
        self.combo_model.clear()
        for mid in models:
            self.combo_model.addItem(mid)
        if current:
            i = self.combo_model.findText(current)
            if i >= 0:
                self.combo_model.setCurrentIndex(i)
            elif self.combo_model.count() > 0:
                self.combo_model.setCurrentIndex(0)
        self.combo_model.blockSignals(False)

    def _selected_model(self) -> str:
        text = (self.combo_model.currentText() or "").strip()
        if text:
            return text
        return (self.search_model.text() or "").strip()

    def _apply_theme_preview(self, _btn=None):
        mode = ThemeMode.LIGHT if self.radio_light.isChecked() else ThemeMode.DARK
        ThemeManager.get_instance().set_theme(mode)
        self.themePersisted.emit("light" if self.radio_light.isChecked() else "dark")

    def _save_all(self):
        from qfluentwidgets import InfoBar, InfoBarPosition

        cfg = self.settings.load()
        cfg.theme = "light" if self.radio_light.isChecked() else "dark"
        cfg.provider = self._provider_key()
        cfg.base_url = self.edit_base.text().strip()
        model = self._selected_model()
        if model:
            cfg.model_id = model
        self.settings.save(cfg)
        self.secrets.save_key(self.edit_key.text())
        ThemeManager.get_instance().set_theme(
            ThemeMode.LIGHT if cfg.theme == "light" else ThemeMode.DARK
        )
        parent = self.window()
        InfoBar.success("已保存", "已保存", parent=parent, position=InfoBarPosition.TOP_RIGHT, duration=1800)

    def _persist_theme(self, _btn=None):
        """兼容旧测试：立即写入主题。"""
        self._apply_theme_preview()
        cfg = self.settings.load()
        cfg.theme = "light" if self.radio_light.isChecked() else "dark"
        self.settings.save(cfg)

    def sync_from_manager(self):
        is_dark = ThemeManager.get_instance().is_dark()
        self.radio_dark.blockSignals(True)
        self.radio_light.blockSignals(True)
        self.radio_dark.setChecked(is_dark)
        self.radio_light.setChecked(not is_dark)
        self.radio_dark.blockSignals(False)
        self.radio_light.blockSignals(False)
