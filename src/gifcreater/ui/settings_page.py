from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SearchLineEdit,
    SubtitleLabel,
)

from ..config.secrets import SecretStore
from ..config.settings import (
    PROVIDER_PRESETS,
    SettingsManager,
    list_models,
    preset_base_url,
    save_cached_models,
)
from ..config.theme_manager import ThemeManager, ThemeMode
from .workers import ModelFetchWorker


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

        model_header = QHBoxLayout()
        model_header.addWidget(BodyLabel("模型"))
        model_header.addStretch()
        self.btn_fetch_models = PushButton("🔄 获取最新模型")
        self.btn_fetch_models.clicked.connect(self._on_fetch_models)
        model_header.addWidget(self.btn_fetch_models)
        a.addLayout(model_header)

        self.search_model = SearchLineEdit()
        self.search_model.setPlaceholderText("搜索模型 (实时过滤下述列表)")
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

    def _on_fetch_models(self):
        base_url = self.edit_base.text().strip()
        if not base_url:
            InfoBar.warning(
                "未配置 Base URL",
                "请先输入服务商 Base URL",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
            )
            return

        api_key = self.edit_key.text().strip()
        self.btn_fetch_models.setEnabled(False)
        self.btn_fetch_models.setText("⏳ 正在获取...")

        self._fetch_worker = ModelFetchWorker(base_url, api_key, parent=self)
        self._fetch_worker.fetchFinished.connect(self._on_models_fetched)
        self._fetch_worker.fetchFailed.connect(self._on_models_fetch_failed)
        self._fetch_worker.start()

    def _on_models_fetched(self, models: list[str]):
        self.btn_fetch_models.setEnabled(True)
        self.btn_fetch_models.setText("🔄 获取最新模型")
        provider = self._provider_key()
        save_cached_models(provider, models, path=self.settings.cache_path)
        self._refill_models(query=self.search_model.text())
        InfoBar.success(
            "获取成功",
            f"已成功同步并缓存 {len(models)} 个可用模型",
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
        )

    def _on_models_fetch_failed(self, err: str):
        self.btn_fetch_models.setEnabled(True)
        self.btn_fetch_models.setText("🔄 获取最新模型")
        InfoBar.error(
            "获取失败",
            err,
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
        )

    def _refill_models(self, query: str = "", selected: str | None = None):
        current = selected if selected is not None else self.combo_model.currentText()
        models = list_models(self._provider_key(), query, cache_path=self.settings.cache_path)
        q = (query or "").strip()
        # 仅当搜索无任何匹配结果时，将用户输入的文本作为自定义模型直通项
        if q and not models:
            models = [q]
        elif current and current not in models and not query:
            models = [current] + models

        self.combo_model.blockSignals(True)
        self.combo_model.clear()
        for mid in models:
            self.combo_model.addItem(mid)
        if current and self.combo_model.findText(current) >= 0:
            self.combo_model.setCurrentIndex(self.combo_model.findText(current))
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
        InfoBar.success(
            "已保存",
            f"设置已生效，当前锁定模型: {cfg.model_id}",
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2500,
        )

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
