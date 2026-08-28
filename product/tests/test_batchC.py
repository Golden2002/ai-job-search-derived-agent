# -*- coding: utf-8 -*-
"""批次 C 测试：latex_compile / template_registry。"""
import os
import shutil
import tempfile

import pytest

from resume_product.render.latex_compile import compile_tex, visual_check
from resume_product.template_registry import TemplateRegistry

HAS_LUALATEX = shutil.which("lualatex") is not None


# ---------- compile_tex ----------

def test_compile_missing_file():
    r = compile_tex(os.path.join(tempfile.gettempdir(), "nope.tex"))
    assert r["ok"] is False
    assert "不存在" in r["error"]


@pytest.mark.skipif(HAS_LUALATEX, reason="lualatex 存在，跳过缺失环境测试")
def test_compile_no_lualatex_clear_error():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.tex")
        open(p, "w").write("\\documentclass{article}\\begin{document}x\\end{document}")
        r = compile_tex(p)
        assert r["ok"] is False
        assert "lualatex" in r["error"]


# ---------- visual_check ----------

def test_visual_check_two_pages_pass():
    text = "Page one content\fPage two content"
    r = visual_check(text, expected_pages=2)
    assert r["page_count_ok"] is True
    assert r["verdict"] == "PASS"


def test_visual_check_wrong_pages_fail():
    text = "one\f\ftwo"  # 2 个换页符 → 3 页
    r = visual_check(text, expected_pages=2)
    assert r["page_count_ok"] is False
    assert r["verdict"] == "FAIL"


def test_visual_check_orphan_heading():
    text = "EXPERIENCE\n\n\nJohn Smith"
    r = visual_check(text, expected_pages=2)
    assert r["orphan_heading_detected"] is True


def test_visual_check_font_consistency():
    r = visual_check("has replacement \ufffd char", expected_pages=2)
    assert r["font_consistent"] is False


# ---------- template_registry ----------

def test_registry_builtins():
    r = TemplateRegistry()
    ids = [t["id"] for t in r.list()]
    assert "moderncv_banking" in ids
    assert "resume_html" in ids


def test_registry_switch_and_get():
    r = TemplateRegistry()
    t = r.switch("generic_md")
    assert t["format"] == "md"
    assert r.current == "generic_md"


def test_registry_duplicate_id_rejected():
    r = TemplateRegistry()
    with pytest.raises(ValueError):
        r.register("generic_md", "dup", "md")


def test_registry_invalid_format_rejected():
    r = TemplateRegistry()
    with pytest.raises(ValueError):
        r.register("new", "x", "docx")


def test_registry_import_missing_file_rejected():
    r = TemplateRegistry()
    with pytest.raises(ValueError):
        r.import_template("new", "x", "tex", os.path.join(tempfile.gettempdir(), "none.tex"))


def test_registry_import_valid():
    r = TemplateRegistry()
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.tex")
        open(p, "w").write("% empty")
        t = r.import_template("custom", "自定义", "tex", p)
        assert t["id"] == "custom"
