# -*- coding: utf-8 -*-
"""简历截图 → OCR 排版识别 → CSS/HTML 还原 测试。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

pytest.importorskip("rapidocr_onnxruntime")
pytest.importorskip("PIL")

from PIL import Image, ImageDraw, ImageFont

from resume_product.render.image_import import import_resume_image, parse_image


def _make_screenshot(path):
    """生成测试简历截图：标题居中 + 左栏正文 + 右栏技能。"""
    W, H = 800, 1000
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
    # 标题居中
    d.text((W // 2 - 60, 30), "Resume", fill="black", font=font_title)
    # 左栏正文
    d.text((40, 120), "Work Experience", fill="black", font=font_body)
    d.text((40, 160), "Engineer at Google", fill="black", font=font_body)
    d.text((40, 200), "Engineer at Apple", fill="black", font=font_body)
    # 右栏技能
    d.text((450, 120), "Skills", fill="black", font=font_body)
    d.text((450, 160), "Python, SQL", fill="black", font=font_body)
    img.save(path)


@pytest.fixture(scope="module")
def screenshot(tmp_path_factory):
    p = str(tmp_path_factory.mktemp("img") / "resume.png")
    _make_screenshot(p)
    return p


def test_parse_image_ocr_text(screenshot):
    r = parse_image(screenshot)
    items = r["items"]
    assert len(items) >= 4, "OCR 应识别出多个文字块"
    texts = " ".join(i["text"] for i in items)
    # 英文测试图（默认字体），断言关键文字（宽松）
    assert "Work" in texts or "Engineer" in texts or "Skills" in texts or "Resume" in texts


def test_import_resume_image_returns_html_css(screenshot):
    r = import_resume_image(screenshot)
    assert r["meta"]["paragraphs"] >= 3
    assert "column-count:2" in r["css"] or r["meta"]["columns"] >= 1
    assert r["html"], "应返回 HTML"
    # 标题居中（若 OCR 识别出 Resume）
    if "Resume" in r["html"]:
        assert "text-align:center" in r["html"], "标题应居中"


def test_image_import_no_ocr_graceful(tmp_path):
    """无 OCR 依赖时优雅降级（monkeypatch 掉 rapidocr 返回空）。"""
    from PIL import Image as _IMG
    p = str(tmp_path / "empty.png")
    _IMG.new("RGB", (100, 100), "white").save(p)
    from resume_product.render import image_import as m
    orig = m._ocr_items
    m._ocr_items = lambda path: []  # 模拟 OCR 失败
    try:
        r = import_resume_image(p)
        assert r["meta"]["paragraphs"] == 0
        assert r["html"] == ""
    finally:
        m._ocr_items = orig
