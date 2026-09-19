# -*- coding: utf-8 -*-
"""
tests/unit/test_workers.py
异步工作线程 (SliceWorker / ExportWorker) 单元测试
"""

import os
from PIL import Image, ImageSequence
import pytest
from PyQt6.QtCore import QObject

from src.gifcreater.core import GridConfig
from src.gifcreater.ui.workers import SliceWorker, ExportWorker
from tests.fixtures.mock_images import create_dummy_grid_image


def test_slice_worker_success(qapp):
    """测试 SliceWorker 正常切片成功发射信号"""
    pil_img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    grid = GridConfig(rows=2, cols=2, col_lines=[60], row_lines=[60])

    worker = SliceWorker(image=pil_img, grid=grid, smart_crop=False)

    finished_results = []
    worker.sliceFinished.connect(lambda frames, cfg: finished_results.append((frames, cfg)))

    worker.run()

    assert len(finished_results) == 1
    frames, cfg = finished_results[0]
    assert len(frames) == 4
    assert cfg.rows == 2


def test_slice_worker_failure(qapp):
    """测试 SliceWorker 在异常输入时发射 sliceFailed"""
    worker = SliceWorker(image=None, grid=None)

    failed_msgs = []
    worker.sliceFailed.connect(lambda msg: failed_msgs.append(msg))

    worker.run()

    assert len(failed_msgs) == 1
    assert "切片" in failed_msgs[0] or "失败" in failed_msgs[0] or "None" in failed_msgs[0]


def test_export_worker_wechat_duration_and_pause(qapp, tmp_path):
    """测试 ExportWorker 导出微信表情包保持用户指定的 duration 与 end_pause"""
    frames = [Image.new("RGB", (60, 60), (i * 40, 50, 50)) for i in range(3)]
    worker = ExportWorker(
        frames=frames,
        preset="wechat",
        duration=350,
        end_pause=1500,
        boomerang=False,
        base_name="test_export_wc",
    )

    finished_results = []
    worker.exportFinished.connect(lambda p, sz: finished_results.append((p, sz)))

    worker.run()

    assert len(finished_results) == 1
    out_path, sz = finished_results[0]
    assert os.path.exists(out_path)
    assert sz > 0

    with Image.open(out_path) as im:
        assert im.format == "GIF"
        durs = [f.info.get("duration", 0) for f in ImageSequence.Iterator(im)]
        # 3 帧：前两帧 350ms，末尾帧 1500ms
        assert durs == [350, 350, 1500]


def test_export_worker_wechat_boomerang(qapp):
    """测试 ExportWorker 导出微信表情包支持乒乓往复展开"""
    frames = [Image.new("RGB", (60, 60), (i * 40, 50, 50)) for i in range(3)]
    worker = ExportWorker(
        frames=frames,
        preset="wechat",
        duration=250,
        end_pause=0,
        boomerang=True,
        base_name="test_export_wc_boom",
    )

    finished_results = []
    worker.exportFinished.connect(lambda p, sz: finished_results.append((p, sz)))

    worker.run()

    assert len(finished_results) == 1
    out_path, sz = finished_results[0]
    assert sz > 0

    with Image.open(out_path) as im:
        # 3 帧展开为 [A, B, C, B] 共 4 帧
        out_frames = [f.copy() for f in ImageSequence.Iterator(im)]
        assert len(out_frames) == 4
        durs = [f.info.get("duration", 0) for f in ImageSequence.Iterator(im)]
        assert durs == [250, 250, 250, 250]


def test_export_worker_empty_frames(qapp):
    """测试 ExportWorker 在空列表时报错"""
    worker = ExportWorker(frames=[], preset="wechat")
    failed_msgs = []
    worker.exportFailed.connect(lambda msg: failed_msgs.append(msg))
    worker.run()

    assert len(failed_msgs) == 1
    assert "没有可导出的有效帧" in failed_msgs[0]


def test_model_fetch_worker(qapp, monkeypatch):
    """测试 ModelFetchWorker 异步获取模型列表"""
    from src.gifcreater.ui.workers import ModelFetchWorker

    # 1. 成功测试
    monkeypatch.setattr(
        "src.gifcreater.core.agent_engine.fetch_remote_models",
        lambda base_url, api_key: ["model-x", "model-y"],
    )
    worker = ModelFetchWorker("https://api.openai.com/v1", "sk-test")
    fetched = []
    worker.fetchFinished.connect(lambda m: fetched.append(m))
    worker.run()
    assert len(fetched) == 1
    assert fetched[0] == ["model-x", "model-y"]

    # 2. 失败测试
    from src.gifcreater.core.agent_engine import AgentError

    def fail_fetch(base_url, api_key):
        raise AgentError("网络不可达")

    monkeypatch.setattr("src.gifcreater.core.agent_engine.fetch_remote_models", fail_fetch)
    fail_worker = ModelFetchWorker("https://bad.url")
    errors = []
    fail_worker.fetchFailed.connect(lambda e: errors.append(e))
    fail_worker.run()
    assert len(errors) == 1
    assert "网络不可达" in errors[0]
