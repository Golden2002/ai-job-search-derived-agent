# -*- coding: utf-8 -*-
"""resume_product.profile_3d —— 候选人 profile 三维度。

基线对齐：01-candidate-profile.md + 02-behavioral-profile.md + 03-writing-style.md。
三维：candidate（教育/经历/技能/发表/奖项）、behavioral（行为评估/优势/理想环境）、
writing_style（语气/结构/禁忌清单）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Profile3D:
    def __init__(self, candidate: Dict[str, Any], behavioral: Dict[str, Any],
                 writing_style: Dict[str, Any]):
        self.candidate = candidate
        self.behavioral = behavioral
        self.writing_style = writing_style

    def validate(self) -> List[str]:
        """返回校验错误列表（空 = 合法）。"""
        errors = []
        if "name" not in self.candidate:
            errors.append("candidate.name 缺失")
        if "skills" not in self.candidate or not isinstance(self.candidate.get("skills"), list):
            errors.append("candidate.skills 必须为非空列表")
        if "experience" not in self.candidate or not isinstance(self.candidate.get("experience"), list):
            errors.append("candidate.experience 必须为列表")
        ws = self.writing_style
        if "forbidden" in ws and not isinstance(ws.get("forbidden"), list):
            errors.append("writing_style.forbidden 必须为列表")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate,
            "behavioral": self.behavioral,
            "writing_style": self.writing_style,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Profile3D":
        return cls(d.get("candidate", {}), d.get("behavioral", {}), d.get("writing_style", {}))


# 默认 writing_style 禁忌（基线 03-writing-style.md：无 em-dashes、无陈词滥调）
DEFAULT_WRITING_STYLE = {
    "tone": "professional",
    "forbidden": ["em-dash", "cliche", "passive-voice-overuse"],
}
