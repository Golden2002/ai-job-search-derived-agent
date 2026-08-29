# -*- coding: utf-8 -*-
"""resume_product.improve —— 低分简历改进建议（LLM + 规则兜底）⭐。

Oracle 方案（2026-08-28）：评分低（total < 55）→ LLM 生成针对性修改建议。
建议分两类（防编造）：
- rewrite：改写真实经历（target_index 指向事实卡，可一键应用）
- gap：缺失技能/经历（仅提示，不编造，无 rewritten）

复用：evaluate_fit 返回结构 + multi_version 的 chat_fn-or-兜底 + llm_client。
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

IMPROVE_THRESHOLD = 55.0  # 与 _verdict_from_total 的 Weak 边界一致

_SYS_PROMPT = (
    "你是资深简历顾问。基于「用户真实经历事实卡 + JD + 五维评分与缺口」产出针对性修改建议。\n"
    "硬性规则（违反即视为失败）：\n"
    "1. 只改写/重排/突出用户已写出的真实经历，绝不新增用户未提及的事实、项目、技能、公司、数字。\n"
    "2. 需要量化但原文无数字时，在文本中写「待补充」占位，禁止编造数字。\n"
    "3. 每条 rewrite 建议：target_index 必须指向一张真实事实卡；target_text 为该卡的 claim 或 quote 原文；rewritten 必须能被该原文完整支撑。\n"
    "4. 缺失技能/经历（用户确实没有）→ 输出 type=\"gap\"，action 写「需补充真实经历或待学习」，rewritten 置 null。\n"
    "5. 每条 reason 必须绑定到具体维度分数或 gaps 项。\n"
    "6. 只输出 JSON 数组，无任何解释文字。"
)


def generate_improvements(
    facts: List[Dict[str, str]],
    evaluation: Dict[str, Any],
    posting: Dict[str, Any],
    chat_fn: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """生成简历改进建议（LLM 优先，规则兜底）。

    facts: 事实卡 [{claim, evidence, quote}]
    evaluation: evaluate_fit 返回（scores/total/verdict/gaps）
    posting: {title, description}
    """
    if not facts:
        return []

    if chat_fn is not None:
        try:
            sug = _via_llm(facts, evaluation, posting, chat_fn)
            if sug:
                return sug
        except Exception:
            pass

    return _rule_fallback(facts, evaluation, posting)


def _via_llm(facts, evaluation, posting, chat_fn) -> List[Dict[str, Any]]:
    scores = evaluation.get("scores", {})
    # 只取数值维度（location 是 dict，排除）
    num_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
    gaps = evaluation.get("gaps", []) or []
    usr_p = (
        f"目标岗位：{posting.get('title', '')}\n"
        f"JD 描述：{posting.get('description', '')[:800]}\n"
        f"五维评分：{json.dumps(num_scores, ensure_ascii=False)}\n"
        f"总分：{evaluation.get('total', 0)}（{evaluation.get('verdict', '')}）\n"
        f"缺失技能 gaps：{gaps}\n\n"
        "用户真实经历事实卡（下标不可改动）：\n"
    )
    for i, f in enumerate(facts):
        usr_p += f"[{i}] claim=\"{f.get('claim', '')}\" quote=\"{f.get('quote', '')}\"\n"
    usr_p += "\n输出 JSON 数组，每项字段：id,type,dimension,priority,reason,target_index,target_text,action,rewritten,needs_user_input"

    raw = chat_fn(_SYS_PROMPT, usr_p)
    if not raw:
        return []
    m = re.search(r"\[.*\]", raw or "", re.S)
    if not m:
        return []
    data = json.loads(m.group(0))
    out = []
    for i, d in enumerate(data, 1):
        if not isinstance(d, dict):
            continue
        typ = d.get("type", "rewrite")
        out.append({
            "id": d.get("id", f"sug_{i}"),
            "type": "rewrite" if typ == "rewrite" else "gap",
            "dimension": d.get("dimension", ""),
            "priority": int(d.get("priority", i)),
            "reason": d.get("reason", ""),
            "target_index": d.get("target_index"),
            "target_text": d.get("target_text", ""),
            "action": d.get("action", ""),
            "rewritten": d.get("rewritten"),
            "needs_user_input": bool(d.get("needs_user_input", typ != "rewrite")),
        })
    # 按优先级排序
    out.sort(key=lambda x: x.get("priority", 99))
    return out


def _rule_fallback(facts, evaluation, posting) -> List[Dict[str, Any]]:
    """规则兜底：对 gaps 生成 gap 建议，对低分维度生成 rewrite 建议。"""
    gaps = evaluation.get("gaps", []) or []
    scores = evaluation.get("scores", {})
    out = []
    i = 0
    # gap 建议（缺失技能——不编造）
    for g in gaps:
        i += 1
        out.append({
            "id": f"sug_{i}", "type": "gap",
            "dimension": "technical", "priority": i,
            "reason": f"JD 要求「{g}」，但技能表与经历均未出现",
            "target_index": None, "target_text": "",
            "action": f"若有 {g} 的真实经历请补充到经历描述；否则作为待学习项，勿在简历中声称",
            "rewritten": None, "needs_user_input": True,
        })
    # rewrite 建议（低分维度 → 在经历中点明 JD 用词）
    weak = [k for k, v in scores.items()
            if isinstance(v, (int, float)) and v < 55]
    for dim in weak:
        if not facts:
            break
        i += 1
        target = 0  # 指向第一张事实卡（最相关）
        out.append({
            "id": f"sug_{i}", "type": "rewrite",
            "dimension": dim, "priority": i,
            "reason": f"{dim} 维度 {scores[dim]} 分偏低",
            "target_index": target,
            "target_text": facts[target].get("claim", ""),
            "action": "在该经历中显式点出与 JD 匹配的关键词与量化成果（缺失数字标「待补充」）",
            "rewritten": facts[target].get("claim", "") + "（待补充：量化成果与 JD 关键词）",
            "needs_user_input": False,
        })
    return out
