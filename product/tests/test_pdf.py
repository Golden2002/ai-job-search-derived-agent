# -*- coding: utf-8 -*-
"""PDF 交付能力测试（to_pdf——Playwright + Chrome 渲染 HTML→PDF）。"""
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.core import ResumeEngine, generate_resume


def test_to_pdf_creates_file():
    """to_pdf 生成 .pdf 文件（Playwright + Chrome）。"""
    engine = ResumeEngine()
    out = os.path.join(tempfile.gettempdir(), "test_resume.pdf")
    if os.path.exists(out):
        os.remove(out)
    path = engine.to_pdf(
        [{"claim": "负责推荐算法优化", "evidence": "提升点击率15%"}],
        target_role="算法工程师", out_path=out)
    assert os.path.exists(path), "应生成 pdf 文件"
    assert path.endswith(".pdf"), "应为 .pdf 扩展名"
    # PDF 文件头 %PDF
    with open(path, "rb") as f:
        assert f.read(4) == b"%PDF", "应为 PDF 格式"
    os.remove(path)


def test_generate_resume_pdf_format():
    """generate_resume(format='pdf') → 文件路径。"""
    path = generate_resume([{"claim": "测试经历"}], format="pdf")
    assert isinstance(path, str)
    assert os.path.exists(path)
    os.remove(path)
