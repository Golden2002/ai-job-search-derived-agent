# -*- coding: utf-8 -*-
"""resume_product.drafter_reviewer — drafter-reviewer 双 Agent 流程（Phase 5.3 ⭐）。

复用 ai-job-search 的 drafter-reviewer 双 Agent 申请流程：
- drafter：生成简历初稿（定向表达）
- reviewer：审核初稿（问题清单 + 评分）
- 迭代：根据审核意见改进（最多 N 轮）
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .core import ResumeEngine
from .ats_check import ats_check


def draft_resume(facts: List[Dict[str, str]], target_role: str,
                 role_pack: str = "tech_v1",
                 chat_fn: Optional[Callable] = None) -> str:
    """drafter：经历 → 简历初稿（定向表达）。"""
    engine = ResumeEngine(chat_fn=chat_fn, role_pack=role_pack)
    return engine.compose(facts, target_role)


def review_resume(resume_md: str, target_role: str) -> Dict[str, Any]:
    """reviewer：审核简历（问题清单 + 评分）。

    确定性审核（可复现）：ATS 校验 + 内容完整性 + 关键词检查。
    """
    issues = []

    # 1. ATS 校验
    ats = ats_check(resume_md)
    issues.extend(ats["issues"])

    # 2. 内容完整性
    if target_role and target_role not in resume_md and "个人简历" not in resume_md:
        issues.append(f"标题未体现目标岗位（{target_role}）")

    # 3. 长度
    if len(resume_md.strip()) < 50:
        issues.append("内容过短——建议补充更多经历细节")

    # 4. 量化
    import re
    if not re.search(r"\d", resume_md):
        issues.append("缺少量化数据——建议补充数字/百分比")

    score = max(0, 100 - len(issues) * 10)
    return {"issues": issues, "score": score,
            "passed": not issues, "ats": ats}


def drafter_reviewer(facts: List[Dict[str, str]], target_role: str,
                     role_pack: str = "tech_v1",
                     max_rounds: int = 2,
                     chat_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """drafter-reviewer 双 Agent 完整流程。

    1. drafter 生成初稿
    2. reviewer 审核（问题清单）
    3. 按问题迭代（确定性补强：加量化/加标题——LLM 可用时润色）
    4. 返回最终简历 + 审核结果 + 轮数
    """
    resume = draft_resume(facts, target_role, role_pack, chat_fn)
    for round_no in range(1, max_rounds + 1):
        review = review_resume(resume, target_role)
        if review["passed"]:
            break
        # 迭代：确定性补强
        fixed_lines = []
        if "标题未体现" in "".join(review["issues"]) and target_role:
            fixed_lines.append(f"# {target_role}（定向简历）")
        # 保留原内容（去旧标题）
        for line in resume.split("\n"):
            if line.startswith("# "):
                continue
            fixed_lines.append(line)
        # 量化缺失补强提示
        if "量化" in "".join(review["issues"]) and facts:
            fixed_lines.append("")
            fixed_lines.append("**补充说明**：建议在经历中补充量化成果（如提升 X%、覆盖 N 用户）。")
        resume = "\n".join(fixed_lines)
        review = review_resume(resume, target_role)

    final_review = review_resume(resume, target_role)
    return {"resume": resume, "review": final_review, "rounds": round_no,
            "target_role": target_role, "role_pack": role_pack}
