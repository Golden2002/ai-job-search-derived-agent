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
