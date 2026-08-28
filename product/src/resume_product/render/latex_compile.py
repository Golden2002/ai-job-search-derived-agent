# -*- coding: utf-8 -*-
"""resume_product.render.latex_compile —— LaTeX 编译链 + 视觉校验。

基线对齐：05-cv-templates.md（moderncv banking/blue、lualatex、2 页硬要求）。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List


def _which_lualatex() -> bool:
    return shutil.which("lualatex") is not None


def compile_tex(tex_path: str, workdir: str = None) -> Dict[str, Any]:
    """调用 lualatex 编译，返回 PDF 路径 + 页数 + 警告。环境缺失报清晰错误。"""
    tex_path = os.path.abspath(tex_path)
    if not os.path.exists(tex_path):
        return {"ok": False, "error": f"tex 文件不存在：{tex_path}"}
    if not _which_lualatex():
        return {"ok": False,
                "error": "未检测到 lualatex（需安装 TeX Live 或 MiKTeX）。"
                         "请在环境变量 PATH 中配置后重试。"}

    workdir = workdir or os.path.dirname(tex_path)
    cmd = ["lualatex", "-interaction=nonstopmode",
           "-output-directory=" + workdir, tex_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=120, cwd=workdir)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "lualatex 编译超时（120s）。"}

    log = proc.stdout + proc.stderr
    pdf_path = os.path.splitext(tex_path)[0] + ".pdf"
    pages = _extract_page_count(log)
    return {
        "ok": proc.returncode == 0 and os.path.exists(pdf_path),
        "pdf_path": pdf_path if os.path.exists(pdf_path) else None,
        "pages": pages,
        "log_tail": log[-2000:],
        "returncode": proc.returncode,
    }


def _extract_page_count(log: str) -> int:
    import re
    m = re.search(r"Output written on .*?\((\d+) pages?", log)
    if m:
        return int(m.group(1))
    return 0


def visual_check(pdf_text: str, expected_pages: int = 2) -> Dict[str, Any]:
    """对 PDF 文本层做视觉校验：页数 / 孤儿标题 / 字体一致性线索。"""
    issues: List[str] = []

    # 页数校验（文本层无法直接得页数时，调用方传入或这里按换页符估算）
    page_count_ok = True
    if pdf_text.count("\f") > 0:
        pages = pdf_text.count("\f") + 1
        page_count_ok = (pages == expected_pages)
        if not page_count_ok:
            issues.append(f"页数 {pages} != 预期 {expected_pages}（2 页硬要求）")

    # 孤儿标题检测：章节标题后紧跟空白或另一标题
    import re
    lines = pdf_text.splitlines()
    orphan_detected = False
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r"^[A-Z][A-Z\s]{2,}$", s) and s.isupper() and len(s) < 50:
            # 大写标题行；检查下一行是否为空或也是标题
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt == "" or (nxt.isupper() and len(nxt) < 50):
                orphan_detected = True
                issues.append(f"疑似孤儿标题：{s}")
                break

    # 字体一致性线索（文本层混入乱码/替换字符）
    font_consistent = True
    if "\ufffd" in pdf_text:
        font_consistent = False
        issues.append("文本层存在替换字符（字体不一致线索）")

    return {
        "page_count_ok": page_count_ok,
        "orphan_heading_detected": orphan_detected,
        "font_consistent": font_consistent,
        "issues": issues,
        "verdict": "PASS" if not issues else "FAIL",
    }
