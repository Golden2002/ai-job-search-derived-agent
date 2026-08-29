# -*- coding: utf-8 -*-
"""改进建议测试：LLM 路径 / 规则兜底 / 防编造。"""
import pytest

from resume_product.improve import generate_improvements, IMPROVE_THRESHOLD


FACTS = [
    {"claim": "负责推荐算法优化", "evidence": "提升15%", "quote": "负责推荐算法优化"},
    {"claim": "主导用户画像模块开发", "evidence": "500万用户", "quote": "主导用户画像模块开发"},
]
EVAL = {
    "scores": {"technical": 40, "experience": 35, "behavioral": 70,
               "alignment": 50, "location": {"verdict": "FLAG"}},
    "total": 42.0, "verdict": "Weak Fit", "gaps": ["Spark", "Kubernetes"],
}
POSTING = {"title": "算法工程师", "description": "要求 Python、机器学习、推荐系统、Spark"}


def test_llm_rewrite_and_gap():
    def fake_chat(sys_p, usr_p):
        assert "硬性规则" in sys_p
        assert "[0] claim" in usr_p  # 事实卡带下标作锚
        return ('[{"type":"rewrite","dimension":"technical","priority":1,'
                '"reason":"technical 40分","target_index":0,'
                '"target_text":"负责推荐算法优化","action":"点明推荐系统",'
                '"rewritten":"负责推荐系统召回排序优化","needs_user_input":false},'
                '{"type":"gap","dimension":"technical","priority":2,'
                '"reason":"缺 Spark","target_index":null,'
                '"action":"需补充真实经历","rewritten":null,'
                '"needs_user_input":true}]')
    sug = generate_improvements(FACTS, EVAL, POSTING, chat_fn=fake_chat)
    assert sug[0]["type"] == "rewrite"
    assert sug[0]["target_index"] == 0
    assert "推荐系统" in sug[0]["rewritten"]
    assert sug[1]["type"] == "gap"
    assert sug[1]["rewritten"] is None  # gap 不编造


def test_rule_fallback_gaps():
    sug = generate_improvements(FACTS, EVAL, POSTING, chat_fn=None)
    assert any(s["type"] == "gap" and "Spark" in s["reason"] for s in sug)
    assert any(s["type"] == "rewrite" for s in sug)  # 低分维度 rewrite


def test_rule_fallback_no_fabrication():
    # gap 建议无 rewritten（不编造）
    sug = generate_improvements(FACTS, EVAL, POSTING, chat_fn=None)
    for s in sug:
        if s["type"] == "gap":
            assert s["rewritten"] is None


def test_llm_failure_falls_back():
    def bad_chat(sys_p, usr_p):
        return "这不是 JSON"
    sug = generate_improvements(FACTS, EVAL, POSTING, chat_fn=bad_chat)
    assert len(sug) > 0  # 兜底仍返回建议


def test_empty_facts():
    assert generate_improvements([], EVAL, POSTING) == []


def test_threshold_constant():
    assert IMPROVE_THRESHOLD == 55.0
