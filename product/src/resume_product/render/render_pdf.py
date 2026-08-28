# -*- coding: utf-8 -*-
"""resume_product.render.render_pdf — PDF 渲染固定资产（多模板 ⭐）。

固定资产（render/）：
- templates/classic.css —— 经典素雅（宋体黑白公文档）
- templates/modern.css —— 现代风格（无衬线、教育蓝、左色带、卡片感）
- templates/minimal.css —— 极简单栏（大留白、细字重）
- resume.css —— 兜底样式（classic 同源）
- 本渲染脚本（Playwright + Chrome，HTML → A4 PDF）

模板加载顺序：custom_css（用户自定义，最高优先）→ templates/{template}.css → resume.css
结构类名契约：build_html 输出 .r-title/.r-adapt/.r-exp/.r-claim/.r-evidence/.r-subtitle
（模板只写样式，结构由本脚本统一输出。）
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_RENDER_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _RENDER_DIR / "templates"

# Chrome 路径（优先环境变量，回退默认安装路径）
_CHROME_CANDIDATES = [
    os.environ.get("RESUME_CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"/usr/bin/google-chrome",
    r"/usr/bin/chromium",
]

TEMPLATE_IDS = ["classic", "modern", "minimal"]

TEMPLATE_META = {
    "classic": {"name": "经典素雅", "description": "宋体黑白公文档，庄重稳妥",
                "accent": "#1a1a1a", "layout": "single"},
    "modern": {"name": "现代风格", "description": "无衬线教育蓝，左色带卡片感",
               "accent": "#3D55E8", "layout": "single-accent"},
    "minimal": {"name": "极简单栏", "description": "大留白细字重，克制简约",
                "accent": "#3a3a3a", "layout": "single-minimal"},
}


def _find_chrome() -> str:
    for p in _CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return ""


def load_template_css(template: str, custom_css: Optional[str] = None) -> str:
    """按优先级加载 CSS：custom_css → templates/{template}.css → resume.css 兜底。"""
    css_parts = []
    # 1. 兜底基础（resume.css 提供 A4 @page 基础）
    base = _RENDER_DIR / "resume.css"
    if base.exists():
        css_parts.append(base.read_text(encoding="utf-8"))
    # 2. 指定模板
    tpl = _TEMPLATES_DIR / f"{template}.css"
    if tpl.exists():
        css_parts.append(tpl.read_text(encoding="utf-8"))
    # 3. 用户自定义（最高优先——覆盖变量换肤/追加样式）
    if custom_css:
        css_parts.append(custom_css)
    return "\n".join(css_parts)


def build_html(resume_md: str, template: str = "classic",
               custom_css: Optional[str] = None) -> str:
    """Markdown 简历 → HTML（结构类名契约 + 多模板 CSS）。"""
    css = load_template_css(template, custom_css)
    title = "个人简历"
    adapt = ""
    body_parts = []
    for line in resume_md.split("\n"):
        line = line.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("**适配方向**"):
            adapt = f'<div class="r-adapt">{_esc(line.strip("*").strip())}</div>'
        elif line.strip().startswith("- "):
            body_parts.append(
                f'<div class="r-exp"><div class="r-evidence">{_esc(line.strip()[2:])}</div></div>')
        elif line.strip() and line.strip()[0].isdigit() and "." in line[:4]:
            body_parts.append(
                f'<div class="r-exp"><div class="r-claim">{_esc(line)}</div></div>')
        elif line.strip().startswith("**"):
            body_parts.append(
                f'<div class="r-subtitle">{_esc(line.strip("*").strip())}</div>')
        else:
            body_parts.append(f'<p>{_esc(line)}</p>')
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>{css}</style>
</head><body>
<h1 class="r-title">{_esc(title)}</h1>
{adapt}
{''.join(body_parts)}
</body></html>"""


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_to_pdf(html: str, out_path: str) -> str:
    """HTML → PDF（Playwright + Chrome）。"""
    import asyncio
    from playwright.async_api import async_playwright

    chrome = _find_chrome()

    async def _render():
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                executable_path=chrome if chrome else None)
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(
                path=out_path, format="A4", print_background=True,
                display_header_footer=True,
                header_template="<div></div>",
                footer_template=(
                    '<div style="font-size:8pt;color:#888;width:100%;'
                    'padding:0 20mm;text-align:center;'
                    'font-family:sans-serif;">'
                    '<span class="pageNumber"></span> / '
                    '<span class="totalPages"></span></div>'))
            await browser.close()

    asyncio.run(_render())
    return out_path


def render_markdown_to_pdf(resume_md: str, out_path: str,
                           template: str = "classic",
                           custom_css: Optional[str] = None) -> str:
    """Markdown 简历 → PDF（一站式：build_html + html_to_pdf）。"""
    html = build_html(resume_md, template=template, custom_css=custom_css)
    return html_to_pdf(html, out_path)
