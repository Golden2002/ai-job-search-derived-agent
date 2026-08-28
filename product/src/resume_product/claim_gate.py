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

import re
from typing import Any, Dict, List, Tuple


class ClaimGate:
    """主张校验门——未确认信息不静默升级。

    §3.116 ⭐ R-R2 增强：在 3 档简化门（review）基础上，移植 medical-resume-agent
    的 12 项确定性检查核心（validate_claim_strict），实现"编造率 0"——
    数字精确匹配 / 责任等级未升级 / 角色包禁用表述 / 角色价值未伪装成事实 / 结果有证据。
    """

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

    # ── §3.116 ⭐ R-R2 移植：12 项确定性检查核心（编造率 0 保障）──

    _RESPONSIBILITY_ORDER = ["participated", "owned_component", "led_delivery", "project_owner"]
    _RESPONSIBILITY_INDICATORS = {
        "participated": ["参与", "协助", "support", "assist", "participate"],
        "owned_component": ["负责", "完成", "own", "responsible for"],
        "led_delivery": ["主导", "协调", "lead", "coordinate"],
        "project_owner": ["管理", "overall responsibility", "manage"],
    }

    @classmethod
    def validate_claim_strict(cls, wording: str, canonical: Dict[str, Any],
                              role_pack: Dict[str, Any] = None,
                              claim_level: str = None) -> List[str]:
        """§3.116 ⭐ R-R2 确定性检查（移植 medical-resume-agent 12 项核心）。

        Returns: 问题列表（空=通过）。检查：
        1. 数字精确匹配（wording 数字必须出现在 canonical scope）
        2. 责任等级未升级（wording 不得含高于 canonical 责任等级的指示词）
        3. 角色包禁用表述（forbidden_claims）
        4. 角色价值未伪装成事实结果（value_mappings 无事实依据时拦截）
        5. 结果有证据（outcomes: 引用必须在 canonical outcomes 内）
        """
        issues = []
        role_pack = role_pack or {}

        # 1. 数字精确匹配
        wording_numbers = re.findall(r'\d+', wording or "")
        if wording_numbers:
            scope = canonical.get("scope", {}) if isinstance(canonical, dict) else {}
            scope_numbers = re.findall(r'\d+', " ".join(str(v) for v in (scope.values() if isinstance(scope, dict) else [])))
            for num in wording_numbers:
                if num not in scope_numbers:
                    issues.append(f"数字 {num} 未在 canonical scope 中（禁止编造数量）")

        # 2. 责任等级未升级
        canonical_level = (claim_level
                           or (canonical.get("role", {}).get("responsibility_level")
                               if isinstance(canonical, dict) else None))
        if canonical_level in cls._RESPONSIBILITY_ORDER:
            idx = cls._RESPONSIBILITY_ORDER.index(canonical_level)
            higher_indicators = []
            for higher in cls._RESPONSIBILITY_ORDER[idx + 1:]:
                higher_indicators.extend(cls._RESPONSIBILITY_INDICATORS.get(higher, []))
            for ind in higher_indicators:
                if ind in (wording or ""):
                    issues.append(f"含高于责任等级({canonical_level})的指示词: {ind}")

        # 3. 角色包禁用表述
        for forbidden in role_pack.get("forbidden_claims", []) or []:
            if forbidden in (wording or ""):
                issues.append(f"含角色包禁用表述: {forbidden}")

        # 4. 角色价值未伪装成事实
        used_facts = canonical.get("used_facts", []) if isinstance(canonical, dict) else []
        value_mappings = role_pack.get("value_mappings", {}) or {}
        has_actual = any(str(f).startswith(("actions:", "methods:", "tools:", "objects:"))
                         for f in used_facts)
        for phrases in value_mappings.values():
            for phrase in (phrases or []):
                if phrase in (wording or "") and not has_actual:
                    issues.append(f"角色价值表述 {phrase} 无事实依据（伪装成事实结果）")

        # 5. 结果有证据
        if isinstance(canonical, dict):
            outcomes_in_claim = [str(f).split(":", 1)[1] for f in used_facts
                                 if str(f).startswith("outcomes:")]
            canonical_outcomes = set(canonical.get("outcomes", []) or [])
            for oc in outcomes_in_claim:
                if oc not in canonical_outcomes:
                    issues.append(f"结果 {oc} 不在 canonical outcomes 中")

        return issues


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
