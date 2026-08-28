# -*- coding: utf-8 -*-
"""渲染固定资产测试：多模板加载 / 自定义 CSS / 模板元数据。"""
import os
import tempfile

import pytest

from resume_product.render.render_pdf import (
    TEMPLATE_IDS, TEMPLATE_META, load_template_css, build_html,
)


def test_template_meta_has_three_templates():
    assert len(TEMPLATE_IDS) >= 3
    for tid in TEMPLATE_IDS:
        assert tid in TEMPLATE_META
        assert TEMPLATE_META[tid]["name"]


def test_load_template_css_each_template():
    for tid in TEMPLATE_IDS:
        css = load_template_css(tid)
        assert "@page" in css or "size: A4" in css
        assert len(css) > 500


def test_load_template_css_custom_overrides():
    css = load_template_css("classic", custom_css=":root { --accent: #ff0000; }")
    assert "--accent: #ff0000" in css


def test_load_template_css_missing_template_falls_back():
    css = load_template_css("nonexistent")
    assert "A4" in css  # 兜底 resume.css 仍加载


def test_build_html_structure_contract():
    md = "# 我的简历\n\n**适配方向**：算法（technical）\n\n1. 优化推荐算法\n   - 证据：CTR 提升 15%"
    html = build_html(md, template="modern")
    assert 'class="r-title"' in html
    assert 'class="r-adapt"' in html
    assert 'class="r-claim"' in html
    assert 'class="r-evidence"' in html


def test_build_html_escapes_injection():
    md = "# <script>alert(1)</script>"
    html = build_html(md)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_build_html_custom_css_injected():
    html = build_html("", template="classic", custom_css=".x{color:red}")
    assert ".x{color:red" in html
