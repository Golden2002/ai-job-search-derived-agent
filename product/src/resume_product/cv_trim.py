# -*- coding: utf-8 -*-
"""resume_product.cv_trim —— 相关性加权裁剪。

基线对齐：05-cv-templates.md 裁剪规则——简历溢出篇幅时按「职位相关性 + 独特性 +
依赖度」加权裁剪，而非机械删除旧经历。

权重公式：score = 0.5*relevance + 0.3*uniqueness + 0.2*dependency
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def _relevance(entry: Dict[str, Any], target_role: str, target_desc: str = "") -> float:
    """职位相关性：经历技能/职责与目标岗位的重叠度。"""
    target = _norm(target_role + " " + target_desc)
    if not target.strip():
        return 0.5
    entry_text = _norm(" ".join([
        str(entry.get("role", "")),
        str(entry.get("summary", "") or entry.get("description", "")),
        " ".join(entry.get("skills", []) or []),
    ]))
    t_tokens = set(target.split())
    e_tokens = set(entry_text.split())
    if not t_tokens or not e_tokens:
        return 0.3
    overlap = len(t_tokens & e_tokens) / len(t_tokens)
    return min(1.0, overlap * 2.0)  # 放大到 0-1


def _uniqueness(entry: Dict[str, Any], all_entries: List[Dict[str, Any]]) -> float:
    """独特性：经历技能在其他条目中少见程度（越独特分越高）。"""
    skills = set(_norm(s) for s in (entry.get("skills", []) or []))
    if not skills:
        return 0.3
    n = len(all_entries) or 1
    others = [e for e in all_entries if e is not entry]
    seen = 0
    for s in skills:
        for o in others:
            o_skills = set(_norm(x) for x in (o.get("skills", []) or []))
            if s in o_skills:
                seen += 1
                break
    # 未在他处出现的技能比例
    return 1.0 - (seen / len(skills))


def _dependency(entry: Dict[str, Any], all_entries: List[Dict[str, Any]]) -> float:
    """依赖度：该经历被其他条目引用/依赖的程度（高依赖应保留）。"""
    # 简化：检查是否有其他条目 summary 提到本条目的 role 或项目名
    key_terms = [_norm(str(entry.get("role", ""))), _norm(str(entry.get("project", "") or ""))]
    key_terms = [t for t in key_terms if t]
    if not key_terms:
        return 0.3
    deps = 0
    for o in all_entries:
        if o is entry:
            continue
        o_text = _norm(str(o.get("summary", "") or o.get("description", "")))
        if any(t in o_text for t in key_terms):
            deps += 1
    return min(1.0, deps / max(1, len(all_entries) - 1))


def trim_experience(
    entries: List[Dict[str, Any]],
    target_role: str,
    max_items: int,
    target_desc: str = "",
) -> Dict[str, Any]:
    """按加权分数裁剪经历，返回保留/移除与理由。

    返回：{kept: [...], removed: [{entry, score, reason}], scores: [...]}
    """
    if len(entries) <= max_items:
        return {"kept": list(entries), "removed": [], "scores": [
            _entry_score(e, entries, target_role, target_desc) for e in entries]}

    scored = []
    for e in entries:
        s = _entry_score(e, entries, target_role, target_desc)
        scored.append((s, e))

    scored.sort(key=lambda x: x[0], reverse=True)  # 降序，高分保留

    kept = [e for _, e in scored[:max_items]]
    removed = [{"entry": e, "score": round(s, 3),
                "reason": "加权分数低于保留阈值（相关性/独特性/依赖度综合）"}
               for s, e in scored[max_items:]]
    return {
        "kept": kept,
        "removed": removed,
        "scores": [{"entry_id": id(e), "score": round(s, 3), "role": e.get("role", "")}
                   for s, e in scored],
    }


def _entry_score(entry: Dict[str, Any], all_entries: List[Dict[str, Any]],
                 target_role: str, target_desc: str) -> float:
    rel = _relevance(entry, target_role, target_desc)
    uniq = _uniqueness(entry, all_entries)
    dep = _dependency(entry, all_entries)
    return 0.5 * rel + 0.3 * uniq + 0.2 * dep
