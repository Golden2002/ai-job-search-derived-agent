# -*- coding: utf-8 -*-
"""W10 ⭐ 简历工具 MCP 标准化测试（工具 schema + 统一调用）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.tools.schema import (
    TOOL_SCHEMAS, list_tool_schemas, get_tool_schema, call_tool,
)
from resume_product.executor import execute


# ── R1: 工具 schema 完整性 ──
def test_schemas_exist():
    """核心工具 schema 声明齐全。"""
    names = [t["name"] for t in list_tool_schemas()]
    assert "generate_resume" in names
    assert "enrich_experience" in names
    assert "list_role_packs" in names


def test_schema_structure():
    """每工具含 name/description/inputs/outputs（MCP 标准）。"""
    for t in list_tool_schemas():
        assert t["name"], "工具名必填"
        assert t["description"], "描述必填"
        assert "inputs" in t, "inputs schema 必填"
        assert "outputs" in t, "outputs schema 必填"


# ── R2: 统一调用（JSON 契约不抛异常）──
def test_call_tool_list_packs():
    """list_role_packs 调用。"""
    r = call_tool("list_role_packs", {})
    assert r["ok"] is True
    assert "tech_v1" in r["result"]["role_packs"]


def test_call_tool_unknown():
    """未知工具 → ok=False 而非抛异常。"""
    r = call_tool("nonexistent", {})
    assert r["ok"] is False


def test_call_tool_generate():
    """generate_resume 调用（markdown）。"""
    r = call_tool("generate_resume", {
        "experiences_json": '[{"claim": "负责推荐算法优化", "evidence": "提升点击率15%"}]',
        "target_role": "算法工程师",
    })
    assert r["ok"] is True
    assert "推荐" in r["result"]["resume"]


def test_call_tool_enrich():
    """enrich_experience 调用（确定性提取）。"""
    r = call_tool("enrich_experience", {"raw_text": "我在公司负责数据分析，提升效率20%。"})
    assert r["ok"] is True
    assert r["result"]["facts"], "应产出事实卡"


# ── R3: executor 直调 ──
def test_executor_generate_html():
    """HTML 格式导出。"""
    import json as _json
    r = _json.loads(execute("generate_resume", {
        "experiences_json": '[{"claim": "数据分析"}]', "format": "html"}))
    assert r["ok"] is True
    assert "<html" in r["resume"].lower()
