# -*- coding: utf-8 -*-
"""W4-W5 ⭐ 通用简历引擎测试（经历采集→事实校验→定向表达→简历生成）。

复用 medical-resume-agent 引擎，验证通用化改造（去医学化 + 全行业 Role Pack）。
"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.core import (
    enrich_experience, generate_resume, list_role_packs,
    ResumeEngine,
)


# ── R1: 经历采集 → 结构化事实卡（主张校验）──
def test_enrich_experience_quote_gate():
    """经历文本 → 事实卡，主张必须引用原文（复用 claim_gate）。"""
    text = "我在字节跳动实习，负责抖音推荐算法优化，通过 A/B 测试提升点击率 15%。"
    facts = enrich_experience(text)
    assert facts, "应产出事实卡"
    assert facts[0].get("quote") or facts[0].get("claim"), "主张需可追溯"
    assert "15%" in str(facts), "量化数据应保留"


def test_enrich_experience_empty():
    """空文本 → 空事实卡（不抛异常）。"""
    assert enrich_experience("") == []


# ── R2: Role Pack 定向表达 ──
def test_list_role_packs():
    """通用 Role Pack 清单（tech 等）。"""
    packs = list_role_packs()
    assert "tech_v1" in packs, "应有 tech 通用角色包"


def test_generate_resume_targeted():
    """按目标岗位生成定向简历（Role Pack 适配）。"""
    experiences = [
        {"claim": "负责推荐系统算法优化", "evidence": "A/B 测试提升点击率 15%"},
    ]
    resume = generate_resume(experiences, target_role="算法工程师", format="markdown")
    assert resume, "应生成简历内容"
    assert "推荐" in resume or "算法" in resume, "内容应包含经历"


# ── R3: 多格式 ──
def test_generate_resume_html():
    """HTML 格式导出。"""
    resume = generate_resume([{"claim": "数据分析"}], format="html")
    assert "<html" in resume.lower() or "<div" in resume or "<h1" in resume


def test_generate_resume_unknown_format():
    """未知格式 → 默认 markdown（不抛异常）。"""
    resume = generate_resume([{"claim": "测试"}], format="unknown")
    assert isinstance(resume, str)


# ── R4: ResumeEngine 类（可注入 LLM——插件化）──
def test_engine_llm_injection():
    """引擎支持注入 chat_fn（外部智能体接入——PAEG 生态）。"""
    engine = ResumeEngine(chat_fn=lambda s, u: "mock response")
    assert engine.chat_fn is not None
    # 无 LLM 时确定性模式可用（默认函数兜底）
    engine2 = ResumeEngine(chat_fn=None)
    assert engine2.chat_fn is not None
    # 确定性提取应产出事实卡
    facts = engine2.enrich("我在公司负责数据分析，通过优化提升效率20%。")
    assert facts, "确定性提取应产出事实卡"
    assert "20%" in str(facts), "量化数据应保留"

