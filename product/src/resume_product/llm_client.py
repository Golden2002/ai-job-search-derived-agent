# -*- coding: utf-8 -*-
"""resume_product.llm_client —— DeepSeek LLM 客户端（OpenAI 兼容）。

Key 读取顺序：auth.json（opencode 配置）→ 环境变量 DEEPSEEK_API_KEY。
失败一律返回空串（调用方降级到确定性模式）。
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

_API_URL = "https://api.deepseek.com/chat/completions"
_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def _get_key() -> str:
    env = os.environ.get("DEEPSEEK_API_KEY", "")
    if env:
        return env
    auth = os.path.expanduser("~/.local/share/opencode/auth.json")
    if os.path.exists(auth):
        try:
            d = json.load(open(auth, encoding="utf-8"))
            return d.get("deepseek", {}).get("key", "")
        except Exception:
            pass
    return ""


def chat(sys_prompt: str, user_prompt: str,
         temperature: float = 0.3, max_tokens: int = 3000,
         timeout: int = 120) -> str:
    """同步调用 DeepSeek（无第三方依赖）。失败返回空串。"""
    key = _get_key()
    if not key:
        return ""
    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        _API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return (msg.get("content") or "").strip()
        return ""
    except Exception:
        return ""
