# -*- coding: utf-8 -*-
"""v3.5 工作台进程内 E2E：导航 + Mock 完善（不打真网）。"""

from PyQt6.QtWidgets import QApplication

from src.gifcreater.config.secrets import FakeProtector, SecretStore
from src.gifcreater.config.settings import SettingsManager
from src.gifcreater.core.prompt_store import PromptStore
from src.gifcreater.ui.main_window import MainWindow
from src.gifcreater.ui.prompt_page import PromptPage


def test_main_window_has_three_pages(qapp, tmp_path):
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    win = MainWindow(settings_manager=settings, secret_store=secrets)
    assert "v3.5" in win.windowTitle()
    assert win.prompt_page is not None
    assert win.settings_page is not None
    assert win.stackedWidget.count() >= 3
    win.switchTo(win.prompt_page)
    assert win.stackedWidget.currentWidget() is win.prompt_page
    win.switchTo(win.settings_page)
    assert win.settings_page.radio_dark is not None
    assert win.settings_page.combo_provider is not None


def test_refine_without_key_does_not_start_worker(qapp, tmp_path):
    store = PromptStore(tmp_path / "lib.sqlite")
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)
    page._on_refine()
    assert page._refine_worker is None
    assert "未配置 API Key" in page.label_refine_status.text()
    assert not page.label_refine_status.isHidden()


def test_refine_with_mock_writes_prompt(qapp, tmp_path, monkeypatch):
    def fake_complete(**kwargs):
        return "A single 3x3 storyboard sheet, nine equal panels, same character waving."

    monkeypatch.setattr("src.gifcreater.core.agent_engine.chat_completions", fake_complete)

    store = PromptStore(tmp_path / "lib.sqlite")
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    secrets.save_key("sk-test")
    page = PromptPage(store=store, settings=settings, secrets=secrets)
    assert page.get_bg_mode() == "transparent"
    page.set_bg_mode("scene")
    assert page.get_bg_mode() == "scene"

    page.spin_rows.setValue(3)
    page.spin_cols.setValue(3)
    page.edit_hint.setText("黄帽衫小人挥手")
    page._on_refine()
    assert page._refine_worker is not None
    assert page._refine_worker.bg_mode == "scene"
    assert page.btn_refine.text() == "完善中..."
    assert page.btn_refine.isEnabled() is False
    assert not page.refine_progress.isHidden()
    assert "正在调用大模型" in page.label_refine_status.text()
    assert not page.label_refine_status.isHidden()

    page._refine_worker.wait(15000)
    QApplication.processEvents()
    text = page.edit_prompt.toPlainText()
    assert "storyboard" in text.lower() or "panel" in text.lower()
    assert "--ar" not in text
    assert "--grid" not in text
    assert page.btn_refine.text() == "完善"
    assert page.btn_refine.isEnabled() is True
    assert page.refine_progress.isHidden()
    assert "成功" in page.label_refine_status.text()


def test_refine_failure_shows_inline_error(qapp, tmp_path):
    store = PromptStore(tmp_path / "lib.sqlite")
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)
    page._on_refine_fail("认证失败 (401)")
    assert page.btn_refine.text() == "完善"
    assert page.btn_refine.isEnabled() is True
    assert page.refine_progress.isHidden()
    assert "❌ 完善失败: 认证失败 (401)" == page.label_refine_status.text()
    assert not page.label_refine_status.isHidden()

    # 编辑提示词后状态自动隐藏
    page.edit_hint.setText("新提示")
    assert page.label_refine_status.isHidden()


def test_prompt_list_elide_and_tooltips(qapp, tmp_path):
    from PyQt6.QtCore import Qt

    store = PromptStore(tmp_path / "lib.sqlite", auto_seed=True)
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)

    # 1. 验证 TextElideMode 为 ElideRight，且禁止横向滚动条
    assert page.list_widget.textElideMode() == Qt.TextElideMode.ElideRight
    assert page.list_widget.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    # 2. 验证每一项均挂载了 ToolTip，且包含完整标题与标签信息
    assert page.list_widget.count() > 0
    first_item = page.list_widget.item(0)
    tip = first_item.toolTip()
    assert tip
    assert "标签:" in tip


def test_prompt_tag_filtering_and_saving(qapp, tmp_path):
    store = PromptStore(tmp_path / "lib.sqlite", auto_seed=True)
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)

    # 1. 验证 tag_combo 初始包含了 "全部标签" 与内置标签
    combo_items = [page.tag_combo.itemText(i) for i in range(page.tag_combo.count())]
    assert "全部标签" in combo_items
    assert "表情包" in combo_items

    # 2. 切换到 "表情包" 标签过滤
    page.tag_combo.setCurrentText("表情包")
    filtered_count = page.list_widget.count()
    assert filtered_count >= 1
    # 切换回 "全部标签"
    page.tag_combo.setCurrentText("全部标签")
    assert page.list_widget.count() >= filtered_count

    # 3. 新建一条 Prompt 并带有特定标签
    page._on_new_prompt()
    page.edit_hint.setText("星空观测者")
    page.edit_prompt.setPlainText("Astronomer looking at stars")
    page.edit_tags.setText("天文, 科幻, 4x4")
    page._save()

    # 4. 验证新标签出现在下拉框中
    all_combo_items = [page.tag_combo.itemText(i) for i in range(page.tag_combo.count())]
    assert "天文" in all_combo_items
    assert "科幻" in all_combo_items

    # 5. 通过新标签进行过滤
    page.tag_combo.setCurrentText("天文")
    assert page.list_widget.count() == 1
    assert "星空观测者" in page.list_widget.item(0).text()


def test_prompt_deletion_protection_and_execution(qapp, tmp_path, monkeypatch):
    from PyQt6.QtCore import QPoint
    from qfluentwidgets import MessageBox

    store = PromptStore(tmp_path / "lib.sqlite", auto_seed=True)
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)

    # 0. 未选中任何项目时的删除防空执行
    page._current_id = None
    page._on_delete_clicked()

    # 1. 尝试删除官方内置模板：应当触发保护，不予删除
    initial_count = page.list_widget.count()
    page.list_widget.setCurrentRow(0)
    page._on_delete_clicked()
    assert page.list_widget.count() == initial_count

    # 2. 创建一条用户自定义的 Prompt
    page._on_new_prompt()
    page.edit_hint.setText("待删除草稿")
    page.edit_prompt.setPlainText("Draft prompt to be deleted")
    page.edit_tags.setText("临时草稿")
    page._save()
    assert page.list_widget.count() == initial_count + 1

    # 3. 模拟用户点击取消删除
    monkeypatch.setattr(MessageBox, "exec", lambda self: False)
    page._on_delete_clicked()
    assert page.list_widget.count() == initial_count + 1

    # 4. 模拟右键菜单触发及用户点击确认删除
    monkeypatch.setattr(MessageBox, "exec", lambda self: True)
    # 模拟在空白处右键菜单
    page._on_list_context_menu(QPoint(-100, -100))
    # 执行删除
    page._on_delete_clicked()
    assert page.list_widget.count() == initial_count
    # 验证已从数据库彻底移除
    assert len(store.list(query="待删除草稿")) == 0


def test_on_new_prompt_resets_state(qapp, tmp_path):
    store = PromptStore(tmp_path / "lib.sqlite", auto_seed=True)
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)

    # 选中第一项
    page.list_widget.setCurrentRow(0)
    assert page._current_id is not None
    assert page.edit_prompt.toPlainText() != ""

    # 点击新建
    page._on_new_prompt()
    assert page._current_id is None
    assert page.edit_prompt.toPlainText() == ""
    assert page.edit_hint.text() == ""
    assert page.edit_tags.text() == ""
    assert page.btn_delete.isEnabled() is False

    # 验证 _on_select(None)
    page._on_select(None)
    assert page._current_id is None

