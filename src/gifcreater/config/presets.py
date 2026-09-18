"""平台导出预设定义与策略管理器 (Export Presets)

定义各大主流社交与动图平台的导出规格约束，
包含画幅、分辨率上限、体积上限与编码格式。
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class ExportPreset:
    """平台导出预设规格数据类"""
    key: str
    name: str
    description: str
    format: str            # 'GIF' 或 'WEBP'
    max_edge: Optional[int] = None      # 最长边限制 (None 为原画)
    max_bytes: Optional[int] = None     # 最大文件大小字节数 (None 为不限制)
    speed_factor: float = 1.0           # 播放速度缩放倍数 (微信表情通常加速至 1.2x)
    target_aspect: Optional[str] = None # 目标画幅比例 (如 '1:1', '3:4')


# 预设集合
PRESETS: Dict[str, ExportPreset] = {
    "wechat": ExportPreset(
        key="wechat",
        name="💬 微信表情包",
        description="最长边 ≤240px，体积 ≤500KB，自适应调色板收敛",
        format="GIF",
        max_edge=240,
        max_bytes=500 * 1024,
        speed_factor=1.2,
        target_aspect="1:1",
    ),
    "xiaohongshu": ExportPreset(
        key="xiaohongshu",
        name="📱 小红书 / 社交动态",
        description="竖版 3:4 比例，1080px 高清动图",
        format="GIF",
        max_edge=1080,
        target_aspect="3:4",
    ),
    "hd_gif": ExportPreset(
        key="hd_gif",
        name="🌟 原画超清 GIF",
        description="保持原始单格分辨率与全色彩阶，无额外压缩",
        format="GIF",
        max_edge=None,
        max_bytes=None,
    ),
    "webp": ExportPreset(
        key="webp",
        name="⚡ 高保真 WebP",
        description="体积减半的现代网页动图格式，极高保真度",
        format="WEBP",
        max_edge=None,
        max_bytes=None,
    ),
}

DEFAULT_PRESET_KEY = "wechat"


def get_preset(key: str) -> ExportPreset:
    """获取指定 key 的预设，若不存在则回退至默认预设。"""
    return PRESETS.get(key, PRESETS[DEFAULT_PRESET_KEY])


def list_preset_items() -> list[tuple[str, str, str]]:
    """返回供 UI 下拉框渲染的预设元组列表: (key, name, description)"""
    return [(p.key, p.name, p.description) for p in PRESETS.values()]
