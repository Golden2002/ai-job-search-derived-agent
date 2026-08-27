# -*- coding: utf-8 -*-
"""resume_product.mcp_server — 简历工具 MCP server（W10 ⭐ PAEG 生态）。

像 MCP 一样直接安装即可用：
- pip install + MCP 配置声明即接入
- console_scripts: resume-mcp
- 可被 PAEG 主 Agent 调度（工具 schema + 统一调用契约）
"""

from __future__ import annotations

import json
import os
import sys

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from .executor import execute

SERVER_NAME = "resume-product"


def build_server() -> "FastMCP":
    """构建 MCP server（幂等）。"""
    if FastMCP is None:
        raise RuntimeError("fastmcp 未安装：pip install 'resume-product[mcp]'")

    mcp = FastMCP(name=SERVER_NAME, strict_input_validation=True)

    @mcp.tool()
    def generate_resume(experiences_json: str, target_role: str = "",
                        format: str = "markdown") -> str:
        """生成简历：结构化经历 → 定向简历（markdown/html）。"""
        return execute("generate_resume", {
            "experiences_json": experiences_json,
            "target_role": target_role, "format": format})

    @mcp.tool()
    def enrich_experience(raw_text: str) -> str:
        """经历文本 → 结构化事实卡（主张校验，引用原文）。"""
        return execute("enrich_experience", {"raw_text": raw_text})

    @mcp.tool()
    def list_role_packs() -> str:
        """可用通用 Role Pack 清单（行业方向）。"""
        return execute("list_role_packs", {})

    @mcp.tool()
    def list_tools() -> str:
        """工具 schema 清单（MCP tools/list 等价）。"""
        from .tools.schema import list_tool_schemas
        return json.dumps({"ok": True, "tools": list_tool_schemas()},
                          ensure_ascii=False)

    return mcp


def main():
    """CLI 入口：启动 MCP server（stdio）。"""
    if FastMCP is None:
        print("错误：fastmcp 未安装，请先 pip install 'resume-product[mcp]'",
              file=sys.stderr)
        sys.exit(1)
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
