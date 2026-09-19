# -*- coding: utf-8 -*-
"""
GifCreater 异步工作线程调度层 (Worker Threads)
==============================================

基于 QThread 封装计算密集型任务，彻底隔离主 UI 事件循环：
- SliceWorker: 网格切片与去黑边异步处理
- ExportWorker: 微信表情包自适应调色板试探压缩、GIF / WebP 导出
"""

from typing import List, Optional
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

from ..core import (
    GridConfig,
    CaptionConfig,
    slice_image,
    compress_wechat_gif,
    generate_boomerang_sequence,
    export_gif,
    export_webp,
    save_to_disk,
    apply_caption_to_frames,
)
from ..utils.paths import get_default_output_dirs


class SliceWorker(QThread):
    """
    异步切片工作线程：在后台执行图像网格拆分与黑边吸附
    """
    progressChanged = pyqtSignal(int)          # 进度百分比 (0-100)
    stageChanged = pyqtSignal(str)             # 阶段描述
    sliceFinished = pyqtSignal(list, object)   # (List[Image.Image], GridConfig)
    sliceFailed = pyqtSignal(str)              # 错误消息

    def __init__(self, image: Image.Image, grid: GridConfig, smart_crop: bool = True, parent=None):
        super().__init__(parent)
        self.image = image
        self.grid = grid
        self.smart_crop = smart_crop

    def run(self):
        try:
            self.stageChanged.emit("正在解析切片网格与边缘探测...")
            self.progressChanged.emit(20)

            # 调用无头算法引擎
            self.stageChanged.emit("正在分割单帧图像...")
            self.progressChanged.emit(50)
            frames = slice_image(self.image, self.grid, smart_crop=self.smart_crop)

            self.stageChanged.emit(f"切片完成，共生成 {len(frames)} 帧")
            self.progressChanged.emit(100)
            self.sliceFinished.emit(frames, self.grid)
        except Exception as e:
            self.sliceFailed.emit(str(e))


class ExportWorker(QThread):
    """
    异步动图导出工作线程：执行自适应调色板探针计算、配文叠加与文件写出
    """
    progressChanged = pyqtSignal(int)
    stageChanged = pyqtSignal(str)
    exportFinished = pyqtSignal(str, int)      # (output_path, size_bytes)
    exportFailed = pyqtSignal(str)

    def __init__(
        self,
        frames: List[Image.Image],
        preset: str = "wechat",
        duration: int = 350,
        end_pause: int = 1500,
        boomerang: bool = False,
        base_name: str = "animation",
        caption_text: Optional[str] = None,
        caption_pos: str = "bottom",
        caption_config: Optional[CaptionConfig] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.frames = frames
        self.preset = preset.lower()  # "wechat", "xiaohongshu", "hd_gif", "gif", "webp"
        self.duration = duration
        self.end_pause = end_pause
        self.boomerang = boomerang
        self.base_name = base_name
        self.caption_text = caption_text
        self.caption_pos = caption_pos
        self.caption_config = caption_config

    def run(self):
        try:
            if not self.frames:
                raise ValueError("没有可导出的有效帧")

            self.stageChanged.emit("准备生成动图数据...")
            self.progressChanged.emit(10)

            # 叠加表情包文字配文 (若指定)
            export_frames = list(self.frames)
            if self.caption_config and self.caption_config.text:
                export_frames = apply_caption_to_frames(export_frames, self.caption_config)
            elif self.caption_text and self.caption_text.strip():
                export_frames = apply_caption_to_frames(
                    export_frames, self.caption_text.strip(), position=self.caption_pos
                )


            # 构建帧间隔列表
            durations = [self.duration] * len(export_frames)
            if self.end_pause > 0 and len(durations) > 0:
                durations[-1] = self.end_pause

            # 获取输出目录
            gifs_dir, _ = get_default_output_dirs()

            if self.preset == "wechat":
                self.stageChanged.emit("正在进行微信表情包自适应调色板试探压缩 (<=500KB, <=240px)...")
                self.progressChanged.emit(30)
                # 若开启乒乓往复，展开序列
                if self.boomerang:
                    wc_frames, wc_durations = generate_boomerang_sequence(export_frames, durations)
                else:
                    wc_frames, wc_durations = list(export_frames), list(durations)

                data = compress_wechat_gif(
                    frames=wc_frames,
                    durations=wc_durations,
                    max_size_bytes=500 * 1024,
                    max_side=240,
                )
                self.progressChanged.emit(85)
                filename = f"{self.base_name}_wechat.gif"
                target_path = gifs_dir / filename
                saved_path = save_to_disk(data, target_path)

            elif self.preset == "xiaohongshu":
                self.stageChanged.emit("正在生成小红书 3:4 社交高清动图...")
                self.progressChanged.emit(40)
                max_edge = 1080
                w0, h0 = export_frames[0].size
                if max(w0, h0) > max_edge:
                    scale = max_edge / max(w0, h0)
                    target_w = max(1, int(round(w0 * scale)))
                    target_h = max(1, int(round(h0 * scale)))
                    export_frames = [im.resize((target_w, target_h), Image.Resampling.LANCZOS) for im in export_frames]
                data = export_gif(
                    frames=export_frames,
                    durations=durations,
                    loop=0,
                    boomerang=self.boomerang,
                )
                self.progressChanged.emit(85)
                filename = f"{self.base_name}_xhs.gif"
                target_path = gifs_dir / filename
                saved_path = save_to_disk(data, target_path)

            elif self.preset == "webp":
                self.stageChanged.emit("正在编码高保真 WebP 动图...")
                self.progressChanged.emit(40)
                data = export_webp(
                    frames=export_frames,
                    durations=durations,
                    loop=0,
                    boomerang=self.boomerang,
                )
                self.progressChanged.emit(85)
                filename = f"{self.base_name}.webp"
                target_path = gifs_dir / filename
                saved_path = save_to_disk(data, target_path)

            else:  # hd_gif / original gif
                self.stageChanged.emit("正在生成高清原画 GIF...")
                self.progressChanged.emit(40)
                data = export_gif(
                    frames=export_frames,
                    durations=durations,
                    loop=0,
                    boomerang=self.boomerang,
                )
                self.progressChanged.emit(85)
                filename = f"{self.base_name}_hd.gif"
                target_path = gifs_dir / filename
                saved_path = save_to_disk(data, target_path)

            size_bytes = len(data)
            self.stageChanged.emit(f"导出成功！体积: {size_bytes / 1024:.1f} KB")
            self.progressChanged.emit(100)
            self.exportFinished.emit(str(saved_path), size_bytes)

        except Exception as e:
            self.exportFailed.emit(str(e))


class RefineWorker(QThread):
    refineFinished = pyqtSignal(str)
    refineFailed = pyqtSignal(str)

    def __init__(
        self,
        inspiration: str,
        current_prompt: str,
        rows: int,
        cols: int,
        base_url: str,
        api_key: str,
        model: str,
        parent=None,
    ):
        super().__init__(parent)
        self.inspiration = inspiration
        self.current_prompt = current_prompt
        self.rows = rows
        self.cols = cols
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def run(self):
        from ..core.agent_engine import AgentError, GenerationBrief, StoryboardPipeline

        try:
            if self.isInterruptionRequested():
                return
            pipeline = StoryboardPipeline()
            result = pipeline.run(
                GenerationBrief(
                    inspiration=self.inspiration,
                    current_prompt=self.current_prompt,
                    rows=self.rows,
                    cols=self.cols,
                ),
                base_url=self.base_url,
                api_key=self.api_key,
                model=self.model,
            )
            if self.isInterruptionRequested():
                return
            self.refineFinished.emit(result.full_prompt)
        except AgentError as exc:
            self.refineFailed.emit(str(exc))
        except Exception:
            self.refineFailed.emit("完善失败")

