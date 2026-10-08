# -*- coding: utf-8 -*-
"""GifCreater 核心视频源解析模块 (Headless Video Source Layer)

提供基于 PyAV 的帧级精确解析、时间戳索引、乱序 seek、邻域预览与等距采样能力。
零 GUI 依赖，纯无头设计。
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Callable, List, Optional, Tuple, Union

import av
from PIL import Image

_FORWARD_WINDOW: int = 48  # 顺推解码最大跨度，超过此阈值触发容器 seek


class VideoError(RuntimeError):
    """视频解析或解码异常。"""


class VideoCancelled(VideoError):
    """用户或外部取消了采样/导出任务。"""


@dataclass(frozen=True)
class VideoInfo:
    """视频元数据。"""

    width: int
    height: int
    fps: float
    duration_s: float
    frame_count: int
    rotation: int


def _normalize_rotation(deg: int) -> int:
    """规范化旋转角度，仅支持 0, 90, 180, 270 度，其余回落至 0。"""
    try:
        val = int(deg) % 360
    except (ValueError, TypeError):
        return 0
    if val in (0, 90, 180, 270):
        return val
    return 0


def _frame_rotation(frame: av.VideoFrame) -> int:
    """从解码帧读取旋转元数据。"""
    rot = getattr(frame, "rotation", 0)
    if rot is None:
        rot = 0
    return _normalize_rotation(int(rot))


def grid_frame_count(rows: int, cols: int) -> int:
    """计算网格切片或采样所需总帧数。"""
    if rows <= 0 or cols <= 0:
        raise ValueError(f"网格行数与列数必须大于 0: rows={rows}, cols={cols}")
    return rows * cols


def probe_video(path: Union[str, Path]) -> VideoInfo:
    """轻量探测视频元数据。"""
    with VideoReader(path) as reader:
        return reader.info


class VideoReader:
    """线程安全的视频逐帧精确读取器。

    支持随机访问、顺推与回退 seek、时间到帧索引映射、旋转自适应校正。
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self._path = Path(path)
        if not self._path.exists() or not self._path.is_file():
            raise VideoError(f"视频文件不存在或不可读: {self._path}")

        self._lock = threading.RLock()
        self._is_closed = False

        try:
            self._container = av.open(str(self._path))
        except Exception as e:
            raise VideoError(f"无法打开视频文件 {self._path}: {e}") from e

        video_streams = [s for s in self._container.streams if s.type == "video"]
        if not video_streams:
            self._container.close()
            self._is_closed = True
            raise VideoError(f"文件中未找到有效的视频流: {self._path}")

        self._stream = video_streams[0]
        self._time_base = float(self._stream.time_base) if self._stream.time_base else 1.0 / 1000.0

        # 构建 PTS 与 Keyframe 索引
        self._pts_list, self._key_pts_list = self._build_pts_index()
        if not self._pts_list:
            self._container.close()
            self._is_closed = True
            raise VideoError(f"视频未包含任何有效帧或时间戳: {self._path}")

        self._first_pts = self._pts_list[0]
        self._last_pts = self._pts_list[-1]
        self._pts_to_index = {pts: idx for idx, pts in enumerate(self._pts_list)}

        # 计算帧率与时长
        fps = 30.0
        if self._stream.average_rate and self._stream.average_rate > 0:
            fps = float(self._stream.average_rate)
        elif self._stream.base_rate and self._stream.base_rate > 0:
            fps = float(self._stream.base_rate)
        elif len(self._pts_list) > 1:
            span_s = (self._last_pts - self._first_pts) * self._time_base
            if span_s > 0:
                fps = (len(self._pts_list) - 1) / span_s

        duration_s = (self._last_pts - self._first_pts) * self._time_base + (1.0 / fps)

        # 预先计算每帧相对第 0 帧的时间偏移
        self._rel_times = [(pts - self._first_pts) * self._time_base for pts in self._pts_list]

        # 解码首帧以提取旋转元数据与原始尺寸
        self._decoder = self._container.decode(self._stream)
        first_frame = self._read_next_decoded_frame()
        if first_frame is None:
            self._container.close()
            self._is_closed = True
            raise VideoError(f"无法从视频流中解码有效帧: {self._path}")

        self._rotation = _frame_rotation(first_frame)
        raw_w = first_frame.width
        raw_h = first_frame.height

        if self._rotation in (90, 270):
            out_w, out_h = raw_h, raw_w
        else:
            out_w, out_h = raw_w, raw_h

        self.info = VideoInfo(
            width=out_w,
            height=out_h,
            fps=fps,
            duration_s=duration_s,
            frame_count=len(self._pts_list),
            rotation=self._rotation,
        )

        # 缓存当前解码状态
        first_img = self._convert_and_rotate(first_frame)
        self._last_idx = 0
        self._last_img = first_img

    def _build_pts_index(self) -> Tuple[List[int], List[int]]:
        """扫描容器中所有视频 packet 的 pts 与关键帧，构建排序索引。"""
        pts_set = set()
        key_pts_set = set()
        for pkt in self._container.demux(self._stream):
            p = pkt.pts if pkt.pts is not None else pkt.dts
            if p is not None:
                pts_set.add(p)
                if pkt.is_keyframe:
                    key_pts_set.add(p)
        # 扫描完毕后必须 seek 回起点
        try:
            self._container.seek(0)
        except Exception:
            pass
        pts_list = sorted(pts_set)
        key_pts_list = sorted(key_pts_set)
        if pts_list and (not key_pts_list or pts_list[0] not in key_pts_set):
            key_pts_list.insert(0, pts_list[0])
        return pts_list, key_pts_list

    def _convert_and_rotate(self, frame: av.VideoFrame) -> Image.Image:
        """将解码帧转为 PIL 图像并按旋转元数据调整。"""
        img = frame.to_image()
        if self._rotation == 90:
            return img.transpose(Image.Transpose.ROTATE_270)
        elif self._rotation == 180:
            return img.transpose(Image.Transpose.ROTATE_180)
        elif self._rotation == 270:
            return img.transpose(Image.Transpose.ROTATE_90)
        return img

    def _read_next_decoded_frame(self) -> Optional[av.VideoFrame]:
        """安全读取生成器的下一帧。"""
        try:
            return next(self._decoder)
        except (StopIteration, Exception):
            return None

    def index_by_clamp(self, index: int) -> int:
        """限制索引在合法范围 [0, frame_count - 1] 内。"""
        if index < 0:
            return 0
        if index >= self.info.frame_count:
            return self.info.frame_count - 1
        return index

    def time_of_index(self, index: int) -> float:
        """获取指定帧相对第 0 帧的时间偏移 (秒)。"""
        clamped = self.index_by_clamp(index)
        return self._rel_times[clamped]

    def index_at(self, t: float) -> int:
        """按 floor 语义将时间戳映射为最近的帧索引。"""
        if t <= 0:
            return 0
        if t >= self._rel_times[-1]:
            return self.info.frame_count - 1
        # 添加微小裕度 1e-7 避免浮点舍入误差
        pos = bisect.bisect_right(self._rel_times, t + 1e-7) - 1
        return self.index_by_clamp(pos)

    def get_frame_at(self, t: float) -> Image.Image:
        """获取时间戳 t (秒) 处的视频帧。"""
        idx = self.index_at(t)
        return self.get_frame_by_index(idx)

    def get_frame_by_index(self, index: int) -> Image.Image:
        """通过帧索引读取单帧图像。"""
        with self._lock:
            if self._is_closed:
                raise VideoError("VideoReader 已经关闭，无法读取帧")

            target_idx = self.index_by_clamp(index)
            if self._last_idx == target_idx and self._last_img is not None:
                return self._last_img.copy()

            target_pts = self._pts_list[target_idx]

            # 判断是否可顺推解码
            can_forward = (
                self._last_idx is not None
                and 0 < target_idx - self._last_idx <= _FORWARD_WINDOW
            )

            matched_frame: Optional[av.VideoFrame] = None
            if can_forward:
                while True:
                    frame = self._read_next_decoded_frame()
                    if frame is None:
                        break
                    if frame.pts == target_pts:
                        matched_frame = frame
                        break

            # 若不可顺推或顺推未命中目标，执行精确 keyframe seek
            if matched_frame is None:
                idx = max(0, bisect.bisect_right(self._key_pts_list, target_pts) - 1)
                seek_pts = self._key_pts_list[idx]
                try:
                    self._container.seek(seek_pts, stream=self._stream, backward=True)
                    self._decoder = self._container.decode(self._stream)
                except Exception as e:
                    raise VideoError(f"Seek 失败 (pts={seek_pts}): {e}") from e

                while True:
                    frame = self._read_next_decoded_frame()
                    if frame is None:
                        break
                    if frame.pts == target_pts:
                        matched_frame = frame
                        break

            # 如果依然未命中（容错回落）
            if matched_frame is None:
                # 尝试重置到 0 线性扫描
                try:
                    self._container.seek(0, stream=self._stream, backward=True)
                    self._decoder = self._container.decode(self._stream)
                    while True:
                        frame = self._read_next_decoded_frame()
                        if frame is None:
                            break
                        if frame.pts == target_pts:
                            matched_frame = frame
                            break
                except Exception:
                    pass

            if matched_frame is None:
                if self._last_img is not None:
                    return self._last_img.copy()
                raise VideoError(f"未能解码出第 {target_idx} 帧 (pts={target_pts})")

            img = self._convert_and_rotate(matched_frame)
            self._last_idx = target_idx
            self._last_img = img
            return img.copy()

    def neighbors(
        self, index: int, radius: int = 2, max_edge: Optional[int] = None
    ) -> List[Tuple[int, Image.Image]]:
        """获取目标索引左右邻域帧列表，可输出限制最大边长的缩略图。"""
        clamped = self.index_by_clamp(index)
        start = max(0, clamped - radius)
        end = min(self.info.frame_count - 1, clamped + radius)

        result: List[Tuple[int, Image.Image]] = []
        for i in range(start, end + 1):
            frame_img = self.get_frame_by_index(i)
            if max_edge is not None and max(frame_img.size) > max_edge:
                frame_img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            result.append((i, frame_img))
        return result

    def sample_evenly(
        self,
        n: int,
        t_start: float = 0.0,
        t_end: Optional[float] = None,
        max_edge: Optional[int] = None,
        progress: Optional[Callable[[int, int], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> List[Image.Image]:
        """在指定时间区间内均匀采样 n 帧。"""
        if n <= 0:
            raise ValueError(f"采样帧数必须大于 0: n={n}")

        if should_cancel and should_cancel():
            raise VideoCancelled("采样任务已取消")

        i0 = self.index_at(t_start)
        i1 = self.info.frame_count - 1 if t_end is None else self.index_at(t_end)
        if i1 < i0:
            i1 = i0

        if n == 1:
            indices = [i0]
        else:
            indices = [int(round(i0 + (i1 - i0) * k / (n - 1))) for k in range(n)]

        frames: List[Image.Image] = []
        for step, idx in enumerate(indices, start=1):
            if should_cancel and should_cancel():
                raise VideoCancelled("采样任务已取消")
            img = self.get_frame_by_index(idx)
            if max_edge is not None and max(img.size) > max_edge:
                img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            frames.append(img)
            if progress:
                progress(step, n)

        return frames

    def close(self) -> None:
        """关闭容器并释放解码资源 (幂等)。"""
        with self._lock:
            if not self._is_closed:
                try:
                    self._container.close()
                except Exception:
                    pass
                self._is_closed = True
                self._decoder = None
                self._last_img = None

    def __enter__(self) -> VideoReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
