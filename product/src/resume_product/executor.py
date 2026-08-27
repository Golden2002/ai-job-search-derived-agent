# -*- coding: utf-8 -*-
"""resume_product.executor — 统一执行入口（MCP 契约 ⭐）。

对标 PAEG 插件模式：execute(name, args) → JSON 字符串，绝不抛异常。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def execute(name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
    """统一执行入口（JSON 契约）。

    支持：generate_resume / enrich_experience / list_role_packs
    """
    args = arguments or {}

    if name == "list_role_packs":
        from .core import list_role_packs
        return json.dumps({"ok": True, "role_packs": list_role_packs()},
                          ensure_ascii=False)

    if name == "enrich_experience":
        from .core import enrich_experience
        try:
            facts = enrich_experience(args.get("raw_text", ""))
            return json.dumps({"ok": True, "facts": facts}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]},
                              ensure_ascii=False)

    if name == "generate_resume":
        from .core import generate_resume
        try:
            experiences = json.loads(args.get("experiences_json", "[]"))
            result = generate_resume(
                experiences,
                target_role=args.get("target_role", ""),
                format=args.get("format", "markdown"))
            return json.dumps({"ok": True, "resume": result},
                              ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]},
                              ensure_ascii=False)

    return json.dumps({"ok": False, "error": f"未知工具: {name}"},
                      ensure_ascii=False)
