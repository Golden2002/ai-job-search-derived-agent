# -*- coding: utf-8 -*-
"""Word 交付能力测试（to_docx——python-docx 生成 .docx）。"""
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.core import ResumeEngine, generate_resume


def test_to_docx_creates_file():
    """to_docx 生成 .docx 文件。"""
    engine = ResumeEngine()
    out = os.path.join(tempfile.gettempdir(), "test_resume.docx")
    if os.path.exists(out):
        os.remove(out)
    path = engine.to_docx(
        [{"claim": "负责推荐算法优化", "evidence": "提升点击率15%"}],
        target_role="算法工程师", out_path=out)
    assert os.path.exists(path), "应生成 docx 文件"
    assert path.endswith(".docx"), "应为 .docx 扩展名"
    # 验证是有效 docx（zip 容器）
    with open(path, "rb") as f:
        assert f.read(2) == b"PK", "docx 应为 zip 容器"
    os.remove(path)


def test_to_docx_default_path():
    """无 out_path → 返回默认路径（tempfile）。"""
    engine = ResumeEngine()
    path = engine.to_docx([{"claim": "数据分析"}], target_role="分析师")
    assert os.path.exists(path)
    os.remove(path)


def test_generate_resume_docx_format():
    """generate_resume(format='docx') → 文件路径。"""
    path = generate_resume([{"claim": "测试经历"}], format="docx")
    assert isinstance(path, str)
    assert os.path.exists(path)
    os.remove(path)
