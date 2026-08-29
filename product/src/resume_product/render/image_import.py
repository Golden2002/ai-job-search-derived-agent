# -*- coding: utf-8 -*-
"""resume_product.render.image_import —— 简历截图 → OCR 排版识别 → CSS/HTML 还原。

用户诉求：上传简历截图（图片），识别其中的文字与排版（字号/对齐/分栏/间距），
生成还原用户自定义样式的 CSS 模板 + HTML，供后续流程（优化内容 + 输出新简历）使用。

设计（几何驱动，不依赖视觉 LLM）：
- OCR（rapidocr）提取文字 + 边界框坐标（box）
- 布局分析：center_x 分类（左栏/右栏/居中）→ 分栏检测 → 栏内按 top 分行
  → 字号（box 高度）→ 对齐（center_x）
- CSS/HTML 生成：居中标题跨栏，左/右栏用 CSS column 布局，字号/间距精确映射

依赖：rapidocr_onnxruntime + Pillow（可选依赖，无则优雅降级返回空）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _image_size(image_path: str) -> Tuple[int, int]:
    from PIL import Image
    with Image.open(image_path) as im:
        return im.size


def _ocr_items(image_path: str) -> List[Dict[str, Any]]:
    """OCR 提取文字 + 边界框（rapidocr）。失败返回空列表。"""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []
    try:
        engine = RapidOCR()
        result, _ = engine(image_path)
    except Exception:
        return []
    items: List[Dict[str, Any]] = []
    if not result:
        return items
    for box, text, score in result:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append({
            "text": text,
            "left": min(xs), "top": min(ys),
            "right": max(xs), "bottom": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),
            "center_x": (min(xs) + max(xs)) / 2,
        })
    return items


def _classify(item: Dict[str, Any], width: float) -> str:
    """center_x → 布局位置（left/right/center）。"""
    if width <= 0:
        return "left"
    r = item["center_x"] / width
    if r < 0.4:
        return "left"
    if r > 0.55:
        return "right"
    return "center"


def _group_by_top(items: List[Dict[str, Any]], y_threshold: float = 14) -> List[Dict[str, Any]]:
    """同栏 items 按 top 聚类为行。"""
    items = sorted(items, key=lambda x: x["top"])
    lines: List[Dict[str, Any]] = []
    for it in items:
        placed = False
        for line in lines:
            if abs(line["top"] - it["top"]) < y_threshold:
                line["items"].append(it)
                line["top"] = min(line["top"], it["top"])
                placed = True
                break
        if not placed:
            lines.append({"top": it["top"], "items": [it]})
    for line in lines:
        line["items"].sort(key=lambda x: x["left"])
        line["left"] = min(i["left"] for i in line["items"])
        line["right"] = max(i["right"] for i in line["items"])
        line["center_x"] = (line["left"] + line["right"]) / 2
        line["height"] = max(i["height"] for i in line["items"])
        line["text"] = "  ".join(i["text"] for i in line["items"])
    return lines


def _height_to_pt(height: float) -> float:
    return round(max(6.0, height / 1.25), 1)


def parse_image(image_path: str) -> Dict[str, Any]:
    """图片简历 → 布局（左栏行 / 右栏行 / 居中行 + 列数）。"""
    width, height = _image_size(image_path)
    items = _ocr_items(image_path)

    left_items = [i for i in items if _classify(i, width) == "left"]
    right_items = [i for i in items if _classify(i, width) == "right"]
    center_items = [i for i in items if _classify(i, width) == "center"]

    columns = 2 if (left_items and right_items) else 1
    return {
        "width": width,
        "height": height,
        "items": items,
        "left_lines": _group_by_top(left_items),
        "right_lines": _group_by_top(right_items),
        "center_lines": _group_by_top(center_items),
        "columns": columns,
    }


def import_resume_image(image_path: str) -> Dict[str, Any]:
    """图片简历 → {html, css, meta}（CSS/HTML 还原自定义样式）。"""
    parsed = parse_image(image_path)
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
        # 对齐：行内对齐取行的 center_x；栏内默认左对齐
        align = _classify(line, width)
        align_css = "center" if align == "center" else default_align
        style = f"font-size:{height_pt:.1f}pt;text-align:{align_css};"
        return f'<div style="{style}">{_esc(line["text"])}</div>'

    html_parts: List[str] = []
    # 居中行（标题，跨栏）
    for line in center_lines:
        html_parts.append(_line_div(line, "center"))
    # 双栏：左栏 + 右栏（CSS columns）
    if columns == 2:
        left_html = "".join(_line_div(l, "left") for l in left_lines)
        right_html = "".join(_line_div(l, "right") for l in right_lines)
        html_parts.append(
            f'<div style="column-count:2;column-gap:8mm;">'
            f'<div>{left_html}</div><div>{right_html}</div></div>')
    else:
        # 单栏：左栏行（含居中行）按 top 顺序合并
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
        css_parts.append(".img-columns { column-count:2; column-gap:8mm; }")

    meta = {
        "paragraphs": len(left_lines) + len(right_lines) + len(center_lines),
        "columns": columns,
        "css_length": len("\n".join(css_parts)),
        "ocr_engine": "rapidocr",
    }
    return {
        "html": html,
        "css": "\n".join(css_parts),
        "meta": meta,
        "parsed": parsed,
    }
