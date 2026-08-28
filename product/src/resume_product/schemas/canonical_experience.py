# -*- coding: utf-8 -*-
"""resume_product.schemas.canonical_experience —— 经历拆解六要素。

基线对齐：medical-resume-agent canonical-experience-v2.schema.json。
六要素：research_subject / method / tools / role / deliverable / transferable_skill。
拆解路径：原始经历 → 六要素 → 可迁移能力 → 目标方向表达重点。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

# 六要素 schema（JSON Schema 风格）
CANONICAL_EXPERIENCE_SCHEMA = {
    "type": "object",
    "required": ["research_subject", "method", "tools", "role", "deliverable",
                 "transferable_skill"],
    "properties": {
        "research_subject": {"type": "string", "description": "研究对象/主题"},
        "method": {"type": "string", "description": "研究方法/流程"},
        "tools": {"type": "array", "items": {"type": "string"}, "description": "工具/技术栈"},
        "role": {"type": "string", "description": "承担角色"},
        "deliverable": {"type": "string", "description": "交付物/成果"},
        "transferable_skill": {"type": "string", "description": "可迁移能力"},
        "target_direction": {"type": "string", "description": "目标方向表达重点（可选）"},
    },
}


def validate_canonical(data: Dict[str, Any]) -> List[str]:
    """校验六要素完整性，返回错误列表（空 = 合法）。"""
    errors = []
    for field in ["research_subject", "method", "tools", "role", "deliverable",
                  "transferable_skill"]:
        if field not in data or not data[field]:
            errors.append(f"缺失字段：{field}")
    if "tools" in data and not isinstance(data["tools"], list):
        errors.append("tools 必须为列表")
    return errors


def decompose(raw_experience: str, target_direction: str = "",
              chat_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """原始经历 → 六要素拆解 → 可迁移能力 → 目标方向表达。

    chat_fn: 可选 LLM 注入（chat_fn(prompt) -> str）；未提供时用规则模板兜底。
    """
    if chat_fn is not None:
        try:
            return _decompose_via_llm(raw_experience, target_direction, chat_fn)
        except Exception:
            pass

    # 规则模板兜底：把原始经历作为 research_subject，其余字段待补充标记
    return {
        "research_subject": raw_experience[:80],
        "method": "（待补充：研究方法/流程）",
        "tools": [],
        "role": "（待补充：承担角色）",
        "deliverable": "（待补充：交付物/成果）",
        "transferable_skill": "（待补充：可迁移能力）",
        "target_direction": target_direction or "（待补充：目标方向表达重点）",
    }


def _decompose_via_llm(raw: str, target: str, chat_fn: Callable) -> Dict[str, Any]:
    import json
    prompt = (
        f"将以下原始经历拆解为六要素 JSON（research_subject/method/tools/role/"
        f"deliverable/transferable_skill），并给出面向「{target}」的表达重点 "
        f"target_direction。\n\n原文：{raw}\n\n只输出 JSON。"
    )
    raw_out = chat_fn(prompt)
    try:
        d = json.loads(raw_out)
    except Exception:
        return decompose(raw, target)  # 回退
    return d
