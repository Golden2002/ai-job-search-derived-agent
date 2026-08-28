# -*- coding: utf-8 -*-
"""resume_product.multi_version —— 多版本输出（稳妥/专业/高竞争力）。

基线对齐：medical-resume-agent 的多版本输出——按目标方向调整表达强度，三版横向对比。
规则模板兜底实现；chat_fn 可选注入以增强。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


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
