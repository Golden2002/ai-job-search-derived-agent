# -*- coding: utf-8 -*-
"""resume_product.rank —— 多职位批量评分排序。

基线对齐：.claude/commands/rank.md（批量评分，/rank --all 重评语义）。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .job_evaluation import evaluate_fit


def rank_postings(postings: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """对多个职位逐一五维评分并按总分降序排序。

    返回排序后的 [{posting, total, verdict, scores, gaps, eligibility, language}, ...]
    """
    results = []
    for p in postings:
        r = evaluate_fit(p, profile)
        entry = {"posting": p, **r}
        results.append(entry)

    # 未评分（资格/语言硬门 FAIL）的排最后
    results.sort(key=lambda x: x.get("total", -1), reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results
