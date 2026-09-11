# -*- coding: utf-8 -*-
"""
GifCreater 动画工坊 v2.0 - Graphical User Interface (GUI)
一体化桌面端：原地动图播放器 · 乒乓循环 · 微信表情包规范 · 辅助分割线预览 · 交互式删帧胶卷
"""

import os
import sys
import glob
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Tuple, List, Optional
from PIL import Image, ImageTk, ImageDraw

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import gif_tool


class GifCreaterStudio:
    def __init__(self, root: tk.Tk, initial_path: str = None):
        self.root = root
        self.root.title("GifCreater 动画工坊 v2.0")
        self.root.geometry("1060x860")
        self.root.minsize(940, 740)

        # 状态数据
        self.source_path_var = tk.StringVar()
        self.is_folder_source = False

        # 切片参数
        self.rows_var = tk.IntVar(value=4)
        self.cols_var = tk.IntVar(value=4)
        self.trim_borders_var = tk.BooleanVar(value=True)

        # 动画参数
        self.duration_var = tk.IntVar(value=350)
        self.last_pause_var = tk.IntVar(value=1500)
        self.loop_mode_var = tk.StringVar(value="normal")  # "normal" or "boomerang"
        self.export_preset_var = tk.StringVar(value="original")  # "original", "wechat", "webp"
        self.scale_var = tk.StringVar(value="1.0x (原寸切片)")

        # 交互式分割线状态
        self.col_dividers = []           # 原图像素级垂直分割线列表 (len = cols - 1)
        self.row_dividers = []           # 原图像素级水平分割线列表 (len = rows - 1)
        self.img_disp_info = None        # 画布映射: ox, oy, disp_w, disp_h, scale, orig_w, orig_h
        self.active_drag = None          # 拖动目标: ('v', idx) 或 ('h', idx)
        self.hover_target = None         # 悬停目标: ('v', idx) 或 ('h', idx)

        # 运行时状态
        self.original_pil_image = None
        self.preview_image_ref = None
        self.current_frames = []        # 当前用于播放和导出的帧路径列表
        self.backup_original_frames = [] # 删帧后的备份，支持撤销重置
        self.frame_thumbnails = []      # 底部胶卷缩略图缓存

        # 播放器核心状态
        self.is_playing = False
        self.current_frame_idx = 0
        self.play_direction = 1         # 1: 前进, -1: 倒退 (乒乓模式用)
        self._play_timer_id = None

        self._apply_styles()
        self._build_ui()

        # 绑定网格联动
        self.rows_var.trace_add("write", lambda *args: self._on_grid_param_changed())
        self.cols_var.trace_add("write", lambda *args: self._on_grid_param_changed())
        self.trim_borders_var.trace_add("write", lambda *args: self._on_grid_param_changed())
        self.loop_mode_var.trace_add("write", lambda *args: self._on_loop_mode_changed())

        # 初始化加载素材
        if initial_path and os.path.exists(initial_path):
            self.load_source(initial_path)
        else:
            candidates = glob.glob("*.png") + glob.glob("*.jpg")
            if candidates:
                self.load_source(os.path.abspath(candidates[0]))

    def _apply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg_main = "#f8fafc"
        self.root.configure(bg=bg_main)

        style.configure(".", background=bg_main, font=("Segoe UI", 9))
        style.configure("TLabel", background=bg_main)
        style.configure("TFrame", background=bg_main)
        style.configure("TLabelframe", background=bg_main)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#1e293b", background=bg_main)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#0f172a")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 8), foreground="#64748b")

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#2563eb")
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")])

        style.configure("Folder.TButton", font=("Segoe UI", 9, "bold"), foreground="white", background="#059669")
        style.map("Folder.TButton", background=[("active", "#047857")])

        style.configure("Player.TButton", font=("Segoe UI", 9, "bold"), padding=3)

    def _build_ui(self):
        main_box = ttk.Frame(self.root, padding="14")
        main_box.pack(fill=tk.BOTH, expand=True)

        # 1. 顶部标题与快速直达
        top_bar = ttk.Frame(main_box)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        title_area = ttk.Frame(top_bar)
        title_area.pack(side=tk.LEFT)
        ttk.Label(title_area, text="🎞️ GifCreater 动画工坊 v2.0", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(title_area, text="原地实时播放 · 乒乓循环 · 微信表情包硬指标(≤500KB) · 自动output归档", style="SubHeader.TLabel").pack(anchor=tk.W)

        btn_output_top = ttk.Button(top_bar, text="📂 打开成品目录 (output)", style="Folder.TButton", command=self.action_open_output)
        btn_output_top.pack(side=tk.RIGHT, pady=2)

        # 2. 素材选择行（单输入入口）
        src_box = ttk.LabelFrame(main_box, text=" 1. 载入素材 (支持网格大图 或 已有帧文件夹) ", padding="8")
        src_box.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(src_box, textvariable=self.source_path_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(src_box, text="📁 选择网格拼图...", command=self.browse_image).pack(side=tk.LEFT, padx=3)
        ttk.Button(src_box, text="📂 选择已有帧目录...", command=self.browse_folder).pack(side=tk.LEFT, padx=3)

        # 3. 中部核心区：左侧视觉与播放器 / 右侧参数与预设
        mid_pane = ttk.Frame(main_box)
        mid_pane.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # === 左侧：视觉中心与原地播放器 ===
        left_box = ttk.LabelFrame(mid_pane, text=" 2. 视觉中心与动图实时播放器 ", padding="10")
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 画布
        self.canvas = tk.Canvas(left_box, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.canvas.bind("<Configure>", lambda e: self._redraw_canvas())
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Leave>", self._on_canvas_leave)

        # 播放器控制条
        player_bar = ttk.Frame(left_box)
        player_bar.pack(fill=tk.X, pady=(0, 4))

        self.btn_play = ttk.Button(player_bar, text="▶ 播放动效", style="Player.TButton", command=self.toggle_play)
        self.btn_play.pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(player_bar, text="⏮", width=3, command=lambda: self.seek_frame(0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(player_bar, text="◀", width=3, command=lambda: self.step_frame(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(player_bar, text="▶", width=3, command=lambda: self.step_frame(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(player_bar, text="⏭", width=3, command=lambda: self.seek_frame(-1)).pack(side=tk.LEFT, padx=2)

        self.lbl_frame_counter = ttk.Label(player_bar, text="未载入动图", font=("Segoe UI", 9, "bold"), foreground="#0284c7")
        self.lbl_frame_counter.pack(side=tk.LEFT, padx=10)

        # 循环模式选择
        loop_frame = ttk.Frame(player_bar)
        loop_frame.pack(side=tk.RIGHT)
        ttk.Radiobutton(loop_frame, text="正序循环", value="normal", variable=self.loop_mode_var).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(loop_frame, text="🔁 乒乓往复 (Boomerang)", value="boomerang", variable=self.loop_mode_var).pack(side=tk.LEFT, padx=4)

        # 提示条
        self.info_status_label = ttk.Label(left_box, text="💡 提示: 红色虚线为分割线，可直接用鼠标按住拖动微调位置", foreground="#64748b")
        self.info_status_label.pack(fill=tk.X)

        # === 右侧：切片与导出预设面板 ===
        right_box = ttk.Frame(mid_pane, width=370)
        right_box.pack(side=tk.RIGHT, fill=tk.Y)
        right_box.pack_propagate(False)

        # 卡片 A: 切片配置
        sec_grid = ttk.LabelFrame(right_box, text=" 3. 网格切片设置 ", padding="10")
        sec_grid.pack(fill=tk.X, pady=(0, 8))

        rc_row = ttk.Frame(sec_grid)
        rc_row.pack(fill=tk.X, pady=3)
        ttk.Label(rc_row, text="网格:").pack(side=tk.LEFT)
        ttk.Spinbox(rc_row, from_=1, to=32, width=4, textvariable=self.rows_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(rc_row, text="行  ×").pack(side=tk.LEFT)
        ttk.Spinbox(rc_row, from_=1, to=32, width=4, textvariable=self.cols_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(rc_row, text="列").pack(side=tk.LEFT)

        self.lbl_total_frames = ttk.Label(rc_row, text="= 16 帧", foreground="#0284c7", font=("Segoe UI", 9, "bold"))
        self.lbl_total_frames.pack(side=tk.LEFT, padx=(6, 0))

        btn_realign = ttk.Button(rc_row, text="🔄 重新吸附", width=9, command=self.action_realign_dividers)
        btn_realign.pack(side=tk.RIGHT)

        # 单格切片尺寸与画面比例指示器
        dim_box = ttk.Frame(sec_grid, padding="4 2")
        dim_box.pack(fill=tk.X, pady=(2, 2))
        self.lbl_cell_dim = ttk.Label(dim_box, text="📐 单格尺寸: -- × -- px", font=("Segoe UI", 9, "bold"), foreground="#0369a1")
        self.lbl_cell_dim.pack(side=tk.LEFT)
        self.lbl_cell_ratio = ttk.Label(dim_box, text="📏 比例: --", font=("Segoe UI", 9, "bold"), foreground="#059669")
        self.lbl_cell_ratio.pack(side=tk.RIGHT)

        ttk.Checkbutton(sec_grid, text="✨ 智能识别黑边/浅色分界线 (推荐)", variable=self.trim_borders_var).pack(anchor=tk.W, pady=2)
        ttk.Label(sec_grid, text="💡 提示: 画布红虚线支持鼠标直接拖动微调", foreground="#64748b", font=("Segoe UI", 8)).pack(anchor=tk.W, pady=(0, 2))

        scale_row = ttk.Frame(sec_grid)
        scale_row.pack(fill=tk.X, pady=2)
        ttk.Label(scale_row, text="画质倍率:").pack(side=tk.LEFT)
        ttk.Combobox(scale_row, textvariable=self.scale_var, values=["1.0x (原寸切片)", "1.5x 标清", "2.0x 高清", "3.0x 超清"], state="readonly", width=16).pack(side=tk.LEFT, padx=6)

        # 卡片 B: 动画节奏
        sec_timing = ttk.LabelFrame(right_box, text=" 4. 动画播放节奏 ", padding="10")
        sec_timing.pack(fill=tk.X, pady=(0, 8))

        time_row1 = ttk.Frame(sec_timing)
        time_row1.pack(fill=tk.X, pady=2)
        ttk.Label(time_row1, text="帧间隔:").pack(side=tk.LEFT)
        ttk.Spinbox(time_row1, from_=30, to=5000, increment=20, width=6, textvariable=self.duration_var, command=self._on_duration_changed).pack(side=tk.LEFT, padx=6)
        ttk.Label(time_row1, text="ms (毫秒)").pack(side=tk.LEFT)

        self.pause_row = ttk.Frame(sec_timing)
        self.pause_row.pack(fill=tk.X, pady=2)
        ttk.Label(self.pause_row, text="尾帧停顿:").pack(side=tk.LEFT)
        self.spin_last_pause = ttk.Spinbox(self.pause_row, from_=0, to=10000, increment=100, width=6, textvariable=self.last_pause_var)
        self.spin_last_pause.pack(side=tk.LEFT, padx=6)
        self.lbl_pause_unit = ttk.Label(self.pause_row, text="ms (乒乓模式自动禁用)")
        self.lbl_pause_unit.pack(side=tk.LEFT)

        # 卡片 C: 导出目标预设 (带微信硬指标)
        sec_export = ttk.LabelFrame(right_box, text=" 5. 导出规格预设 ", padding="10")
        sec_export.pack(fill=tk.X, pady=(0, 8))

        ttk.Radiobutton(sec_export, text="🌟 原画高质量 GIF (完整色彩/自然原寸)", value="original", variable=self.export_preset_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(sec_export, text="💬 微信自定义表情规范 (长边240px · ≤500KB)", value="wechat", variable=self.export_preset_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(sec_export, text="⚡ 现代高保真 WebP (全彩1600万色 · 体积减半)", value="webp", variable=self.export_preset_var).pack(anchor=tk.W, pady=2)

        # 卡片 D: 操作执行
        act_box = ttk.Frame(right_box)
        act_box.pack(fill=tk.X, pady=4)

        self.btn_generate = ttk.Button(act_box, text="🚀 一键拆解并合成动图", style="Primary.TButton", command=self.action_process_all)
        self.btn_generate.pack(fill=tk.X, ipady=4, pady=(0, 4))

        sub_btns = ttk.Frame(act_box)
        sub_btns.pack(fill=tk.X)
        self.btn_split_only = ttk.Button(sub_btns, text="🔪 仅拆解单帧", command=self.action_split_only)
        self.btn_split_only.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.btn_merge_only = ttk.Button(sub_btns, text="🎞️ 仅合成当前帧", command=self.action_merge_current_frames)
        self.btn_merge_only.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # 进度条与状态显示
        self.progressbar = ttk.Progressbar(right_box, mode="determinate")
        self.progressbar.pack(fill=tk.X, pady=(6, 2))
        self.lbl_task_status = ttk.Label(right_box, text="成品自动归档于 output/ 目录", foreground="#64748b", font=("Segoe UI", 8))
        self.lbl_task_status.pack(fill=tk.X)

        # 4. 底部：交互式序列帧胶卷 (支持直接删废帧与重置)
        gallery_outer = ttk.LabelFrame(main_box, text=" 6. 序列帧胶卷 (支持点击 ❌ 删废帧；双击大图查看；删帧后动图自动重构) ", padding="6")
        gallery_outer.pack(fill=tk.X)

        top_film_bar = ttk.Frame(gallery_outer)
        top_film_bar.pack(fill=tk.X, pady=(0, 2))
        self.lbl_film_summary = ttk.Label(top_film_bar, text="当前未切分单帧", font=("Segoe UI", 8, "bold"), foreground="#475569")
        self.lbl_film_summary.pack(side=tk.LEFT)
        self.btn_restore_frames = ttk.Button(top_film_bar, text="↩ 恢复已删帧", width=12, command=self.restore_frames, state=tk.DISABLED)
        self.btn_restore_frames.pack(side=tk.RIGHT)

        self.gallery_canvas = tk.Canvas(gallery_outer, height=92, bg="#f1f5f9", highlightthickness=0)
        self.gallery_scrollbar = ttk.Scrollbar(gallery_outer, orient=tk.HORIZONTAL, command=self.gallery_canvas.xview)
        self.gallery_canvas.configure(xscrollcommand=self.gallery_scrollbar.set)

        self.gallery_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.gallery_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.gallery_inner = ttk.Frame(self.gallery_canvas)
        self.gallery_canvas.create_window((0, 0), window=self.gallery_inner, anchor="nw")
        self.gallery_inner.bind("<Configure>", lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))

    # ================= 业务与数据联动 =================

    def get_current_cell_dimensions(self) -> Tuple[int, int, str, str]:
        """计算当前网格设置或分割线下，单格的平均切片尺寸与画面长宽比例"""
        if not self.original_pil_image:
            return 0, 0, "--:--", "未载入素材"

        orig_w, orig_h = self.original_pil_image.size
        r = max(1, self.rows_var.get())
        c = max(1, self.cols_var.get())

        if self.col_dividers and len(self.col_dividers) == c - 1:
            col_widths = []
            prev = 0
            for vx in sorted(self.col_dividers):
                col_widths.append(vx - prev)
                prev = vx
            col_widths.append(orig_w - prev)
            cell_w = max(1, int(round(sum(col_widths) / len(col_widths))))
        else:
            cell_w = max(1, int(round(orig_w / float(c))))

        if self.row_dividers and len(self.row_dividers) == r - 1:
            row_heights = []
            prev = 0
            for hy in sorted(self.row_dividers):
                row_heights.append(hy - prev)
                prev = hy
            row_heights.append(orig_h - prev)
            cell_h = max(1, int(round(sum(row_heights) / len(row_heights))))
        else:
            cell_h = max(1, int(round(orig_h / float(r))))

        ratio_str, desc = gif_tool.get_aspect_ratio_info(cell_w, cell_h)
        return cell_w, cell_h, ratio_str, desc

    def update_cell_dimension_display(self):
        """刷新侧边栏单格尺寸与比例卡片"""
        cell_w, cell_h, ratio_str, desc = self.get_current_cell_dimensions()
        if cell_w <= 0 or cell_h <= 0:
            self.lbl_cell_dim.configure(text="📐 单格尺寸: -- × -- px")
            self.lbl_cell_ratio.configure(text="📏 比例: --")
        else:
            self.lbl_cell_dim.configure(text=f"📐 单格尺寸: {cell_w} × {cell_h} px")
            self.lbl_cell_ratio.configure(text=f"📏 比例: {ratio_str} ({desc})")

    def recompute_dividers(self):
        """重新智能识别网格分割线位置"""
        if not self.original_pil_image:
            self.col_dividers = []
            self.row_dividers = []
            self.update_cell_dimension_display()
            return
        r = max(1, self.rows_var.get())
        c = max(1, self.cols_var.get())
        xs, ys = gif_tool.get_grid_divider_coords(
            self.original_pil_image,
            rows=r,
            cols=c,
            auto_trim_borders=self.trim_borders_var.get()
        )
        self.col_dividers = list(xs)
        self.row_dividers = list(ys)
        self.update_cell_dimension_display()

    def action_realign_dividers(self):
        """用户点击按钮：重新自动吸附分割线"""
        if not self.original_pil_image:
            messagebox.showinfo("提示", "请先载入网格大图！")
            return
        self.recompute_dividers()
        self._redraw_canvas()
        self.info_status_label.configure(text="🔄 已重新智能吸附分割线！支持直接鼠标拖拽红线微调位置")

    def _on_grid_param_changed(self):
        r = max(1, self.rows_var.get())
        c = max(1, self.cols_var.get())
        total = r * c
        self.lbl_total_frames.configure(text=f"= {total} 帧")
        self.btn_split_only.configure(text=f"🔪 仅拆解 {total} 帧")
        self.btn_generate.configure(text=f"🚀 一键拆解 ({total} 帧) 并合成动图")
        # 如果当前显示的是静态大图，重新计算分割线并重绘画布
        if self.original_pil_image and not self.is_playing and not self.current_frames:
            self.recompute_dividers()
            self._redraw_canvas()

    def _on_loop_mode_changed(self):
        mode = self.loop_mode_var.get()
        if mode == "boomerang":
            self.spin_last_pause.configure(state=tk.DISABLED)
            self.lbl_pause_unit.configure(text="ms (乒乓模式已停用尾帧)")
        else:
            self.spin_last_pause.configure(state=tk.NORMAL)
            self.lbl_pause_unit.configure(text="ms (结局停留)")

    def _on_duration_changed(self):
        # 调速滑块/微调时，如果正在播放，立即应用新速度
        if self.is_playing:
            self.pause()
            self.play()

    def browse_image(self):
        p = filedialog.askopenfilename(
            title="选择网格大图",
            filetypes=[("支持的图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有文件", "*.*")]
        )
        if p:
            self.load_source(p, is_folder=False)

    def browse_folder(self):
        f = filedialog.askdirectory(title="选择包含单帧序列的文件夹")
        if f:
            self.load_source(f, is_folder=True)

    def load_source(self, path: str, is_folder: bool = False):
        self.pause()
        self.source_path_var.set(path)
        self.is_folder_source = is_folder

        if is_folder or os.path.isdir(path):
            self.is_folder_source = True
            # 直接载入文件夹内的序列
            patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp", "*.PNG", "*.JPG", "*.JPEG", "*.WEBP", "*.BMP"]
            found = []
            for pat in patterns:
                found.extend(glob.glob(os.path.join(path, pat)))
            found = list(set(found))
            found.sort(key=gif_tool.natural_sort_key)
            if not found:
                messagebox.showwarning("提示", f"该文件夹下未找到图片文件:\n{path}")
                return
            self.original_pil_image = None
            self.col_dividers = []
            self.row_dividers = []
            self.current_frames = found
            self.backup_original_frames = list(found)
            self.btn_restore_frames.configure(state=tk.DISABLED)
            self.info_status_label.configure(text=f"📁 载入帧目录: {os.path.basename(path)} (共 {len(found)} 帧)，已加载至时间轴与播放器")
            self._render_frame_to_canvas(self.current_frames[0])
            self._refresh_timeline()
            self.play()
        else:
            self.is_folder_source = False
            try:
                self.original_pil_image = Image.open(path)
                w, h = self.original_pil_image.size
                self.current_frames = []
                self.backup_original_frames = []
                self._clear_timeline()
                self.recompute_dividers()
                self._redraw_canvas()
                self.info_status_label.configure(text=f"🖼️ 原图尺寸: {w} × {h} 像素 | 💡 鼠标可直接拖动红色虚线微调分割位置，点击【一键拆解】即可原地播放")
            except Exception as e:
                messagebox.showerror("打开图片失败", f"无法加载图片:\n{e}")

    # ================= 视觉中心与播放引擎 =================

    def _redraw_canvas(self):
        if not self.original_pil_image or self.current_frames:
            return

        cw = max(200, self.canvas.winfo_width())
        ch = max(150, self.canvas.winfo_height())
        if cw <= 1 or ch <= 1:
            cw, ch = 480, 320

        orig_w, orig_h = self.original_pil_image.size
        scale = min(cw / float(orig_w), ch / float(orig_h))
        disp_w = max(1, int(orig_w * scale))
        disp_h = max(1, int(orig_h * scale))
        ox = (cw - disp_w) // 2
        oy = (ch - disp_h) // 2

        self.img_disp_info = {
            "ox": ox, "oy": oy,
            "disp_w": disp_w, "disp_h": disp_h,
            "scale": scale,
            "orig_w": orig_w, "orig_h": orig_h
        }

        # 底图缩略渲染（无破坏原图）
        img_copy = self.original_pil_image.copy().convert("RGB")
        img_copy.thumbnail((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.preview_image_ref = ImageTk.PhotoImage(img_copy)

        self.canvas.delete("all")
        self.canvas.create_image(ox, oy, anchor=tk.NW, image=self.preview_image_ref)
        self._render_interactive_guidelines()

    def _render_interactive_guidelines(self):
        """在画布上矢量绘制可交互分割虚线与手柄"""
        if not self.img_disp_info or self.current_frames or not self.original_pil_image:
            return
        self.canvas.delete("guideline")

        ox = self.img_disp_info["ox"]
        oy = self.img_disp_info["oy"]
        dw = self.img_disp_info["disp_w"]
        dh = self.img_disp_info["disp_h"]
        scale = self.img_disp_info["scale"]

        # 绘制垂直参考线
        for idx, vx in enumerate(self.col_dividers):
            cx = ox + int(vx * scale)
            is_active = (self.active_drag == ('v', idx)) or (self.hover_target == ('v', idx))
            color = "#f43f5e" if is_active else "#ef4444"
            w = 3 if is_active else 2
            self.canvas.create_line(cx, oy, cx, oy + dh, fill=color, width=w, dash=(6, 4), tags=("guideline", f"v_{idx}"))
            # 顶部和底部控制把手
            self.canvas.create_oval(cx - 4, oy - 4, cx + 4, oy + 4, fill=color, outline="white", width=1, tags=("guideline",))
            self.canvas.create_oval(cx - 4, oy + dh - 4, cx + 4, oy + dh + 4, fill=color, outline="white", width=1, tags=("guideline",))

        # 绘制水平参考线
        for idx, hy in enumerate(self.row_dividers):
            cy = oy + int(hy * scale)
            is_active = (self.active_drag == ('h', idx)) or (self.hover_target == ('h', idx))
            color = "#f43f5e" if is_active else "#ef4444"
            w = 3 if is_active else 2
            self.canvas.create_line(ox, cy, ox + dw, cy, fill=color, width=w, dash=(6, 4), tags=("guideline", f"h_{idx}"))
            # 左侧和右侧控制把手
            self.canvas.create_oval(ox - 4, cy - 4, ox + 4, cy + 4, fill=color, outline="white", width=1, tags=("guideline",))
            self.canvas.create_oval(ox + dw - 4, cy - 4, ox + dw + 4, cy + 4, fill=color, outline="white", width=1, tags=("guideline",))

        # 绘制半透明尺寸与比例悬浮徽章 (HUD Badge)
        cell_w, cell_h, ratio_str, desc = self.get_current_cell_dimensions()
        if cell_w > 0 and cell_h > 0:
            badge_text = f"📐 单格预估: {cell_w} × {cell_h} px  |  比例: {ratio_str} ({desc})"
            bx = ox + 10
            by = oy + 10
            tw = max(240, int(len(badge_text) * 7.4) + 20)
            th = 26
            self.canvas.create_rectangle(bx, by, bx + tw, by + th, fill="#0f172a", outline="#38bdf8", width=1, tags=("guideline",))
            self.canvas.create_text(bx + 10, by + 13, text=badge_text, anchor=tk.W, fill="#38bdf8", font=("Segoe UI", 9, "bold"), tags=("guideline",))

    def _find_nearest_divider(self, mx: int, my: int):
        """寻找鼠标附近的分割线"""
        if not self.img_disp_info or self.current_frames or not self.original_pil_image:
            return None
        ox = self.img_disp_info["ox"]
        oy = self.img_disp_info["oy"]
        dw = self.img_disp_info["disp_w"]
        dh = self.img_disp_info["disp_h"]
        scale = self.img_disp_info["scale"]
        tol = 8

        # 优先检查垂直线 (左右移动)
        if (oy - 8 <= my <= oy + dh + 8):
            for idx, vx in enumerate(self.col_dividers):
                cx = ox + int(vx * scale)
                if abs(mx - cx) <= tol:
                    return ('v', idx)

        # 检查水平线 (上下移动)
        if (ox - 8 <= mx <= ox + dw + 8):
            for idx, hy in enumerate(self.row_dividers):
                cy = oy + int(hy * scale)
                if abs(my - cy) <= tol:
                    return ('h', idx)

        return None

    def _on_canvas_motion(self, event):
        if not self.original_pil_image or self.current_frames:
            return
        if self.active_drag:
            return
        target = self._find_nearest_divider(event.x, event.y)
        if target != self.hover_target:
            self.hover_target = target
            if target:
                axis, idx = target
                cur = "sb_h_double_arrow" if axis == 'v' else "sb_v_double_arrow"
                try:
                    self.canvas.config(cursor=cur)
                except Exception:
                    self.canvas.config(cursor="hand2")
            else:
                self.canvas.config(cursor="")
            self._render_interactive_guidelines()

    def _on_canvas_press(self, event):
        if not self.original_pil_image or self.current_frames:
            return
        target = self._find_nearest_divider(event.x, event.y)
        if target:
            self.active_drag = target
            axis, idx = target
            axis_name = "垂直" if axis == 'v' else "水平"
            self.info_status_label.configure(text=f"↔ 正在按住拖拽第 {idx+1} 条{axis_name}分割线，微调裁切边界")
            self._render_interactive_guidelines()

    def _on_canvas_drag(self, event):
        if not self.active_drag or not self.img_disp_info:
            return

        axis, idx = self.active_drag
        ox = self.img_disp_info["ox"]
        oy = self.img_disp_info["oy"]
        scale = self.img_disp_info["scale"]
        orig_w = self.img_disp_info["orig_w"]
        orig_h = self.img_disp_info["orig_h"]

        if axis == 'v':
            px = int((event.x - ox) / scale)
            min_x = (self.col_dividers[idx - 1] + 8) if idx > 0 else 8
            max_x = (self.col_dividers[idx + 1] - 8) if idx < len(self.col_dividers) - 1 else (orig_w - 8)
            clamped_x = max(min_x, min(max_x, px))
            self.col_dividers[idx] = clamped_x
        else:
            py = int((event.y - oy) / scale)
            min_y = (self.row_dividers[idx - 1] + 8) if idx > 0 else 8
            max_y = (self.row_dividers[idx + 1] - 8) if idx < len(self.row_dividers) - 1 else (orig_h - 8)
            clamped_y = max(min_y, min(max_y, py))
            self.row_dividers[idx] = clamped_y

        self.update_cell_dimension_display()
        cell_w, cell_h, ratio_str, desc = self.get_current_cell_dimensions()
        if axis == 'v':
            self.info_status_label.configure(text=f"↔ 垂直线 #{idx+1}: x={self.col_dividers[idx]}px | 📐 单格: {cell_w}×{cell_h}px ({ratio_str} {desc})")
        else:
            self.info_status_label.configure(text=f"↕ 水平线 #{idx+1}: y={self.row_dividers[idx]}px | 📐 单格: {cell_w}×{cell_h}px ({ratio_str} {desc})")

        self._render_interactive_guidelines()

    def _on_canvas_release(self, event):
        if self.active_drag:
            axis, idx = self.active_drag
            axis_name = "垂直" if axis == 'v' else "水平"
            val = self.col_dividers[idx] if axis == 'v' else self.row_dividers[idx]
            self.active_drag = None
            cell_w, cell_h, ratio_str, desc = self.get_current_cell_dimensions()
            self.info_status_label.configure(text=f"✅ {axis_name}分割线 #{idx+1} 已微调至 {val}px (单格: {cell_w}×{cell_h}px · {ratio_str})！点击【一键拆解】按此线精确裁切")
            self._render_interactive_guidelines()

    def _on_canvas_leave(self, event):
        if not self.active_drag:
            self.canvas.config(cursor="")
            if self.hover_target:
                self.hover_target = None
                self._render_interactive_guidelines()

    def _render_frame_to_canvas(self, frame_path: str):
        if not os.path.exists(frame_path):
            return
        cw = max(200, self.canvas.winfo_width())
        ch = max(150, self.canvas.winfo_height())
        if cw <= 1 or ch <= 1:
            cw, ch = 480, 320

        try:
            im = Image.open(frame_path).convert("RGB")
            im.thumbnail((cw, ch), Image.Resampling.LANCZOS)
            self.preview_image_ref = ImageTk.PhotoImage(im)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=self.preview_image_ref)
        except Exception:
            pass

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.current_frames:
            messagebox.showinfo("提示", "当前未生成单帧序列，请先点击【一键拆解】或载入帧文件夹。")
            return
        self.is_playing = True
        self.btn_play.configure(text="⏸ 暂停")
        self._schedule_next_frame()

    def pause(self):
        self.is_playing = False
        self.btn_play.configure(text="▶ 播放动效")
        if self._play_timer_id:
            try:
                self.root.after_cancel(self._play_timer_id)
            except Exception:
                pass
            self._play_timer_id = None

    def _schedule_next_frame(self):
        if not self.is_playing or not self.current_frames:
            return

        total = len(self.current_frames)
        d = max(30, self.duration_var.get())

        # 尾帧停顿逻辑（非乒乓模式）
        if self.loop_mode_var.get() == "normal" and self.current_frame_idx == total - 1 and self.last_pause_var.get() > 0:
            d = self.last_pause_var.get()

        self._render_frame_to_canvas(self.current_frames[self.current_frame_idx])
        self.lbl_frame_counter.configure(text=f"帧 {self.current_frame_idx + 1:02d} / {total:02d}")

        # 计算下一帧索引
        if self.loop_mode_var.get() == "boomerang":
            if total <= 1:
                next_idx = 0
            else:
                next_idx = self.current_frame_idx + self.play_direction
                if next_idx >= total:
                    self.play_direction = -1
                    next_idx = max(0, total - 2)
                elif next_idx < 0:
                    self.play_direction = 1
                    next_idx = min(total - 1, 1)
        else:
            next_idx = (self.current_frame_idx + 1) % total

        self.current_frame_idx = next_idx
        self._play_timer_id = self.root.after(d, self._schedule_next_frame)

    def step_frame(self, delta: int):
        if not self.current_frames:
            return
        self.pause()
        total = len(self.current_frames)
        self.current_frame_idx = (self.current_frame_idx + delta) % total
        self._render_frame_to_canvas(self.current_frames[self.current_frame_idx])
        self.lbl_frame_counter.configure(text=f"帧 {self.current_frame_idx + 1:02d} / {total:02d}")

    def seek_frame(self, idx: int):
        if not self.current_frames:
            return
        self.pause()
        total = len(self.current_frames)
        self.current_frame_idx = (total - 1) if idx < 0 else (idx % total)
        self._render_frame_to_canvas(self.current_frames[self.current_frame_idx])
        self.lbl_frame_counter.configure(text=f"帧 {self.current_frame_idx + 1:02d} / {total:02d}")

    # ================= 时间轴胶卷与删帧交互 =================

    def _clear_timeline(self):
        for child in self.gallery_inner.winfo_children():
            child.destroy()
        self.frame_thumbnails.clear()
        self.lbl_film_summary.configure(text="当前未切分单帧")

    def _refresh_timeline(self):
        self._clear_timeline()
        total = len(self.current_frames)
        info_extra = ""
        if self.current_frames and os.path.exists(self.current_frames[0]):
            try:
                with Image.open(self.current_frames[0]) as im:
                    fw, fh = im.size
                    fratio, fdesc = gif_tool.get_aspect_ratio_info(fw, fh)
                    info_extra = f" · 单帧: {fw}×{fh} px ({fratio} {fdesc})"
            except Exception:
                pass
        self.lbl_film_summary.configure(text=f"序列帧胶卷 (共 {total} 帧{info_extra} | 点击 ❌ 移除废帧)")

        for idx, fp in enumerate(self.current_frames):
            try:
                frame_img = Image.open(fp)
                frame_img.thumbnail((68, 50), Image.Resampling.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(frame_img)
                self.frame_thumbnails.append(thumb_photo)

                item_card = ttk.Frame(self.gallery_inner, padding=2, relief=tk.SOLID, borderwidth=1)
                item_card.pack(side=tk.LEFT, padx=3, pady=2)

                # 顶部序号与删除按钮
                card_top = ttk.Frame(item_card)
                card_top.pack(fill=tk.X)
                ttk.Label(card_top, text=f"#{idx+1:02d}", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
                btn_del = tk.Label(card_top, text="❌", font=("Segoe UI", 7), fg="#ef4444", cursor="hand2")
                btn_del.pack(side=tk.RIGHT)
                btn_del.bind("<Button-1>", lambda e, target=fp: self.delete_frame(target))

                # 缩略图
                lbl_pic = ttk.Label(item_card, image=thumb_photo, cursor="hand2")
                lbl_pic.pack()
                lbl_pic.bind("<Button-1>", lambda e, pos=idx: self.seek_frame(pos))
                lbl_pic.bind("<Double-Button-1>", lambda e, path=fp: os.startfile(path))
            except Exception:
                pass

    def delete_frame(self, frame_path: str):
        if frame_path in self.current_frames:
            if len(self.current_frames) <= 2:
                messagebox.showwarning("提示", "至少需保留 2 帧图片以维持动画循环！")
                return
            self.pause()
            self.current_frames.remove(frame_path)
            self.btn_restore_frames.configure(state=tk.NORMAL)
            self.info_status_label.configure(text=f"已剔除 1 帧废帧，剩余 {len(self.current_frames)} 帧；动效与导出将自动同步生效")
            self.current_frame_idx = min(self.current_frame_idx, len(self.current_frames) - 1)
            self._render_frame_to_canvas(self.current_frames[self.current_frame_idx])
            self._refresh_timeline()
            self.play()

    def restore_frames(self):
        if self.backup_original_frames:
            self.pause()
            self.current_frames = list(self.backup_original_frames)
            self.btn_restore_frames.configure(state=tk.DISABLED)
            self.info_status_label.configure(text=f"已重置恢复全部 {len(self.current_frames)} 帧！")
            self._refresh_timeline()
            self.play()

    # ================= 执行功能与后台线程 =================

    def _get_scale_factor(self) -> float:
        val = self.scale_var.get()
        if "1.0x" in val:
            return 1.0
        elif "1.5x" in val:
            return 1.5
        elif "2.0x" in val:
            return 2.0
        elif "3.0x" in val:
            return 3.0
        return 1.0

    def action_split_only(self):
        src = self.source_path_var.get().strip()
        if not src or not os.path.exists(src) or os.path.isdir(src):
            messagebox.showwarning("提示", "请先选择一张有效的网格大图文件！")
            return

        c_divs = list(self.col_dividers) if (self.col_dividers and len(self.col_dividers) == self.cols_var.get() - 1) else None
        r_divs = list(self.row_dividers) if (self.row_dividers and len(self.row_dividers) == self.rows_var.get() - 1) else None

        def task():
            self._set_busy(True)
            try:
                self.progressbar["value"] = 20
                frames = gif_tool.split_grid_image(
                    image_path=src,
                    rows=self.rows_var.get(),
                    cols=self.cols_var.get(),
                    auto_trim_borders=self.trim_borders_var.get(),
                    custom_col_divs=c_divs,
                    custom_row_divs=r_divs,
                    scale_factor=self._get_scale_factor()
                )
                self.root.after(0, lambda: self._on_split_success(frames, auto_play=False))
            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("拆解失败", str(err)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=task, daemon=True).start()

    def _on_split_success(self, frames: list, auto_play: bool = True):
        self.progressbar["value"] = 100
        self.current_frames = frames
        self.backup_original_frames = list(frames)
        self.btn_restore_frames.configure(state=tk.DISABLED)
        self.info_status_label.configure(text=f"✅ 成功拆解为 {len(frames)} 帧，并自动归档进 output/frames/")
        self._refresh_timeline()
        if auto_play and self.current_frames:
            self.seek_frame(0)
            self.play()

    def action_merge_current_frames(self):
        if not self.current_frames:
            messagebox.showwarning("提示", "当前没有可合成的单帧图片，请先拆解大图或载入帧文件夹。")
            return

        preset = self.export_preset_var.get()
        boomerang = (self.loop_mode_var.get() == "boomerang")

        def task():
            self._set_busy(True)
            try:
                self.progressbar["value"] = 30
                base_name = "output_animation"
                if self.source_path_var.get():
                    base_name = os.path.splitext(os.path.basename(self.source_path_var.get()))[0]

                out_root = gif_tool.get_default_output_dir()
                ext = ".webp" if preset == "webp" else ".gif"
                suffix = "_wechat" if preset == "wechat" else ("_boomerang" if boomerang else "")
                target_gif = os.path.join(out_root, "gifs", f"{base_name}{suffix}{ext}")

                res = gif_tool.create_animation(
                    frame_paths_or_dir=self.current_frames,
                    output_path=target_gif,
                    duration=self.duration_var.get(),
                    last_frame_pause=self.last_pause_var.get(),
                    preset=preset,
                    boomerang=boomerang
                )
                self.root.after(0, lambda p=res: self._on_export_success(p))
            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("合成失败", str(err)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=task, daemon=True).start()

    def action_process_all(self):
        """一键拆解并合成流水线"""
        src = self.source_path_var.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showwarning("提示", "请先选择素材（大图或帧文件夹）！")
            return

        # 如果用户已经选了帧文件夹，直接执行合成
        if self.is_folder_source or os.path.isdir(src):
            self.action_merge_current_frames()
            return

        preset = self.export_preset_var.get()
        boomerang = (self.loop_mode_var.get() == "boomerang")
        c_divs = list(self.col_dividers) if (self.col_dividers and len(self.col_dividers) == self.cols_var.get() - 1) else None
        r_divs = list(self.row_dividers) if (self.row_dividers and len(self.row_dividers) == self.rows_var.get() - 1) else None

        def task():
            self._set_busy(True)
            try:
                self.progressbar["value"] = 25
                frames, result_gif = gif_tool.process_image_to_gif(
                    image_path=src,
                    rows=self.rows_var.get(),
                    cols=self.cols_var.get(),
                    duration=self.duration_var.get(),
                    last_frame_pause=self.last_pause_var.get(),
                    auto_trim_borders=self.trim_borders_var.get(),
                    custom_col_divs=c_divs,
                    custom_row_divs=r_divs,
                    scale_factor=self._get_scale_factor(),
                    preset=preset,
                    boomerang=boomerang
                )
                self.root.after(0, lambda f=frames, p=result_gif: self._on_process_all_success(f, p))
            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("处理失败", str(err)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=task, daemon=True).start()

    def _on_process_all_success(self, frames: list, result_path: str):
        self._on_split_success(frames, auto_play=True)
        self._on_export_success(result_path)

    def _on_export_success(self, result_path: str):
        self.progressbar["value"] = 100
        size_kb = os.path.getsize(result_path) / 1024.0
        fname = os.path.basename(result_path)
        self.lbl_task_status.configure(text=f"✅ 导出成功: {fname} ({size_kb:.1f} KB) 已归档至 output/gifs/")
        msg = f"🎉 导出完成！\n\n文件: {fname}\n大小: {size_kb:.1f} KB\n路径: {result_path}\n\n是否立即在资源管理器中打开成品目录？"
        if messagebox.askyesno("成功", msg):
            self.action_open_output()

    def action_open_output(self):
        out_root = gif_tool.get_default_output_dir()
        gifs_dir = os.path.join(out_root, "gifs")
        target = gifs_dir if os.path.exists(gifs_dir) else out_root
        os.startfile(target)

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_generate.configure(state=state)
        self.btn_split_only.configure(state=state)
        self.btn_merge_only.configure(state=state)


def launch_gui(initial_path: str = None):
    root = tk.Tk()
    app = GifCreaterStudio(root, initial_path=initial_path)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()