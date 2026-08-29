# -*- coding: utf-8 -*-
"""resume_product.llm_client —— DeepSeek LLM 客户端（OpenAI 兼容，零第三方依赖）。

对齐主项目（14_教育者Agent项目 llm_api.py）的配置发现优先级：
  1. 环境变量 PAEG_API_KEY（+PAEG_API_BASE / PAEG_MODEL，主项目自定义）
  2. 环境变量 DEEPSEEK_API_KEY（→ DeepSeek）
  3. opencode auth.json（项目 secret/auth.json 优先，再 opencode 系统级；
     同时识别 key 与 api_key 两种字段）

无 key 时返回空串（调用方降级到确定性模式——/api/chat 走规则式追问）。
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

_API_URL_DEFAULT = "https://api.deepseek.com/chat/completions"
_MODEL_DEFAULT = "deepseek-chat"

# 旧模型别名迁移（主项目 llm_api._migrate_model：旧别名已下线）
_MODEL_ALIASES = {"deepseek-reasoner": "deepseek-v4-flash"}


def _load_env_dotenv() -> None:
    """加载 .env（无第三方依赖的轻量实现；已存在的环境变量不覆盖）。

    主项目用 .env 存 DEEPSEEK_API_KEY——独立运行时需要显式加载。
    扫描顺序：本包 product 根目录 → 当前工作目录。
    """
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates = [
        os.path.join(base, ".env"),
        os.path.join(base, "product", ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for p in candidates:
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


def _find_auth_key() -> str:
    """在 auth.json 系列中查找 deepseek key（对齐主项目 llm_api._find_opencode_auth）。

    项目级 secret/auth.json 优先，再 opencode 系统级（~/.local / ~/.config / APPDATA）。
    同时识别 {"key": ...} 与 {"api_key": ...} 两种字段。
    """
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_secret = os.path.join(base, "secret", "auth.json")
    candidates = [
        project_secret,
        os.path.expanduser("~/.local/share/opencode/auth.json"),
        os.path.expanduser("~/.config/opencode/auth.json"),
        os.path.join(os.environ.get("APPDATA", ""), "opencode", "auth.json"),
    ]
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            entry = data.get("deepseek")
            if isinstance(entry, dict):
                key = entry.get("key") or entry.get("api_key")
                if key:
                    return str(key).strip()
            elif isinstance(entry, str) and entry.strip():
                return entry.strip()
        except Exception:
            continue
    return ""


def _get_key() -> str:
    """读 API key：PAEG_API_KEY → DEEPSEEK_API_KEY → auth.json（含 .env 加载）。"""
    _load_env_dotenv()
    for name in ("PAEG_API_KEY", "DEEPSEEK_API_KEY"):
        env = os.environ.get(name, "").strip()
        if env:
            return env
    return _find_auth_key()


def _normalize_url(base: str) -> str:
    """base → chat/completions 完整端点（对齐主项目 OpenAICompatModelAPI._url）。"""
    base = (base or "").rstrip("/")
    if not base:
        return _API_URL_DEFAULT
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def _get_url() -> str:
    _load_env_dotenv()
    custom = os.environ.get("PAEG_API_BASE", "").strip() or os.environ.get(
        "DEEPSEEK_API_URL", "").strip()
    if custom:
        return _normalize_url(custom)
    return _API_URL_DEFAULT


def _get_model() -> str:
    _load_env_dotenv()
    model = (os.environ.get("PAEG_MODEL", "").strip()
             or os.environ.get("DEEPSEEK_MODEL", "").strip()
             or _MODEL_DEFAULT)
    return _MODEL_ALIASES.get(model, model)


def chat(sys_prompt: str, user_prompt: str,
         temperature: float = 0.3, max_tokens: int = 3000,
         timeout: int = 120) -> str:
    """同步调用 DeepSeek（无第三方依赖）。失败 / 无 key 一律返回空串。"""
    key = _get_key()
    if not key:
        return ""
    payload = {
        "model": _get_model(),
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        _get_url(),
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
