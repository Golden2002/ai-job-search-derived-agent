# -*- coding: utf-8 -*-
"""resume_product.api — Flask API（W9 ⭐ 网页产品后端）。

复用 medical-resume-agent 的 Flask 模式，提供网页产品后端：
- POST /api/enrich（经历→事实卡）
- POST /api/generate（事实卡→定向简历）
- GET  /api/role-packs（行业方向清单）
- GET  /（前端页面）
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request

from .core import enrich_experience, generate_resume, list_role_packs

_DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "web"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(_DEMO_DIR), static_url_path="/web")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True, "service": "resume-product"})

    @app.route("/api/role-packs")
    def role_packs():
        return jsonify({"ok": True, "role_packs": list_role_packs()})

    @app.route("/api/enrich", methods=["POST"])
    def enrich():
        data = request.get_json(force=True) or {}
        raw = data.get("raw_text", "")
        facts = enrich_experience(raw)
        return jsonify({"ok": True, "facts": facts})

    @app.route("/api/generate", methods=["POST"])
    def generate():
        data = request.get_json(force=True) or {}
        experiences = data.get("experiences", [])
        target_role = data.get("target_role", "")
        fmt = data.get("format", "markdown")
        resume = generate_resume(experiences, target_role=target_role, format=fmt)
        return jsonify({"ok": True, "resume": resume, "format": fmt})

    @app.route("/")
    def index():
        idx = _DEMO_DIR / "index.html"
        if idx.exists():
            return idx.read_text(encoding="utf-8")
        return "resume-product 运行中（前端待构建）"

    return app
