# -*- coding: utf-8 -*-
"""resume_product.core — 通用简历引擎（W4-W5 ⭐）。

复用 medical-resume-agent 引擎（claim_gate/confirmation_gate/experience_draft/
bullet_composer）+ 通用化改造（去医学化 + 全行业 Role Pack）。

架构：
- 经历采集：LLM 从原始文本提取事实卡（主张必须引用原文——claim gate 思想）
- 定向表达：Role Pack 适配（能力重排/动词优化/句式模板）
- 简历生成：结构化事实卡 → markdown/html（可扩展 LaTeX/PDF）
- 可注入 chat_fn（PAEG 生态——外部智能体接入）
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 复用 medical-resume-agent 引擎（不重复造轮子）
_MEDICAL_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", "..", "..",
                            "medical-resume-agent", "src")
if _MEDICAL_SRC not in os.sys.path:
    os.sys.path.insert(0, _MEDICAL_SRC)

# 数据目录（product/data/——role_packs + capability_tags）
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_json(name: str) -> Dict[str, Any]:
    p = _DATA_DIR / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _load_role_packs() -> Dict[str, Dict[str, Any]]:
    """加载通用 Role Pack（data/role_packs/*.json）。"""
    packs: Dict[str, Dict[str, Any]] = {}
    d = _DATA_DIR / "role_packs"
    if d.is_dir():
        for f in d.glob("*.json"):
            try:
                packs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
    return packs


def _default_chat(sys_p: str, usr_p: str) -> str:
    """默认 chat_fn：无 LLM 时返回空（确定性模式）。"""
    return ""


class ResumeEngine:
    """通用简历引擎（可注入 LLM——PAEG 生态 ⭐）。"""

    def __init__(self, chat_fn: Optional[Callable] = None,
                 role_pack: str = "tech_v1"):
        self.chat_fn = chat_fn or _default_chat
        self.role_pack = role_pack

    def enrich(self, raw_text: str) -> List[Dict[str, str]]:
        """经历文本 → 结构化事实卡（主张校验思想）。

        无 LLM 时：确定性启发式提取（量化数字/动词短语）。
        有 LLM 时：提示词提取事实卡（要求引用原文）。
        """
        if not raw_text or not raw_text.strip():
            return []
        if self.chat_fn is _default_chat:
            return self._heuristic_extract(raw_text)
        # LLM 提取（主张校验——要求引用原文）
        sys_p = ("你是经历拆解助手。从用户提供的经历描述中提取结构化事实卡。"
                 "每张事实卡必须：1) 保留原文关键信息 2) 标注可验证的证据 3) 保留量化数据。"
                 '输出 JSON 数组：[{"claim": "主张", "evidence": "证据", "quote": "原文引用"}]')
        raw = self.chat_fn(sys_p, f"经历描述：{raw_text}")
        try:
            import re
            m = re.search(r"\[.*\]", raw or "", re.S)
            if m:
                data = json.loads(m.group(0))
                return [d for d in data if isinstance(d, dict)]
        except Exception:
            pass
        return self._heuristic_extract(raw_text)

    def _heuristic_extract(self, raw_text: str) -> List[Dict[str, str]]:
        """确定性提取（无 LLM 兜底）：按句拆事实卡。"""
        import re
        sentences = re.split(r"[。！？!?；;]", raw_text)
        facts = []
        for s in sentences:
            s = s.strip()
            if len(s) < 4:
                continue
            facts.append({"claim": s, "evidence": s,
                          "quote": s, "source": "heuristic"})
        return facts

    def compose(self, facts: List[Dict[str, str]],
                target_role: str = "") -> str:
        """定向表达：Role Pack 适配 → markdown 简历。"""
        pack = _load_role_packs().get(self.role_pack, {})
        label = pack.get("label", "通用")
        lines = [f"# {target_role or '个人简历'}", ""]
        if pack.get("priorities"):
            lines.append(f"**适配方向**：{label}（{', '.join(pack['priorities'])}）")
            lines.append("")
        for i, fact in enumerate(facts[:10], 1):
            claim = fact.get("claim", "")
            ev = fact.get("evidence", "")
            if claim:
                lines.append(f"{i}. {claim}")
                if ev and ev != claim:
                    lines.append(f"   - 证据：{ev}")
        return "\n".join(lines)

    def to_html(self, facts: List[Dict[str, str]],
                target_role: str = "") -> str:
        """结构化 → HTML 简历。"""
        md = self.compose(facts, target_role)
        import html as _h
        title = _h.escape(target_role or "个人简历")
        body = ""
        for line in md.split("\n"):
            if line.startswith("# "):
                body += f"<h1>{_h.escape(line[2:])}</h1>"
            elif line.startswith("**"):
                body += f"<p><strong>{_h.escape(line.strip('*'))}</strong></p>"
            elif line.strip().startswith("- "):
                body += f"<li>{_h.escape(line.strip()[2:])}</li>"
            elif line.strip() and line.strip()[0].isdigit() and "." in line[:4]:
                body += f"<p>{_h.escape(line)}</p>"
            elif line.strip():
                body += f"<p>{_h.escape(line)}</p>"
        return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:'SimSun',serif;max-width:800px;margin:40px auto;line-height:1.7}}
h1{{text-align:center;border-bottom:1px solid #333;padding-bottom:8px}}</style>
</head><body>{body}</body></html>"""


# ═══════════════════════════════════════════════════════════
# 便捷 API（MCP 工具对应）
# ═══════════════════════════════════════════════════════════
_engine = ResumeEngine()


def enrich_experience(raw_text: str) -> List[Dict[str, str]]:
    """经历文本 → 结构化事实卡（主张校验）。"""
    return _engine.enrich(raw_text)


def generate_resume(experiences: List[Dict[str, str]],
                    target_role: str = "",
                    format: str = "markdown",
                    chat_fn: Optional[Callable] = None) -> str:
    """经历 → 定向简历（markdown/html）。"""
    eng = ResumeEngine(chat_fn=chat_fn or _engine.chat_fn)
    if format == "html":
        return eng.to_html(experiences, target_role)
    return eng.compose(experiences, target_role)


def list_role_packs() -> List[str]:
    """可用通用 Role Pack 清单。"""
    return sorted(_load_role_packs().keys())
