# -*- coding: utf-8 -*-
"""resume_product.skill_gap —— 技能缺口分析 + 学习路径建议。

基线对齐：upskill/SKILL.md（技能频率热图 + 权重 + 学习计划）。
权重：(100 - fit) / 100；记录缺口优先于推断；空白 fit 不当 0（跳过并计数）。
"""

from __future__ import annotations

from typing import Any, Dict, List


def analyze_gaps(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """分析多职位技能缺口，输出热图 + 学习计划。

    jobs: [{title, skills: [...], fit_rating: 0-100, gaps: [...]}]
    profile: {skills: [...]}
    """
    current = set(s.strip().lower() for s in profile.get("skills", []))

    freq: Dict[str, Dict[str, Any]] = {}
    skipped_blank_fit = 0
    skipped_no_gaps = 0

    for job in jobs:
        fit = job.get("fit_rating")
        # 空白/非数值 fit 跳过（不当 0）
        if fit is None or not isinstance(fit, (int, float)):
            skipped_blank_fit += 1
            weight = None
        else:
            weight = (100 - fit) / 100.0

        # 记录缺口优先于推断
        recorded = job.get("gaps")
        if recorded:
            skills = [s.strip().lower() for s in recorded]
            provenance = "recorded"
        else:
            skills = [s.strip().lower() for s in job.get("skills", [])]
            provenance = "inferred"

        for s in skills:
            if s in current:
                continue  # 已具备，不算缺口
            if s not in freq:
                freq[s] = {"count": 0, "weight": 0.0, "provenance": set()}
            freq[s]["count"] += 1
            if weight is not None:
                freq[s]["weight"] += weight
            freq[s]["provenance"].add(provenance)

    heatmap = {
        s: {"count": v["count"], "weight": round(v["weight"], 3),
            "provenance": sorted(v["provenance"])}
        for s, v in freq.items()
    }

    # 学习计划：按权重降序
    plan = sorted(heatmap.items(), key=lambda kv: kv[1]["weight"], reverse=True)
    learning_plan = [
        {"skill": s, "priority": i + 1, "weight": v["weight"],
         "note": "建议补充学习资源（可注入 chat_fn 联网检索）"}
        for i, (s, v) in enumerate(plan)
    ]

    return {
        "heatmap": heatmap,
        "learning_plan": learning_plan,
        "skipped_blank_fit": skipped_blank_fit,
        "skipped_no_gaps": skipped_no_gaps,
    }
