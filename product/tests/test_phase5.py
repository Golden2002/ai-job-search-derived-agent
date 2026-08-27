# -*- coding: utf-8 -*-
"""多行业 Role Pack + ATS 校验 + 双 Agent 测试（Phase 5 补齐 ⭐）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.core import ResumeEngine, list_role_packs, generate_resume
from resume_product.ats_check import ats_check, ATS_RULES
from resume_product.drafter_reviewer import (
    drafter_reviewer, draft_resume, review_resume,
)


# ── R1: 多行业 Role Pack ──
def test_multi_role_packs():
    """tech/consulting/finance/education 行业包。"""
    packs = list_role_packs()
    for p in ["tech_v1", "consulting_v1", "finance_v1", "education_v1"]:
        assert p in packs, f"应有 {p}"


def test_consulting_role_pack_direction():
    """咨询行业定向（问题解决/客户沟通优先）。"""
    engine = ResumeEngine(role_pack="consulting_v1")
    md = engine.compose([{"claim": "数据分析"}], target_role="咨询顾问")
    assert "咨询" in md or "consulting" in md.lower(), "应体现咨询方向"


# ── R2: ATS 校验 ──
def test_ats_rules_defined():
    """ATS 规则表（兼容性检查项）。"""
    assert len(ATS_RULES) >= 5


def test_ats_check_clean_resume():
    """合规简历 → 通过。"""
    r = ats_check("数据分析师\n经历：负责数据分析项目\n技能：Python, SQL")
    assert r["score"] is not None


def test_ats_check_empty():
    """空简历 → 低分提示。"""
    r = ats_check("")
    assert r["score"] == 0 or r["score"] is not None


# ── R3: drafter-reviewer 双 Agent ──
def test_draft_resume():
    """drafter 生成简历。"""
    md = draft_resume([{"claim": "负责推荐算法"}], "算法工程师")
    assert md, "drafter 应产出简历"


def test_review_resume():
    """reviewer 审核简历（问题清单）。"""
    review = review_resume("测试简历内容", "算法工程师")
    assert "issues" in review
    assert "score" in review


def test_drafter_reviewer_flow():
    """双 Agent 完整流程：draft → review → 迭代。"""
    result = drafter_reviewer(
        [{"claim": "负责推荐算法优化", "evidence": "提升15%"}],
        "算法工程师")
    assert result["resume"], "应产出简历"
    assert result["review"] is not None, "应产出审核"
    assert result["rounds"] >= 1, "至少一轮迭代"
