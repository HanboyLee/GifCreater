# -*- coding: utf-8 -*-
"""
tests/unit/test_ui_components.py
PyQt6 Fluent 表现层交互与组件单元测试
"""

import sys
import pytest
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.gifcreater.core import calculate_default_grid
from src.gifcreater.ui.canvas import InteractiveCanvas, pil_to_qpixmap
from src.gifcreater.ui.filmstrip import FilmstripWidget
from src.gifcreater.ui.sidebar import ControlSidebar
from src.gifcreater.ui.main_window import MainWindow
from tests.fixtures.mock_images import create_dummy_grid_image


def test_canvas_and_player(qapp):
    """测试可交互画布与原地动图播放器及配文联动"""
    canvas = InteractiveCanvas()
    pil_img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    grid = calculate_default_grid(120, 120, 2, 2)

    # 1. 载入原图
    canvas.set_source_image(pil_img, grid)
    assert canvas.current_pil_image is not None
    assert len(canvas.grid_lines) > 0

    # 2. 模拟参考线拖拽完成
    canvas.on_line_drag_finished()

    # 3. 载入切片帧并启动播放
    frames = [pil_img.crop((0, 0, 60, 60)), pil_img.crop((60, 0, 120, 60))]
    canvas.set_animation_frames(frames, boomerang=True)
    assert canvas.is_playing is True
    assert len(canvas.play_indices) == 2  # 2 帧普通循环

    # 4. 定时器滴答
    canvas._on_play_tick()
    assert canvas.current_play_idx == 1

    # 5. 暂停播放与寻帧
    canvas.stop_playback()
    assert canvas.is_playing is False
    canvas.seek_frame(0)
    assert canvas.current_play_idx == 0

    # 6. 配文所见即所得测试
    canvas.set_caption("测试表情包配文", "bottom")
    assert canvas.caption_text == "测试表情包配文"
    assert canvas.caption_pos == "bottom"


def test_filmstrip_widget(qapp):
    """测试卡片流式序列帧胶卷与废帧剔除"""
    filmstrip = FilmstripWidget()
    pil_img = create_dummy_grid_image(60, 60)
    frames = [pil_img.copy() for _ in range(4)]

    # 1. 载入 4 帧
    filmstrip.set_frames(frames)
    assert len(filmstrip.cards) == 4
    assert len(filmstrip.get_active_frames()) == 4

    # 2. 选中第一帧
    filmstrip._on_card_selected(0, True)
    assert 0 in filmstrip.selected_indices

    # 3. 剔除第二帧
    filmstrip.cards[1].set_deleted(True)
    active = filmstrip.get_active_frames()
    assert len(active) == 3

    # 4. 恢复第二帧
    filmstrip.cards[1].set_deleted(False)
    assert len(filmstrip.get_active_frames()) == 4

    # 5. 清空
    filmstrip.clear()
    assert len(filmstrip.cards) == 0


def test_control_sidebar(qapp):
    """测试现代参数控制侧边栏与配文变换控件"""
    from PyQt6.QtCore import Qt

    sidebar = ControlSidebar()

    # 验证自适应尺寸限制与横向滚动条策略
    assert sidebar.minimumWidth() == 320
    assert sidebar.maximumWidth() == 480
    assert sidebar.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    # 1. 默认预设 (微信表情包)
    assert sidebar.get_export_preset() == "wechat"

    # 2. 切换下拉预设
    sidebar.combo_presets.setCurrentIndex(1)
    assert sidebar.get_export_preset() == "xiaohongshu"
    sidebar.combo_presets.setCurrentIndex(2)
    assert sidebar.get_export_preset() == "hd_gif"
    sidebar.combo_presets.setCurrentIndex(3)
    assert sidebar.get_export_preset() == "webp"

    # 3. 配文输入、旋转与配置获取
    cfg_captured = []
    sidebar.captionConfigChanged.connect(lambda cfg: cfg_captured.append(cfg))

    sidebar.edit_caption.setText("大吉大利")
    assert sidebar.get_caption_text() == "大吉大利"
    assert len(cfg_captured) > 0
    assert cfg_captured[-1].text == "大吉大利"

    # 旋转角度滑块与快捷键
    sidebar._set_rotation_angle(-15)
    assert sidebar.caption_rotation == -15.0
    assert cfg_captured[-1].rotation_deg == -15.0

    sidebar.slider_font_size.setValue(36)
    assert sidebar.get_caption_config().font_size == 36

    # 九宫格快捷对齐
    sidebar._set_position_ratio(0.5, 0.12)
    assert sidebar.caption_pos_y_ratio == 0.12
    assert sidebar.get_caption_position() == "top"

    # 一键模板
    sidebar._apply_style_template("yellow")
    assert sidebar.text_color_rgb == (250, 204, 21)
    sidebar._apply_style_template("danger")
    assert sidebar.text_color_rgb == (239, 68, 68)
    sidebar._apply_style_template("watermark")
    assert sidebar.slider_text_opacity.value() == 35

    # 4. 锁定与解锁处理状态
    sidebar.set_processing_state(True)
    assert sidebar.btn_process.isEnabled() is False
    assert sidebar.edit_caption.isEnabled() is False
    assert sidebar.combo_presets.isEnabled() is False
    sidebar.set_processing_state(False)
    assert sidebar.btn_process.isEnabled() is True
    assert sidebar.edit_caption.isEnabled() is True
    assert sidebar.combo_presets.isEnabled() is True


def test_canvas_caption_drag_interaction(qapp):
    """测试画布配文图元拖拽与位置同步"""
    from PyQt6.QtCore import QPointF
    from src.gifcreater.core.caption import CaptionConfig

    canvas = InteractiveCanvas()
    pil_img = create_dummy_grid_image(200, 200)
    grid = calculate_default_grid(200, 200, 2, 2)
    canvas.set_source_image(pil_img, grid)

    # 载入带角度与透明度的配置
    cfg = CaptionConfig(text="可拖拽文字", pos_x_ratio=0.5, pos_y_ratio=0.88, rotation_deg=15.0)
    canvas.set_caption_config(cfg)
    assert canvas.caption_item is not None
    assert canvas.caption_item.isVisible() is True

    # 模拟鼠标拖拽释放至 (120, 80)
    moved_signals = []
    canvas.captionPositionMoved.connect(lambda x, y: moved_signals.append((x, y)))
    canvas.on_caption_item_drag_finished(QPointF(120, 80))

    assert len(moved_signals) > 0
    assert canvas.caption_config.pos_x_ratio == pytest.approx(120 / 200, rel=1e-2)
    assert canvas.caption_config.pos_y_ratio == pytest.approx(80 / 200, rel=1e-2)




def test_prompt_page_save_list(qapp, tmp_path):
    from src.gifcreater.config.secrets import FakeProtector, SecretStore
    from src.gifcreater.core.prompt_store import PromptStore
    from src.gifcreater.ui.prompt_page import PromptPage

    secrets = SecretStore(tmp_path / "sec.bin", protector=FakeProtector())
    page = PromptPage(PromptStore(tmp_path / "lib.sqlite"), secrets=secrets)

    # 验证快捷网格预设按钮精简为黄金4强（3×3, 4×4, 4×6, 6×4），冷门移至手动微调
    labels = [btn.text() for btn in page.grid_buttons]
    assert labels == ["3×3", "4×4", "4×6", "6×4"]
    assert "1×6" not in labels
    assert "2×2" not in labels

    btn_3x3 = next(b for b in page.grid_buttons if b.text() == "3×3")
    btn_3x3.click()
    assert page.spin_rows.value() == 3
    assert page.spin_cols.value() == 3

    btn_4x4 = next(b for b in page.grid_buttons if b.text() == "4×4")
    btn_4x4.click()
    assert page.spin_rows.value() == 4
    assert page.spin_cols.value() == 4

    btn_4x6 = next(b for b in page.grid_buttons if b.text() == "4×6")
    btn_4x6.click()
    assert page.spin_rows.value() == 4
    assert page.spin_cols.value() == 6

    btn_6x4 = next(b for b in page.grid_buttons if b.text() == "6×4")
    btn_6x4.click()
    assert page.spin_rows.value() == 6
    assert page.spin_cols.value() == 4

    # 验证背景模式三态单选控件
    assert page.rb_bg_transparent.isChecked() is True
    assert page.get_bg_mode() == "transparent"

    page.rb_bg_scene.click()
    assert page.get_bg_mode() == "scene"

    page.rb_bg_auto.click()
    assert page.get_bg_mode() == "auto"

    page.set_bg_mode("transparent")
    assert page.get_bg_mode() == "transparent"

    page._set_grid(2, 2)
    page.edit_hint.setText("眨眼")
    page.edit_prompt.setPlainText("blink sheet")
    page._save()
    assert len(page.store.list()) == 1
    assert page.store.list()[0].grid == "2x2"
    page.reload_list()
    assert page.list_widget.count() == 1
    page.list_widget.setCurrentRow(0)
    page._on_select(page.list_widget.item(0))
    page._copy()
    out = tmp_path / "e.json"
    page.store.export_json(out)
    page.store.import_json(out)
    page._on_refine()
    page._notify("x")
    page._on_refine_ok("refined prompt text")
    assert page.edit_prompt.toPlainText() == "refined prompt text"
    page._on_refine_fail("认证失败")


def test_settings_page_theme_persist(qapp, tmp_path):
    from src.gifcreater.config.settings import SettingsManager
    from src.gifcreater.ui.settings_page import SettingsPage

    from src.gifcreater.config.settings import AppConfig

    mgr = SettingsManager(tmp_path / "gifcreater-settings.json")
    mgr.save(AppConfig(theme="light"))
    page = SettingsPage(mgr)
    assert page.radio_light.isChecked()
    page.radio_light.setChecked(True)
    page._persist_theme()
    assert mgr.load().theme == "light"
    page.sync_from_manager()
    page.combo_provider.setCurrentIndex(1)
    page._on_provider_changed()
    page._save_all()
    loaded = mgr.load()
    assert loaded.provider == "openai" or "openai" in loaded.base_url
    from src.gifcreater.config.secrets import FakeProtector, SecretStore

    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page2 = SettingsPage(mgr, secrets=secrets)
    page2.edit_key.setText("sk-new")
    page2._save_all()
    assert secrets.load_key() == "sk-new"
    assert page2.combo_model.count() > 0
    page2.search_model.setText("gpt-4o")
    page2._on_model_search()
    texts = [page2.combo_model.itemText(i) for i in range(page2.combo_model.count())]
    assert texts
    assert any("gpt-4o" in t.lower() for t in texts)


def test_main_window_headless(qapp, tmp_path):
    """测试主窗口生命周期与素材加载"""
    win = MainWindow()
    assert win.windowTitle().startswith("🎞️ GifCreater")
    assert not win.windowIcon().isNull()

    # 验证工作区 QSplitter 自适应
    assert win.work_splitter is not None
    assert win.work_splitter.count() == 2
    assert win.work_splitter.widget(1) == win.sidebar
    assert win.work_splitter.sizes()[1] > 0

    # 创建测试图并载入
    img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    img_path = tmp_path / "test_load.png"
    img.save(img_path)

    win.load_image_file(img_path)
    assert win.current_pil_image is not None
    assert win.current_grid is not None
    assert win.current_grid.rows == 4  # 侧边栏默认 4 行

    # 验证智能吸附与几何均匀等分按钮交互
    assert win.sidebar.btn_auto_align is not None
    assert win.sidebar.btn_reset_grid is not None

    # 触发智能吸附对齐
    win.sidebar.btn_auto_align.click()
    assert win.current_grid is not None
    assert len(win.current_grid.col_lines) == 3

    # 触发几何均匀等分
    win.sidebar.btn_reset_grid.click()
    assert win.current_grid is not None
    assert win.current_grid.col_lines == [30, 60, 90]
    assert win.sidebar.switch_crop.isChecked() is False

    assert win.prompt_page is not None
    assert win.settings_page is not None
    win._toggle_app_theme()
    win._on_theme_changed("light")

    assert win.prompt_page is not None
    assert win.settings_page is not None
    win._toggle_app_theme()
    win._on_theme_changed("light")

