# -*- coding: utf-8 -*-
"""resume_product.salary_benchmark —— 薪资基准对比。

基线对齐：rank/评估相关能力。输入职位/地区/年限，输出市场分位区间与对比结论。
sources 保留可扩展接口（用户可注入外部薪资数据源）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def benchmark(
    role: str,
    region: str,
    years: float,
    sources: Optional[List[Dict[str, Any]]] = None,
    expected: Optional[float] = None,
) -> Dict[str, Any]:
    """返回薪资基准区间与对比结论。

    sources: 可选外部数据源，形如 [{role, region, years, p25, p50, p75, source}]
    expected: 候选人期望/当前薪资（用于生成对比结论）
    """
    matched = _match_sources(role, region, years, sources or [])

    if matched:
        p25 = matched.get("p25")
        p50 = matched.get("p50")
        p75 = matched.get("p75")
        source_note = matched.get("source", "外部数据源")
        data_sufficient = True
    else:
        # 无外部数据时给出占位区间并明确标注数据不足
        p25, p50, p75 = None, None, None
        source_note = "无匹配数据源，需用户提供薪资数据"
        data_sufficient = False

    verdict = None
    if expected is not None and p50 is not None:
        if expected < p50 * 0.85:
            verdict = "低于市场"
        elif expected > p50 * 1.15:
            verdict = "高于市场"
        else:
            verdict = "符合市场"

    return {
        "role": role,
        "region": region,
        "years": years,
        "percentile25": p25,
        "percentile50": p50,
        "percentile75": p75,
        "source_note": source_note,
        "data_sufficient": data_sufficient,
        "expected": expected,
        "verdict": verdict,
    }


def _match_sources(role: str, region: str, years: float,
                   sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for s in sources:
        if (s.get("role", "").lower() in role.lower() or not s.get("role")) and \
           (s.get("region", "").lower() in region.lower() or not s.get("region")):
            return s
    return None
