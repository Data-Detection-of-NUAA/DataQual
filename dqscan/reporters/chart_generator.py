# -*- coding: utf-8 -*-

"""
轻量图表生成器（Pillow 版本）。

参考工程的报告使用 matplotlib 生成图片并插入 DOCX；但在一些部署环境下
matplotlib 体积较大、依赖复杂。这里改用 Pillow 绘制基础柱状图，满足：
- 各数据类型评分（水平条形图）
- 问题率对比（分组柱状图）

输出文件会写到 `output_dir`，供 `docx_report_generator.py` 插入到 Word 报告中。
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# 保持与参考工程的变量名兼容（docx_report_generator 中会判断是否可用）
MATPLOTLIB_AVAILABLE = PIL_AVAILABLE


@dataclass(frozen=True)
class _Palette:
    excellent: tuple[int, int, int] = (0x28, 0xA7, 0x45)  # 绿色
    good: tuple[int, int, int] = (0x17, 0xA2, 0xB8)  # 蓝绿色
    warning: tuple[int, int, int] = (0xFF, 0xC1, 0x07)  # 黄色
    danger: tuple[int, int, int] = (0xDC, 0x35, 0x45)  # 红色
    neutral: tuple[int, int, int] = (0x6C, 0x75, 0x7D)  # 灰色
    primary: tuple[int, int, int] = (0x1F, 0x49, 0x7D)  # 深蓝
    grid: tuple[int, int, int] = (0xDE, 0xE2, 0xE6)  # 浅灰


LABELS: dict[str, str] = {
    "tabular": "表格数据",
    "timeseries": "时序数据",
    "image": "图像数据",
    "text": "文本数据",
}


def _find_font_path() -> str | None:
    """
    优先选择支持中文的字体。

    说明：
    - macOS 常见：PingFang/Heiti/Arial Unicode
    - Linux 常见：Noto/DejaVu
    """
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _load_font(size: int) -> Any:
    if not PIL_AVAILABLE:
        raise ImportError("pillow 未安装")
    path = _find_font_path()
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return int(right - left), int(bottom - top)
    except Exception:
        return (len(text) * 10, 14)


def _draw_text_center(draw: Any, box: tuple[int, int, int, int], text: str, font: Any, fill: tuple[int, int, int]):
    x0, y0, x1, y1 = box
    w, h = _text_size(draw, text, font)
    x = x0 + (x1 - x0 - w) / 2
    y = y0 + (y1 - y0 - h) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _draw_dashed_line(draw: Any, x0: int, y0: int, x1: int, y1: int, fill: tuple[int, int, int], dash: int = 6, gap: int = 6):
    if x0 == x1:
        # vertical
        y = y0
        while y < y1:
            y2 = min(y + dash, y1)
            draw.line((x0, y, x1, y2), fill=fill, width=1)
            y = y2 + gap
        return
    if y0 == y1:
        # horizontal
        x = x0
        while x < x1:
            x2 = min(x + dash, x1)
            draw.line((x, y0, x2, y1), fill=fill, width=1)
            x = x2 + gap
        return
    draw.line((x0, y0, x1, y1), fill=fill, width=1)


class ChartGenerator:
    """为 DOCX 报告生成 PNG 图表（Pillow 实现）。"""

    def __init__(self, output_dir: str = "output/charts"):
        if not PIL_AVAILABLE:
            raise ImportError("pillow 未安装。请运行: pip install pillow")
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.palette = _Palette()
        self.font_title = _load_font(28)
        self.font_axis = _load_font(14)
        self.font_label = _load_font(18)
        self.font_value = _load_font(18)

    def generate_data_type_bars(self, scores: dict[str, float], title: str = "各数据类型评分") -> str | None:
        if not scores:
            return None

        order = ["text", "image", "timeseries", "tabular"]
        keys = [k for k in order if k in scores] + [k for k in scores.keys() if k not in order]
        max_x = 110.0

        width = 900
        top = 60
        bottom = 70
        left = 140
        right = 60
        bar_h = 52
        gap = 18
        height = top + bottom + len(keys) * bar_h + max(len(keys) - 1, 0) * gap

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # title
        _draw_text_center(draw, (0, 10, width, 10 + 40), title, self.font_title, (0, 0, 0))

        axis_y = height - bottom
        axis_x0 = left
        axis_x1 = width - right
        draw.line((axis_x0, axis_y, axis_x1, axis_y), fill=(0, 0, 0), width=2)

        # vertical grid lines
        for v in [60, 70, 80, 90]:
            x = int(axis_x0 + (v / max_x) * (axis_x1 - axis_x0))
            _draw_dashed_line(draw, x, top - 10, x, axis_y, fill=self.palette.grid, dash=6, gap=6)

        # x ticks
        for v in range(0, 101, 20):
            x = int(axis_x0 + (v / max_x) * (axis_x1 - axis_x0))
            draw.line((x, axis_y, x, axis_y + 6), fill=(0, 0, 0), width=1)
            t = str(v)
            tw, th = _text_size(draw, t, self.font_axis)
            draw.text((x - tw / 2, axis_y + 10), t, font=self.font_axis, fill=(0, 0, 0))

        # x-axis label
        _draw_text_center(draw, (axis_x0, axis_y + 35, axis_x1, axis_y + 60), "分数", self.font_axis, (0, 0, 0))

        for idx, key in enumerate(keys):
            score = float(scores.get(key, 0) or 0)
            label = LABELS.get(key, key)

            y0 = top + idx * (bar_h + gap)
            y1 = y0 + bar_h

            # left label (right-aligned)
            tw, th = _text_size(draw, label, self.font_label)
            draw.text((left - 10 - tw, y0 + (bar_h - th) / 2), label, font=self.font_label, fill=(0, 0, 0))

            bar_len = int((min(max(score, 0.0), max_x) / max_x) * (axis_x1 - axis_x0))
            bar_x1 = axis_x0 + bar_len

            color = self._score_color(score)
            draw.rectangle((axis_x0, y0 + 8, bar_x1, y1 - 8), fill=color)

            # value label
            value_text = f"{score:.0f}"
            draw.text((bar_x1 + 10, y0 + (bar_h - th) / 2), value_text, font=self.font_value, fill=(0, 0, 0))

        path = os.path.join(self.output_dir, "data_type_bars.png")
        img.save(path, "PNG")
        return path

    def generate_rate_comparison(self, data_type_rates: dict[str, dict[str, float]], title: str = "问题率对比") -> str | None:
        if not data_type_rates:
            return None

        order = ["tabular", "timeseries", "image", "text"]
        keys = [k for k in order if k in data_type_rates] + [k for k in data_type_rates.keys() if k not in order]

        width = 1050
        height = 760
        left = 90
        right = 60
        top = 70
        bottom = 90
        y_max = 100.0

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        _draw_text_center(draw, (0, 10, width, 10 + 40), title, self.font_title, (0, 0, 0))

        axis_x0 = left
        axis_x1 = width - right
        axis_y0 = height - bottom
        axis_y1 = top

        # axes
        draw.line((axis_x0, axis_y1, axis_x0, axis_y0), fill=(0, 0, 0), width=2)
        draw.line((axis_x0, axis_y0, axis_x1, axis_y0), fill=(0, 0, 0), width=2)

        # y ticks
        for v in range(0, 101, 20):
            y = int(axis_y0 - (v / y_max) * (axis_y0 - axis_y1))
            draw.line((axis_x0 - 6, y, axis_x0, y), fill=(0, 0, 0), width=1)
            t = str(v)
            tw, th = _text_size(draw, t, self.font_axis)
            draw.text((axis_x0 - 12 - tw, y - th / 2), t, font=self.font_axis, fill=(0, 0, 0))

        # dashed thresholds (5% and 10%)
        for v, color in [(5, self.palette.excellent), (10, self.palette.warning)]:
            y = int(axis_y0 - (v / y_max) * (axis_y0 - axis_y1))
            _draw_dashed_line(draw, axis_x0, y, axis_x1, y, fill=color, dash=8, gap=6)

        # y label
        draw.text((20, (axis_y1 + axis_y0) / 2 - 20), "百分比 (%)", font=self.font_axis, fill=(0, 0, 0))

        series = [
            ("异常率", self.palette.danger, "anomaly_rate"),
            ("缺失率", self.palette.warning, "missing_rate"),
            ("重复率", self.palette.good, "duplicate_rate"),
        ]

        group_count = len(keys)
        slot_w = (axis_x1 - axis_x0) / max(group_count, 1)
        bar_w = min(34, int(slot_w * 0.22))
        inner_gap = int(bar_w * 0.25)

        for idx, key in enumerate(keys):
            group_center = axis_x0 + slot_w * (idx + 0.5)
            label = LABELS.get(key, key).replace("数据", "")  # 与参考图一致：表格/时序/图像/文本

            group_total_w = bar_w * len(series) + inner_gap * (len(series) - 1)
            start_x = int(group_center - group_total_w / 2)

            for si, (_, color, field) in enumerate(series):
                rate = float((data_type_rates.get(key) or {}).get(field, 0) or 0) * 100.0
                rate = max(0.0, min(rate, y_max))
                bar_h = int((rate / y_max) * (axis_y0 - axis_y1))
                x0 = start_x + si * (bar_w + inner_gap)
                x1 = x0 + bar_w
                y0 = axis_y0 - bar_h
                draw.rectangle((x0, y0, x1, axis_y0), fill=color)

            # x label
            tw, th = _text_size(draw, label, self.font_label)
            draw.text((group_center - tw / 2, axis_y0 + 12), label, font=self.font_label, fill=(0, 0, 0))

        # legend
        legend_x = width - right - 220
        legend_y = top + 10
        box = 18
        for i, (name, color, _) in enumerate(series):
            y = legend_y + i * 28
            draw.rectangle((legend_x, y, legend_x + box, y + box), fill=color)
            draw.text((legend_x + box + 10, y - 2), name, font=self.font_label, fill=(0, 0, 0))

        path = os.path.join(self.output_dir, "rate_comparison.png")
        img.save(path, "PNG")
        return path

    def _score_color(self, score: float) -> tuple[int, int, int]:
        if score >= 90:
            return self.palette.excellent
        if score >= 80:
            return self.palette.good
        if score >= 70:
            return self.palette.warning
        return self.palette.danger

    def cleanup(self) -> None:
        try:
            shutil.rmtree(self.output_dir)
        except Exception:
            pass
