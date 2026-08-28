# -*- coding: utf-8 -*-
"""resume_product.claim_gate —— 事实校验（移植 medical-resume-agent 方法论）。

基线对齐：medical-resume-agent 的 claim_gate/confirmation_gate/claim_ledger。
核心原则：未确认信息不静默升级，绝不编造经历。

claim 三档：
- verified：有证据支持
- unverified：缺证据，不得写入正式简历（需向用户确认）
- exaggerated：表述超出证据范围（如"主导"但证据仅"参与"）
"""

from __future__ import annotations

from typing import Any, Dict, List


class ClaimGate:
    """主张校验门——未确认信息不静默升级。"""

    # 需要警惕的强度词（出现时若证据不足即 exaggerated）
    _STRONG_TERMS = ["主导", "负责", "独立完成", "第一作者", "核心", "首创",
                     "leading", "led", "owned", "sole", "first author", "pioneered"]

    @classmethod
    def review(cls, claims: List[Dict[str, Any]], evidence: Dict[str, Any]) -> Dict[str, Any]:
        """审查主张列表。

        claims: [{text, evidence_key}]——evidence_key 指向 evidence 中的证据条目
        evidence: {key: {text, strength}}——strength 为 "strong"/"weak"/"absent"
        """
        passed: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = []
        needs_confirmation: List[Dict[str, Any]] = []

        for claim in claims:
            text = claim.get("text", "")
            key = claim.get("evidence_key", "")
            ev = evidence.get(key) if key else None

            # 无证据主张 → unverified（不静默升级）
            if not ev or ev.get("strength") == "absent":
                needs_confirmation.append({
                    "text": text, "verdict": "unverified",
                    "reason": "缺少证据支持，需用户确认后方可写入正式简历。"})
                continue

            # 证据弱 + 强强度词 → exaggerated
            if ev.get("strength") == "weak" and cls._has_strong_term(text):
                failed.append({
                    "text": text, "verdict": "exaggerated",
                    "reason": f"表述含强度词（{cls._find_strong_term(text)}），但证据强度不足，"
                              "属夸大，禁止直接使用。"})
                continue

            # 弱证据 → 需确认（可降级表述）
            if ev.get("strength") == "weak":
                needs_confirmation.append({
                    "text": text, "verdict": "unverified",
                    "reason": "证据强度不足，建议降级表述或补充证据。"})
                continue

            # 强证据 → 通过
            passed.append({"text": text, "verdict": "verified",
                           "reason": "有充分证据支持。"})

        return {
            "passed": passed,
            "failed": failed,
            "needs_confirmation": needs_confirmation,
            "summary": {
                "total": len(claims),
                "verified": len(passed),
                "unverified": len(needs_confirmation),
                "exaggerated": len(failed),
            },
        }

    @classmethod
    def _has_strong_term(cls, text: str) -> bool:
        return cls._find_strong_term(text) is not None

    @classmethod
    def _find_strong_term(cls, text: str) -> str:
        for t in cls._STRONG_TERMS:
            if t.lower() in text.lower():
                return t
        return ""


class ConfirmationGate:
    """确认门——生成待确认问题清单（用于 MCP 对话流向用户追问）。"""

    @classmethod
    def ask(cls, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """把需要确认的主张转为问题清单。"""
        questions = []
        for c in claims:
            text = c.get("text", "")
            questions.append({
                "question": f"关于「{text}」，请确认该表述是否准确？如有，请提供证据或更正。",
                "claim": text,
            })
        return questions
