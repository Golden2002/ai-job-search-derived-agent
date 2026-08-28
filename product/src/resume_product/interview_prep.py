# -*- coding: utf-8 -*-
"""resume_product.interview_prep —— 面试准备（STAR 框架 + 难题映射 + 反问）。

基线对齐：07-interview-prep.md。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def prepare(role: str, company: str, profile: Dict[str, Any],
            jd_text: str = "") -> Dict[str, Any]:
    """生成面试准备包：STAR 故事 + 高频难题 + 反问问题。"""
    star_stories = _build_star_stories(profile.get("experience", []))
    tough_questions = _map_tough_questions(jd_text, profile)
    questions_to_ask = _questions_to_ask(company, jd_text)
    return {
        "role": role,
        "company": company,
        "star_stories": star_stories,
        "tough_questions": tough_questions,
        "questions_to_ask": questions_to_ask,
    }


def _build_star_stories(experience: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    stories = []
    for exp in experience:
        story = {
            "project": exp.get("project", "") or exp.get("role", ""),
            "skill": ", ".join(exp.get("skills", []) or []),
            "S": exp.get("context", "") or "（需补充：当时的背景与问题）",
            "T": exp.get("task", "") or "（需补充：你的具体职责）",
            "A": exp.get("action", "") or exp.get("summary", "") or "（需补充：你采取的行动/工具/方法）",
            "R": exp.get("result", "") or "（需补充：可量化的成果）",
        }
        stories.append(story)
    return stories


def _map_tough_questions(jd_text: str, profile: Dict[str, Any]) -> List[Dict[str, str]]:
    jd = _norm(jd_text)
    questions = [
        {"q": "为什么离开上一家公司？", "hint": "诚实、向前看，不贬低前雇主"},
        {"q": "你缺少 X 技能/经验怎么办？", "hint": "承认差距→桥接到相邻经验→展示学习意愿"},
        {"q": "你 5 年后的职业规划？", "hint": "野心与岗位成长路径对齐"},
        {"q": "你最大的弱点是什么？", "hint": "真实弱点 + 具体缓解策略"},
    ]
    if jd:
        questions.append({"q": "为什么选择我们公司？",
                          "hint": "结合公司具体项目/价值观/市场地位，拒绝泛泛而谈"})
    return questions


def _questions_to_ask(company: str, jd_text: str) -> List[str]:
    qs = [
        "这个岗位未来 12 个月最重要的目标是什么？",
        "团队目前的规模与协作方式？",
        "晋升与绩效评估机制是怎样的？",
        "公司对技术/业务方向的中期规划？",
    ]
    return qs


def simulate_interview(role: str, profile: Dict[str, Any], rounds: int = 1) -> Dict[str, Any]:
    """STAR 框架模拟面试：生成一轮问答结构（供后续 LLM 对话流使用）。"""
    stories = _build_star_stories(profile.get("experience", []))
    questions = _map_tough_questions("", profile)
    return {
        "role": role,
        "rounds": rounds,
        "opening_questions": [q["q"] for q in questions],
        "star_pool": stories,
        "note": "模拟面试为问答结构，需注入 chat_fn 由 LLM 生成动态追问。",
    }
