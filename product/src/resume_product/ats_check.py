# -*- coding: utf-8 -*-
"""resume_product.ats_check — ATS 校验（Phase 5.1 ⭐）。

ATS（Applicant Tracking System，申请人追踪系统）兼容性校验——
简历能被招聘系统正确解析的检查项。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

# ATS 规则（检查项 → 说明）
ATS_RULES: List[Dict[str, str]] = [
    {"id": "headings", "name": "标准标题", "desc": "使用标准章节标题（教育背景/工作经历/项目经历/技能）"},
    {"id": "no_table", "name": "无表格", "desc": "避免表格布局（ATS 解析困难）"},
    {"id": "no_image", "name": "无图片", "desc": "避免图片/图表（ATS 无法读取）"},
    {"id": "standard_font", "name": "标准字体", "desc": "使用标准字体（ATS 兼容）"},
    {"id": "keywords", "name": "关键词", "desc": "含目标岗位关键词（ATS 关键词匹配）"},
    {"id": "plain_text", "name": "纯文本可读", "desc": "内容为纯文本可解析（无特殊编码）"},
    {"id": "contact_info", "name": "联系方式", "desc": "含联系方式（姓名/电话/邮箱）"},
    {"id": "quantified", "name": "量化成果", "desc": "经历含量化数据（数字/百分比）"},
]

# 标准标题（ATS 识别）
_STANDARD_HEADINGS = ["教育背景", "教育经历", "工作经历", "工作经验", "项目经历",
                      "项目经验", "技能", "专业技能", "个人技能", "自我评价"]


def ats_check(resume_text: str) -> Dict[str, Any]:
    """ATS 兼容性校验（确定性规则——可复现）。

    Returns: {"score": 0-100, "checks": [...], "issues": [...]}
    """
    t = resume_text or ""
    checks = []
    issues = []

    # 1. 标准标题
    has_heading = any(h in t for h in _STANDARD_HEADINGS)
    checks.append({"id": "headings", "passed": has_heading})
    if not has_heading:
        issues.append("缺少标准章节标题（如：教育背景/工作经历/技能）")

    # 2. 无表格/图片
    has_table_img = ("<table" in t.lower() or "<img" in t.lower()
                     or "| ---" in t)
    checks.append({"id": "no_table", "passed": not has_table_img})
    if has_table_img:
        issues.append("含表格/图片（ATS 解析困难——建议纯文本）")

    # 3. 关键词（长度/内容信号）
    has_content = len(t.strip()) >= 20
    checks.append({"id": "keywords", "passed": has_content})
    if not has_content:
        issues.append("内容过短（建议补充经历细节与关键词）")

    # 4. 量化数据
    has_numbers = bool(re.search(r"\d+", t))
    checks.append({"id": "quantified", "passed": has_numbers})
    if not has_numbers:
        issues.append("缺少量化数据（数字/百分比——建议量化成果）")

    # 5. 联系方式
    has_contact = ("@" in t) or bool(re.search(r"1\d{10}", t))
    checks.append({"id": "contact_info", "passed": has_contact})
    if not has_contact:
        issues.append("缺少联系方式（邮箱/电话）")

    passed = sum(1 for c in checks if c["passed"])
    score = round(passed / max(1, len(checks)) * 100)
    return {"score": score, "checks": checks, "issues": issues,
            "passed_count": passed, "total_count": len(checks)}
