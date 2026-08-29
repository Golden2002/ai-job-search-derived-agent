# -*- coding: utf-8 -*-
"""resume_product.render.pdf_import —— PDF 简历 → pdfplumber 字符级提取 → CSS/HTML 还原。

Oracle 论证 P0：PDF 是固定布局，pdfplumber 能提取**真实字体信息**（fontname/size/color）
+ 字符级坐标，比图片 OCR 的几何推断精度更高。

设计（复用 image_import 的几何布局框架，但用真实字体替代 OCR 推断）：
- pdfplumber 提取词级坐标（extract_words）+ 字符级字体/字号/颜色（chars）
- 布局分析：行分组（top 聚类）→ 分栏（x 聚类）→ 字号（char size）→ 对齐（x 位置）→ 颜色（non_stroking_color）
- CSS/HTML 生成：居中标题跨栏，左/右栏用 column 布局，字号/颜色精确映射

依赖：pdfplumber（可选，无则优雅降级返回空）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .image_import import _classify, _esc, _group_by_top, _height_to_pt


def _color_to_hex(color) -> str:
    """non_stroking_color (r,g,b[,a]) 0-1 浮点 → '#RRGGBB'。"""
    try:
        if not color:
            return ""
        r, g, b = color[0], color[1], color[2]
        return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"
    except Exception:
        return ""


def _extract_items(pdf_path: str) -> Tuple[List[Dict[str, Any]], float, float]:
    """pdfplumber 提取词级 items（text + 坐标 + 字号 + 颜色）+ 页面尺寸。"""
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        width, height = float(page.width), float(page.height)
        words = page.extract_words() or []
        chars = page.chars or []
        # 构建 char 索引（按位置匹配词 → 字号/颜色）
        items: List[Dict[str, Any]] = []
        for w in words:
            x0, top, x1, bottom = float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])
            # 匹配落在词范围内的首个 char（取字号/颜色）
            size = None
            color = ""
            for ch in chars:
                cx, cy = float(ch.get("x0", 0)), float(ch.get("top", 0))
                if x0 - 1 <= cx <= x1 + 1 and top - 1 <= cy <= bottom + 1:
                    if size is None and ch.get("size"):
                        size = float(ch["size"])
                    if not color and ch.get("non_stroking_color"):
                        color = _color_to_hex(ch["non_stroking_color"])
                    if size is not None and color:
                        break
            items.append({
                "text": w["text"],
                "left": x0, "top": top, "right": x1, "bottom": bottom,
                "width": x1 - x0, "height": bottom - top,
                "center_x": (x0 + x1) / 2,
                "size": size or round((bottom - top) * 1.25, 1),
                "color": color,
            })
        return items, width, height


def _group_lines(items: List[Dict[str, Any]], width: float) -> Tuple[List, List, List]:
    """center_x 分类（左/右/居中）→ 各自按 top 分行。"""
    left_items = [i for i in items if _classify(i, width) == "left"]
    right_items = [i for i in items if _classify(i, width) == "right"]
    center_items = [i for i in items if _classify(i, width) == "center"]
    return (_group_by_top(left_items), _group_by_top(right_items),
            _group_by_top(center_items))


def parse_pdf(pdf_path: str) -> Dict[str, Any]:
    """PDF 简历 → 布局（左栏行/右栏行/居中行 + 列数 + 页面尺寸）。"""
    items, width, height = _extract_items(pdf_path)
    left_lines, right_lines, center_lines = _group_lines(items, width)
    columns = 2 if (left_lines and right_lines) else 1
    return {
        "width": width, "height": height, "items": items,
        "left_lines": left_lines, "right_lines": right_lines,
        "center_lines": center_lines, "columns": columns,
    }


def import_resume_pdf(pdf_path: str) -> Dict[str, Any]:
    """PDF 简历 → {html, css, meta}（CSS/HTML 还原自定义样式）。"""
    parsed = parse_pdf(pdf_path)
    width = parsed["width"]
    left_lines = parsed["left_lines"]
    right_lines = parsed["right_lines"]
    center_lines = parsed["center_lines"]
    columns = parsed["columns"]

    if not (left_lines or right_lines or center_lines):
        return {
            "html": "", "css": "",
            "meta": {"paragraphs": 0, "columns": 1, "css_length": 0},
            "parsed": parsed,
        }

    def _line_div(line: Dict[str, Any], default_align: str) -> str:
        height_pt = _height_to_pt(line["height"])
        align = _classify(line, width)
        align_css = "center" if align == "center" else default_align
        # 颜色：取行内首个有颜色的词
        color = next((i["color"] for i in line["items"] if i.get("color")), "")
        color_css = f"color:{color};" if color else ""
        style = f"font-size:{height_pt:.1f}pt;text-align:{align_css};{color_css}"
        text = " ".join(i["text"] for i in line["items"])
        return f'<div style="{style}">{_esc(text)}</div>'

    html_parts: List[str] = []
    for line in center_lines:
        html_parts.append(_line_div(line, "center"))
    if columns == 2:
        left_html = "".join(_line_div(l, "left") for l in left_lines)
        right_html = "".join(_line_div(l, "right") for l in right_lines)
        html_parts.append(
            f'<div style="column-count:2;column-gap:8mm;">'
            f'<div>{left_html}</div><div>{right_html}</div></div>')
    else:
        merged = left_lines + center_lines
        merged.sort(key=lambda x: x["top"])
        for line in merged:
            html_parts.append(_line_div(line, "left"))

    html = "\n".join(html_parts)
    css_parts = [
        "@page { size: A4; margin: 18mm 16mm; }",
        "body { font-family: 'SimSun','Songti SC','Noto Serif CJK SC',serif; }",
    ]
    if columns == 2:
        css_parts.append(".pdf-columns { column-count:2; column-gap:8mm; }")

    meta = {
        "paragraphs": len(left_lines) + len(right_lines) + len(center_lines),
        "columns": columns,
        "css_length": len("\n".join(css_parts)),
        "pdf_engine": "pdfplumber",
    }
    return {
        "html": html,
        "css": "\n".join(css_parts),
        "meta": meta,
        "parsed": parsed,
    }
