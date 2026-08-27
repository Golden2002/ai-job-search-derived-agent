# -*- coding: utf-8 -*-
"""resume_product.render.render_pdf — PDF 渲染固定资产（P ⭐）。

固定资产：
- resume.css（官方正式样式）
- 本渲染脚本（Playwright + Chrome，HTML → A4 PDF）

复用词汇表插件 render_html_to_pdf.py 的成熟模式（独立脚本 + Chrome 渲染）。
"""

from __future__ import annotations

import os
from pathlib import Path

_RENDER_DIR = Path(__file__).resolve().parent

# Chrome 路径（优先环境变量，回退默认安装路径）
_CHROME_CANDIDATES = [
    os.environ.get("RESUME_CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"/usr/bin/google-chrome",
    r"/usr/bin/chromium",
]


def _find_chrome() -> str:
    for p in _CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return ""


def build_html(resume_md: str) -> str:
    """Markdown 简历 → HTML（嵌入 resume.css 固定资产）。"""
    css = (_RENDER_DIR / "resume.css").read_text(encoding="utf-8")
    title = "个人简历"
    subtitle = ""
    adapt = ""
    body_parts = []
    for line in resume_md.split("\n"):
        line = line.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("**适配方向**"):
            adapt = f'<div class="adapt">{_esc(line.strip("*").strip())}</div>'
        elif line.strip().startswith("- "):
            body_parts.append(f'<div class="experience"><div class="evidence">{_esc(line.strip()[2:])}</div></div>')
        elif line.strip() and line.strip()[0].isdigit() and "." in line[:4]:
            body_parts.append(f'<div class="experience"><div class="claim">{_esc(line)}</div></div>')
        elif line.strip().startswith("**"):
            body_parts.append(f'<div class="subtitle">{_esc(line.strip("*").strip())}</div>')
        else:
            body_parts.append(f'<p>{_esc(line)}</p>')
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>{css}</style>
</head><body>
<h1>{_esc(title)}</h1>
{subtitle}{adapt}
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


def render_markdown_to_pdf(resume_md: str, out_path: str) -> str:
    """Markdown 简历 → PDF（一站式：build_html + html_to_pdf）。"""
    html = build_html(resume_md)
    return html_to_pdf(html, out_path)
