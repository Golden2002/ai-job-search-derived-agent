# -*- coding: utf-8 -*-
"""resume_product.tools.schema — 标准化工具契约（MCP 风格 JSON Schema ⭐）。

开发者可自动发现工具能力（MCP tools/list + tools/call 等价）。
"""

from __future__ import annotations

from typing import Any, Dict, List

TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "generate_resume": {
        "name": "generate_resume",
        "description": "生成简历：结构化经历 → 定向简历（markdown/html）。按目标岗位用 Role Pack 适配表达。",
        "inputs": {
            "type": "object",
            "properties": {
                "experiences_json": {"type": "string", "description": "结构化经历 JSON 数组"},
                "target_role": {"type": "string", "description": "目标岗位（触发 Role Pack 适配）"},
                "format": {"type": "string", "enum": ["markdown", "html"], "default": "markdown"},
            },
            "required": ["experiences_json"],
        },
        "outputs": {"type": "object", "properties": {"ok": {"type": "boolean"}, "resume": {"type": "string"}}},
    },
    "enrich_experience": {
        "name": "enrich_experience",
        "description": "经历文本 → 结构化事实卡（主张校验——引用原文，保留量化数据）。",
        "inputs": {
            "type": "object",
            "properties": {"raw_text": {"type": "string", "description": "原始经历描述"}},
            "required": ["raw_text"],
        },
        "outputs": {"type": "object", "properties": {"ok": {"type": "boolean"}, "facts": {"type": "array"}}},
    },
    "list_role_packs": {
        "name": "list_role_packs",
        "description": "可用通用 Role Pack 清单（行业方向：tech/consulting/finance 等）。",
        "inputs": {"type": "object", "properties": {}},
        "outputs": {"type": "object", "properties": {"ok": {"type": "boolean"}, "role_packs": {"type": "array"}}},
    },
    # ---- 基线对齐补全工具（批次 A-E）----
    "evaluate_fit": {
        "name": "evaluate_fit",
        "description": "职位匹配度五维度评估评分（资格门+语言门+技术/经验/行为/地点/职业对齐）。",
        "inputs": {"type": "object", "properties": {
            "posting": {"type": "object", "description": "职位信息（title/description/location）"},
            "profile": {"type": "object", "description": "候选人画像（skills/experience/languages/career_goals）"}}},
        "outputs": {"type": "object"},
    },
    "trim_experience": {
        "name": "trim_experience",
        "description": "相关性加权裁剪（相关性+独特性+依赖度，非机械时间裁剪）。",
        "inputs": {"type": "object", "properties": {
            "entries": {"type": "array"}, "target_role": {"type": "string"},
            "max_items": {"type": "integer"}}},
        "outputs": {"type": "object"},
    },
    "rank_postings": {
        "name": "rank_postings",
        "description": "多职位批量评分排序。",
        "inputs": {"type": "object", "properties": {
            "postings": {"type": "array"}, "profile": {"type": "object"}}},
        "outputs": {"type": "object"},
    },
    "salary_benchmark": {
        "name": "salary_benchmark",
        "description": "薪资基准对比（分位区间 + 低于/符合/高于市场结论）。",
        "inputs": {"type": "object", "properties": {
            "role": {"type": "string"}, "region": {"type": "string"},
            "years": {"type": "number"}, "sources": {"type": "array"},
            "expected": {"type": "number"}}},
        "outputs": {"type": "object"},
    },
    "prepare_interview": {
        "name": "prepare_interview",
        "description": "面试准备（STAR 故事 + 高频难题 + 反问清单）。",
        "inputs": {"type": "object", "properties": {
            "role": {"type": "string"}, "company": {"type": "string"},
            "profile": {"type": "object"}, "jd_text": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "simulate_interview": {
        "name": "simulate_interview",
        "description": "STAR 框架模拟面试（问答结构）。",
        "inputs": {"type": "object", "properties": {
            "role": {"type": "string"}, "profile": {"type": "object"},
            "rounds": {"type": "integer"}}},
        "outputs": {"type": "object"},
    },
    "track_application": {
        "name": "track_application",
        "description": "记录一条求职申请（状态机 applied→interview→offer→rejected→withdrawn）。",
        "inputs": {"type": "object", "properties": {
            "company": {"type": "string"}, "role": {"type": "string"},
            "source": {"type": "string"}, "deadline": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "generate_followup": {
        "name": "generate_followup",
        "description": "生成跟进信（按 7/14/21 天分档）。",
        "inputs": {"type": "object", "properties": {
            "entry": {"type": "object"}, "days_since": {"type": "integer"}}},
        "outputs": {"type": "object"},
    },
    "analyze_skill_gaps": {
        "name": "analyze_skill_gaps",
        "description": "技能缺口分析 + 学习路径建议（频率热图 + 权重）。",
        "inputs": {"type": "object", "properties": {
            "jobs": {"type": "array"}, "profile": {"type": "object"}}},
        "outputs": {"type": "object"},
    },
    "claim_review": {
        "name": "claim_review",
        "description": "事实校验（verified/unverified/exaggerated，不静默升级）。",
        "inputs": {"type": "object", "properties": {
            "claims": {"type": "array"}, "evidence": {"type": "object"}}},
        "outputs": {"type": "object"},
    },
    "generate_versions": {
        "name": "generate_versions",
        "description": "多版本输出（稳妥版/专业版/高竞争力版）。",
        "inputs": {"type": "object", "properties": {
            "content": {"type": "string"}, "target": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "decompose_experience": {
        "name": "decompose_experience",
        "description": "经历拆解六要素（研究对象/方法/工具/角色/交付物/可迁移能力）。",
        "inputs": {"type": "object", "properties": {
            "raw_experience": {"type": "string"},
            "target_direction": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "tag_experience": {
        "name": "tag_experience",
        "description": "经历标签化（能力分类体系）。",
        "inputs": {"type": "object", "properties": {
            "experience": {"type": "object"}}},
        "outputs": {"type": "object"},
    },
    "list_templates": {
        "name": "list_templates",
        "description": "列出简历模板（moderncv_banking/resume_html/generic_md 等）。",
        "inputs": {"type": "object", "properties": {}},
        "outputs": {"type": "object"},
    },
    "register_template": {
        "name": "register_template",
        "description": "注册自定义模板（校验文件存在 + 格式合法）。",
        "inputs": {"type": "object", "properties": {
            "template_id": {"type": "string"}, "name": {"type": "string"},
            "format": {"type": "string"}, "path": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "compile_latex": {
        "name": "compile_latex",
        "description": "LaTeX 编译链 + 视觉校验（lualatex，2 页硬要求）。",
        "inputs": {"type": "object", "properties": {
            "tex_path": {"type": "string"}, "workdir": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
    "portal_search": {
        "name": "portal_search",
        "description": "职位门户搜索（可扩展适配器架构）。",
        "inputs": {"type": "object", "properties": {
            "portal_name": {"type": "string"}, "query": {"type": "string"},
            "portal_path": {"type": "string"}}},
        "outputs": {"type": "object"},
    },
}


def list_tool_schemas() -> List[Dict[str, Any]]:
    return list(TOOL_SCHEMAS.values())


def get_tool_schema(name: str) -> Dict[str, Any]:
    return TOOL_SCHEMAS.get(name, {})


def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """统一工具调用（JSON 契约，绝不抛异常）。"""
    from ..executor import execute
    import json as _json
    try:
        raw = execute(name, arguments)
        parsed = _json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(parsed, dict) and parsed.get("ok") is False:
            return {"ok": False, "tool": name, "error": parsed.get("error", "调用失败")}
        return {"ok": True, "tool": name, "result": parsed}
    except Exception as e:
        return {"ok": False, "tool": name, "error": str(e)[:300]}
