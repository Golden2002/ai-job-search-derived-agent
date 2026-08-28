# -*- coding: utf-8 -*-
"""resume_product.multi_version —— 多版本输出（稳妥/专业/高竞争力）。

基线对齐：medical-resume-agent 的多版本输出——按目标方向调整表达强度，三版横向对比。
规则模板兜底实现；chat_fn 可选注入以增强。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional


# §3.116 ⭐ R-R5 STAR 分段提示词（顶尖简历标准：S/T/A/R 显式分段 + 量化）
STAR_GUIDE = (
    "请将经历改写为 STAR 结构化表述（每条 bullet 按四要素显式展开）：\n"
    "S 情境（Situation）：在什么背景下（1 句）\n"
    "T 任务（Task）：承担什么任务/目标（1 句）\n"
    "A 行动（Action）：采取什么具体行动，用强动作动词开头（2-3 条）\n"
    "R 结果（Result）：量化成果（数字/百分比/规模），无法量化则用可验证的结果描述\n"
    "要求：R 段必须量化（补充数据缺口要标注「待补充」而非编造）；"
    "不得编造经历中不存在的数字。"
)


def star_compose(content: str, target: str = "",
                 chat_fn: Optional[Callable] = None) -> Dict[str, str]:
    """§3.116 ⭐ R-R5 经历 → STAR 四段结构化表达。

    Returns: {situation, task, action, result} 四段（LLM 优先，规则兜底）。
    """
    if chat_fn is not None:
        try:
            import json
            raw = chat_fn(
                f"{STAR_GUIDE}\n\n经历：{content}\n目标方向：{target or '通用'}\n"
                f'输出 JSON：{{"situation": "...", "task": "...", "action": "...", "result": "..."}}'
            )
            d = json.loads(raw)
            if all(k in d for k in ("situation", "task", "action", "result")):
                return {k: str(d[k]) for k in ("situation", "task", "action", "result")}
        except Exception:
            pass  # 回退规则兜底
    return _star_fallback(content)


def _star_fallback(content: str) -> Dict[str, str]:
    """STAR 规则兜底：无 LLM 时按四段模板占位（如实标注，不编造）。"""
    return {
        "situation": f"在 {content} 的工作背景下",
        "task": "承担相关任务并达成目标",
        "action": f"{content}（具体行动：待补充，基于真实经历）",
        "result": "（结果：待量化补充——请补充可衡量的成果数据）",
    }


def has_quantification(text: str) -> bool:
    """§3.116 ⭐ R-R5 量化检测：是否含数字/百分比/规模量词。"""
    if re.search(r'\d+', text):
        return True
    for kw in ("％", "%", "倍", "人", "万", "亿", "项", "个", "套", "篇"):
        if kw in text:
            return True
    return False


def quantify_suggest(text: str) -> str:
    """§3.116 ⭐ R-R5 量化建议：无量化时提示（不编造，标注待补充）。"""
    if has_quantification(text):
        return ""
    return "（建议补充量化数据：规模/数量/百分比/耗时——若原经历无确切数字，标注「待补充」勿编造）"


def generate_versions(content: str, target: str,
                      chat_fn: Optional[Callable] = None) -> Dict[str, str]:
    """生成三版表述：稳妥版 / 专业版 / 高竞争力版。

    content: 原始经历表述
    target: 目标方向（岗位/领域）
    chat_fn: 可选 LLM 注入（签名 chat_fn(prompt) -> str）；未提供时用规则模板兜底。
    """
    if chat_fn is not None:
        try:
            return _generate_via_llm(content, target, chat_fn)
        except Exception:
            pass  # 回退规则模板

    safe = _safe_version(content)
    professional = _professional_version(content, target)
    competitive = _competitive_version(content, target)
    return {"safe": safe, "professional": professional, "competitive": competitive}


def _generate_via_llm(content: str, target: str, chat_fn: Callable) -> Dict[str, str]:
    prompt = (
        f"请将以下经历表述改写为三个版本（针对目标：{target}）：\n"
        f"1) 稳妥版（保守、如实陈述）\n2) 专业版（行业术语、规范表达）\n"
        f"3) 高竞争力版（量化成果、冲击力表达）\n\n"
        f"原文：{content}\n\n"
        f"输出 JSON：{{\"safe\": \"...\", \"professional\": \"...\", \"competitive\": \"...\"}}"
    )
    import json
    raw = chat_fn(prompt)
    # 尝试解析 JSON；失败则提取三行
    try:
        d = json.loads(raw)
        return {"safe": d["safe"], "professional": d["professional"], "competitive": d["competitive"]}
    except Exception:
        return {"safe": content, "professional": content, "competitive": content}


def _safe_version(content: str) -> str:
    """稳妥版：如实、保守，弱化强度词。"""
    c = content
    for strong, weak in [("主导", "参与并承担主要工作于"), ("负责", "承担"),
                         ("独立完成", "完成"), ("首创", "提出")]:
        c = c.replace(strong, weak)
    return c


def _professional_version(content: str, target: str) -> str:
    """专业版：追加目标方向术语提示（规则层面）。"""
    if target:
        return f"{content}（面向 {target} 方向，突出相关专业能力与交付）"
    return content


def _competitive_version(content: str, target: str) -> str:
    """高竞争力版：鼓励量化与成果导向表述。"""
    return f"{content}——成果导向、可量化呈现，突出可衡量的影响与交付价值。"
