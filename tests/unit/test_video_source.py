# -*- coding: utf-8 -*-
"""core/video_source.py 单元测试：用动态编码的微型视频验证「帧级精确」。"""

import wave

import pytest

from src.gifcreater.core import video_source
from src.gifcreater.core.video_source import (
    VideoCancelled,
    VideoError,
    VideoReader,
    grid_frame_count,
    probe_video,
)
from tests.fixtures.mock_video import index_from_image, make_color_video


@pytest.fixture()
def video(tmp_path):
    return make_color_video(tmp_path / "clip.mp4", n=12, size=(64, 48), fps=10)


def test_probe_video_metadata(video):
    info = probe_video(video)
    assert (info.width, info.height) == (64, 48)
    assert info.frame_count == 12
    assert info.fps == pytest.approx(10.0, rel=0.01)
    assert info.duration_s == pytest.approx(1.2, abs=0.05)
    assert info.rotation == 0


def test_every_frame_is_exact(video):
    with VideoReader(video) as r:
        for i in range(12):
            assert index_from_image(r.get_frame_by_index(i)) == i


def test_random_access_is_exact(video):
    """乱序、回退、重复读取都必须取到正确帧（覆盖顺推与 seek 两条路径）。"""
    with VideoReader(video) as r:
        for i in (11, 0, 5, 6, 7, 3, 3, 9, 1, 10):
            assert index_from_image(r.get_frame_by_index(i)) == i


def test_seek_path_when_forward_window_is_tiny(video, monkeypatch):
    monkeypatch.setattr(video_source, "_FORWARD_WINDOW", 1)
    with VideoReader(video) as r:
        for i in (0, 4, 8, 2, 11, 6):
            assert index_from_image(r.get_frame_by_index(i)) == i


def test_get_frame_at_uses_floor_and_clamps(video):
    with VideoReader(video) as r:
        assert index_from_image(r.get_frame_at(0.0)) == 0
        assert index_from_image(r.get_frame_at(0.35)) == 3
        assert index_from_image(r.get_frame_at(0.4)) == 4
        assert index_from_image(r.get_frame_at(-5)) == 0
        assert index_from_image(r.get_frame_at(999)) == 11
        assert r.index_at(-1) == 0
        assert r.index_at(999) == 11
        assert r.index_by_clamp(-3) == 0
        assert r.index_by_clamp(99) == 11


def test_frame_index_is_clamped(video):
    with VideoReader(video) as r:
        assert index_from_image(r.get_frame_by_index(-4)) == 0
        assert index_from_image(r.get_frame_by_index(500)) == 11


def test_time_of_index(video):
    with VideoReader(video) as r:
        assert r.time_of_index(0) == pytest.approx(0.0, abs=1e-6)
        assert r.time_of_index(5) == pytest.approx(0.5, abs=1e-3)
        assert r.time_of_index(999) == pytest.approx(1.1, abs=1e-3)


def test_neighbors_middle_and_edges(video):
    with VideoReader(video) as r:
        mid = r.neighbors(5, radius=2, max_edge=32)
        assert [i for i, _ in mid] == [3, 4, 5, 6, 7]
        for i, thumb in mid:
            assert max(thumb.size) <= 32
            assert index_from_image(thumb) == i
        assert [i for i, _ in r.neighbors(0, radius=2)] == [0, 1, 2]
        assert [i for i, _ in r.neighbors(11, radius=2)] == [9, 10, 11]


def test_sample_evenly_picks_expected_frames(video):
    with VideoReader(video) as r:
        frames = r.sample_evenly(4)
        assert [index_from_image(f) for f in frames] == [0, 4, 7, 11]
        assert len(r.sample_evenly(1)) == 1
        assert index_from_image(r.sample_evenly(1)[0]) == 0
        # 帧数不足时允许重复取帧，保证张数等于网格格数
        assert len(r.sample_evenly(20)) == 20
        # 指定区间
        sub = r.sample_evenly(3, t_start=0.4, t_end=0.8)
        assert [index_from_image(f) for f in sub] == [4, 6, 8]


def test_sample_evenly_max_edge_progress_and_cancel(video):
    with VideoReader(video) as r:
        calls = []
        frames = r.sample_evenly(
            3, max_edge=16, progress=lambda done, total: calls.append((done, total))
        )
        assert all(max(f.size) <= 16 for f in frames)
        assert calls == [(1, 3), (2, 3), (3, 3)]
        with pytest.raises(VideoCancelled):
            r.sample_evenly(5, should_cancel=lambda: True)
        with pytest.raises(ValueError):
            r.sample_evenly(0)


def test_grid_frame_count():
    assert grid_frame_count(3, 3) == 9
    assert grid_frame_count(4, 6) == 24
    assert grid_frame_count(6, 4) == 24
    with pytest.raises(ValueError):
        grid_frame_count(0, 3)


def test_variable_frame_rate_maps_by_pts(tmp_path):
    """变帧率视频：帧索引必须按 pts 对齐，而不是按 fps 推算。"""
    path = make_color_video(tmp_path / "vfr.mp4", fps=10, pts_list=[0, 1, 3, 4, 8, 9, 10, 11], bframes=0)
    with VideoReader(path) as r:
        assert r.info.frame_count == 8
        for i in range(8):
            assert index_from_image(r.get_frame_by_index(i)) == i
        # 第 3 帧 pts=4 -> 0.4s；0.55s 仍应落在第 3 帧
        assert index_from_image(r.get_frame_at(0.55)) == 3
        assert index_from_image(r.get_frame_at(0.8)) == 4


def test_webm_container_is_supported(tmp_path):
    path = make_color_video(tmp_path / "clip.webm", n=8, codec="libvpx")
    with VideoReader(path) as r:
        assert r.info.frame_count == 8
        assert index_from_image(r.get_frame_by_index(5)) == 5


def test_rotation_metadata_is_applied(video, monkeypatch):
    monkeypatch.setattr(video_source, "_frame_rotation", lambda frame: 90)
    with VideoReader(video) as r:
        assert r.info.rotation == 90
        assert (r.info.width, r.info.height) == (48, 64)
        img = r.get_frame_by_index(2)
        assert img.size == (48, 64)
        assert index_from_image(img) == 2
        assert all(t.size[0] <= t.size[1] for _, t in r.neighbors(2, radius=1))


@pytest.mark.parametrize("deg,expected", [(0, 0), (90, 90), (-90, 270), (180, 180), (270, 270), (45, 0), (360, 0)])
def test_normalize_rotation(deg, expected):
    assert video_source._normalize_rotation(deg) == expected


def test_rotation_180_keeps_size(video, monkeypatch):
    monkeypatch.setattr(video_source, "_frame_rotation", lambda frame: 180)
    with VideoReader(video) as r:
        assert r.get_frame_by_index(1).size == (64, 48)


def test_missing_file_raises_video_error(tmp_path):
    with pytest.raises(VideoError):
        VideoReader(tmp_path / "nope.mp4")


def test_garbage_file_raises_video_error(tmp_path):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"this is definitely not a video" * 20)
    with pytest.raises(VideoError):
        VideoReader(bad)


def test_audio_only_file_has_no_video_stream(tmp_path):
    wav = tmp_path / "sound.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 800)
    with pytest.raises(VideoError, match="视频"):
        VideoReader(wav)


def test_closed_reader_raises_and_close_is_idempotent(video):
    r = VideoReader(video)
    r.close()
    r.close()
    with pytest.raises(VideoError):
        r.get_frame_by_index(0)


def test_normalize_rotation_invalid():
    assert video_source._normalize_rotation("not_a_number") == 0


def test_frame_rotation_none():
    class DummyFrame:
        rotation = None

    assert video_source._frame_rotation(DummyFrame()) == 0


def test_sample_evenly_cancel_midway(video):
    with VideoReader(video) as r:
        called = 0

        def should_cancel():
            nonlocal called
            called += 1
            return called > 1

        with pytest.raises(VideoCancelled):
            r.sample_evenly(5, should_cancel=should_cancel)


def test_cache_hit_returns_copy(video):
    with VideoReader(video) as r:
        f1 = r.get_frame_by_index(2)
        f2 = r.get_frame_by_index(2)
        assert f1 is not f2
        assert index_from_image(f1) == 2


def test_empty_pts_raises(video, monkeypatch):
    monkeypatch.setattr(VideoReader, "_build_pts_index", lambda self: ([], []))
    with pytest.raises(VideoError, match="未包含任何有效帧"):
        VideoReader(video)


def test_first_frame_none_raises(video, monkeypatch):
    monkeypatch.setattr(VideoReader, "_read_next_decoded_frame", lambda self: None)
    with pytest.raises(VideoError, match="无法从视频流中解码有效帧"):
        VideoReader(video)


def test_close_exception_handled(video):
    with VideoReader(video) as r:
        class FakeContainer:
            def close(self):
                raise RuntimeError("fail")
        r._container = FakeContainer()
        r.close()
        assert r._is_closed


def test_seek_failure_raises_video_error(video):
    with VideoReader(video) as r:
        r._last_idx = 10  # 强制使 can_forward 为 False

        class FailContainer:
            def seek(self, *args, **kwargs):
                raise RuntimeError("seek failed")

        r._container = FailContainer()
        with pytest.raises(VideoError, match="Seek 失败"):
            r.get_frame_by_index(5)


def test_decode_frame_failure_raises(video, monkeypatch):
    with VideoReader(video) as r:
        r._last_idx = None
        r._last_img = None
        monkeypatch.setattr(r, "_read_next_decoded_frame", lambda: None)
        with pytest.raises(VideoError, match="未能解码出第"):
            r.get_frame_by_index(5)



