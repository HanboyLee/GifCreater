# -*- coding: utf-8 -*-
"""Prompt 工作台页面。"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    IndeterminateProgressBar,
    LineEdit,
    ListWidget,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SpinBox,
    SubtitleLabel,
)

from ..config.secrets import SecretStore
from ..config.settings import SettingsManager
from ..config.theme_manager import ThemeManager
from ..core.prompt_schema import format_grid
from ..core.prompt_store import PromptStore, default_library_path
from .workers import RefineWorker


class PromptPage(QWidget):
    def __init__(
        self,
        store: Optional[PromptStore] = None,
        settings: Optional[SettingsManager] = None,
        secrets: Optional[SecretStore] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("promptInterface")
        self.store = store or PromptStore(default_library_path(), auto_seed=True)
        self.settings = settings or SettingsManager()
        self.secrets = secrets or SecretStore()
        self._current_id: Optional[str] = None
        self._refine_worker: Optional[RefineWorker] = None
        self._build()
        self.reload_list()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        left = CardWidget(self)
        left_l = QVBoxLayout(left)
        left_l.addWidget(SubtitleLabel("收藏"))
        self.search = LineEdit()
        self.search.setPlaceholderText("搜索")
        self.search.textChanged.connect(self.reload_list)
        left_l.addWidget(self.search)
        self.list_widget = ListWidget()
        self.list_widget.currentItemChanged.connect(self._on_select)
        left_l.addWidget(self.list_widget, 1)
        self._apply_list_theme()
        ThemeManager.get_instance().themeChanged.connect(self._apply_list_theme)
        io_row = QHBoxLayout()
        self.btn_export = PushButton("导出")
        self.btn_import = PushButton("导入")
        self.btn_export.clicked.connect(self._export)
        self.btn_import.clicked.connect(self._import)
        io_row.addWidget(self.btn_export)
        io_row.addWidget(self.btn_import)
        left_l.addLayout(io_row)
        left.setFixedWidth(268)
        root.addWidget(left)

        right = QVBoxLayout()
        grid_card = CardWidget(self)
        g = QVBoxLayout(grid_card)
        g.addWidget(BodyLabel("网格"))
        pills = QHBoxLayout()
        self.grid_buttons = []
        for r, c, label in (
            (3, 3, "3×3"),
            (4, 4, "4×4"),
            (4, 6, "4×6"),
            (6, 4, "6×4"),
        ):
            btn = PushButton(label)
            btn.clicked.connect(lambda _=False, rr=r, cc=c: self._set_grid(rr, cc))
            pills.addWidget(btn)
            self.grid_buttons.append(btn)
        pills.addWidget(BodyLabel("行"))
        self.spin_rows = SpinBox()
        self.spin_rows.setRange(1, 20)
        self.spin_rows.setValue(3)
        pills.addWidget(self.spin_rows)
        pills.addWidget(BodyLabel("列"))
        self.spin_cols = SpinBox()
        self.spin_cols.setRange(1, 20)
        self.spin_cols.setValue(3)
        pills.addWidget(self.spin_cols)
        pills.addStretch()
        g.addLayout(pills)

        g.addWidget(BodyLabel("背景模式"))
        bg_row = QHBoxLayout()
        self.rb_bg_transparent = RadioButton("🟢 透明背景 (表情包推荐)")
        self.rb_bg_solid = RadioButton("⚪ 纯色背景")
        self.rb_bg_scene = RadioButton("🔵 场景背景 (连贯环境)")
        self.rb_bg_auto = RadioButton("⚪ 自由不限")
        self.rb_bg_transparent.setChecked(True)
        self.bg_group = QButtonGroup(self)
        self.bg_group.addButton(self.rb_bg_transparent, 0)
        self.bg_group.addButton(self.rb_bg_solid, 1)
        self.bg_group.addButton(self.rb_bg_scene, 2)
        self.bg_group.addButton(self.rb_bg_auto, 3)
        bg_row.addWidget(self.rb_bg_transparent)
        bg_row.addWidget(self.rb_bg_solid)
        bg_row.addWidget(self.rb_bg_scene)
        bg_row.addWidget(self.rb_bg_auto)
        bg_row.addStretch()
        g.addLayout(bg_row)

        g.addWidget(BodyLabel("提示"))
        hint_row = QHBoxLayout()
        self.edit_hint = LineEdit()
        self.edit_hint.setText("黄帽衫小人挥手打招呼")
        self.edit_hint.textChanged.connect(lambda: self.label_refine_status.setVisible(False))
        self.btn_refine = PrimaryPushButton("完善")
        self.btn_refine.clicked.connect(self._on_refine)
        hint_row.addWidget(self.edit_hint, 1)
        hint_row.addWidget(self.btn_refine)
        g.addLayout(hint_row)

        self.refine_progress = IndeterminateProgressBar(self)
        self.refine_progress.setVisible(False)
        g.addWidget(self.refine_progress)

        self.label_refine_status = CaptionLabel(self)
        self.label_refine_status.setVisible(False)
        g.addWidget(self.label_refine_status)
        right.addWidget(grid_card)

        prompt_card = CardWidget(self)
        p = QVBoxLayout(prompt_card)
        p.addWidget(BodyLabel("Prompt"))
        self.edit_prompt = PlainTextEdit()
        p.addWidget(self.edit_prompt, 1)
        act = QHBoxLayout()
        self.btn_copy = PrimaryPushButton("复制")
        self.btn_save = PushButton("保存")
        self.btn_copy.clicked.connect(self._copy)
        self.btn_save.clicked.connect(self._save)
        act.addWidget(self.btn_copy)
        act.addWidget(self.btn_save)
        act.addStretch()
        p.addLayout(act)
        right.addWidget(prompt_card, 1)
        root.addLayout(right, 1)

    def _apply_list_theme(self, _name: str = ""):
        t = ThemeManager.get_instance().tokens
        self.list_widget.setStyleSheet(
            f"""
            ListWidget, QListWidget {{
                background-color: {t.card_bg};
                color: {t.text_primary};
                border: 1px solid {t.card_border};
                border-radius: 6px;
                outline: none;
            }}
            ListWidget::viewport, QListWidget::viewport {{
                background-color: {t.card_bg};
            }}
            ListWidget::item, QListWidget::item {{
                color: {t.text_primary};
                background: transparent;
                padding: 6px 8px;
            }}
            ListWidget::item:hover, QListWidget::item:hover {{
                background-color: {t.btn_hover_bg};
            }}
            ListWidget::item:selected, QListWidget::item:selected {{
                background-color: {t.btn_secondary_bg};
                color: {t.text_primary};
            }}
            """
        )

    def _set_grid(self, rows: int, cols: int):
        self.spin_rows.setValue(rows)
        self.spin_cols.setValue(cols)

    def get_bg_mode(self) -> str:
        if self.rb_bg_solid.isChecked():
            return "solid"
        if self.rb_bg_scene.isChecked():
            return "scene"
        if self.rb_bg_auto.isChecked():
            return "auto"
        return "transparent"

    def set_bg_mode(self, mode: str):
        mode = (mode or "transparent").lower().strip()
        if mode == "solid":
            self.rb_bg_solid.setChecked(True)
        elif mode == "scene":
            self.rb_bg_scene.setChecked(True)
        elif mode == "auto":
            self.rb_bg_auto.setChecked(True)
        else:
            self.rb_bg_transparent.setChecked(True)

    def reload_list(self):
        q = self.search.text()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for rec in self.store.list(query=q or None):
            item = QListWidgetItem(f"{rec.title}    {rec.grid.replace('x', '×')}")
            item.setData(Qt.ItemDataRole.UserRole, rec.id)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    def _on_select(self, current: Optional[QListWidgetItem], _prev=None):
        if current is None:
            return
        rid = current.data(Qt.ItemDataRole.UserRole)
        rec = self.store.get(rid)
        if rec is None:
            return
        self._current_id = rec.id
        self.edit_prompt.setPlainText(rec.prompt)
        self.spin_rows.setValue(rec.rows)
        self.spin_cols.setValue(rec.cols)
        self.label_refine_status.setVisible(False)

    def _copy(self):
        from PyQt6.QtWidgets import QApplication

        text = self.edit_prompt.toPlainText()
        QApplication.clipboard().setText(text)
        self._notify("已复制")

    def _save(self):
        prompt = self.edit_prompt.toPlainText()
        rows, cols = self.spin_rows.value(), self.spin_cols.value()
        title = (self.edit_hint.text() or prompt[:24] or "未命名").strip()
        if self._current_id:
            rec = self.store.get(self._current_id)
            if rec:
                rec.title = title
                rec.prompt = prompt
                rec.grid = format_grid(rows, cols)
                self.store.save(rec)
                self.reload_list()
                self._notify("已保存")
                return
        rec = self.store.create(title=title, prompt=prompt, rows=rows, cols=cols)
        self._current_id = rec.id
        self.reload_list()
        self._notify("已保存")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出", "prompts.json", "JSON (*.json)")
        if path:
            self.store.export_json(Path(path))
            self._notify("已导出")

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入", "", "JSON (*.json)")
        if path:
            self.store.import_json(Path(path))
            self.reload_list()
            self._notify("已导入")

    def _on_refine(self):
        from qfluentwidgets import InfoBar, InfoBarPosition

        key = self.secrets.load_key()
        if not key:
            self.label_refine_status.setText("⚠️ 未配置 API Key，请先前往「设置」配置模型参数")
            self.label_refine_status.setStyleSheet("color: #eab308; font-weight: 500;")
            self.label_refine_status.setVisible(True)
            InfoBar.warning(
                "未配置 API",
                "请先在设置中配置 API",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=2800,
            )
            return

        cfg = self.settings.load()
        model_name = cfg.model_id.strip() or "默认模型"
        self.btn_refine.setEnabled(False)
        self.btn_refine.setText("完善中...")
        self.refine_progress.setVisible(True)
        self.refine_progress.start()

        t = ThemeManager.get_instance().tokens
        self.label_refine_status.setText(f"⏳ 正在调用大模型 ({model_name}) 生成分镜动作描述...")
        self.label_refine_status.setStyleSheet(f"color: {t.accent}; font-weight: 500;")
        self.label_refine_status.setVisible(True)

        self._refine_worker = RefineWorker(
            inspiration=self.edit_hint.text(),
            current_prompt=self.edit_prompt.toPlainText(),
            rows=self.spin_rows.value(),
            cols=self.spin_cols.value(),
            base_url=cfg.base_url,
            api_key=key,
            model=cfg.model_id,
            bg_mode=self.get_bg_mode(),
            parent=self,
        )
        self._refine_worker.refineFinished.connect(self._on_refine_ok)
        self._refine_worker.refineFailed.connect(self._on_refine_fail)
        self._refine_worker.start()

    def _on_refine_ok(self, text: str):
        self.btn_refine.setEnabled(True)
        self.btn_refine.setText("完善")
        self.refine_progress.stop()
        self.refine_progress.setVisible(False)
        self.edit_prompt.setPlainText(text)
        self.label_refine_status.setText("✓ 分镜描述完善成功，已更新至下方编辑器")
        self.label_refine_status.setStyleSheet("color: #10b981; font-weight: 500;")
        self.label_refine_status.setVisible(True)
        self._notify("已完善")

    def _on_refine_fail(self, msg: str):
        from qfluentwidgets import InfoBar, InfoBarPosition

        self.btn_refine.setEnabled(True)
        self.btn_refine.setText("完善")
        self.refine_progress.stop()
        self.refine_progress.setVisible(False)
        self.label_refine_status.setText(f"❌ 完善失败: {msg}")
        self.label_refine_status.setStyleSheet("color: #ef4444; font-weight: 500;")
        self.label_refine_status.setVisible(True)
        InfoBar.error("完善失败", msg, parent=self.window(), position=InfoBarPosition.TOP_RIGHT, duration=4000)

    def _notify(self, msg: str):
        from qfluentwidgets import InfoBar, InfoBarPosition

        InfoBar.success(msg, msg, parent=self.window(), position=InfoBarPosition.TOP_RIGHT, duration=1800)
