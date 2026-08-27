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
        if fmt == "docx":
            # Word 导出——生成文件并返回下载
            from .core import generate_resume as _gen
            path = _gen(experiences, target_role=target_role, format="docx")
            if path.endswith(".docx"):
                from flask import send_file
                return send_file(path, as_attachment=True,
                                 download_name="我的简历.docx",
                                 mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            return jsonify({"ok": True, "resume": open(path, encoding="utf-8").read(),
                            "format": "text"})
        if fmt == "pdf":
            # PDF 导出——固定资产渲染
            from .core import generate_resume as _gen
            path = _gen(experiences, target_role=target_role, format="pdf")
            if path.endswith(".pdf"):
                from flask import send_file
                return send_file(path, as_attachment=True,
                                 download_name="我的简历.pdf",
                                 mimetype="application/pdf")
            return jsonify({"ok": True, "resume": open(path, encoding="utf-8").read(),
                            "format": "text"})
        resume = generate_resume(experiences, target_role=target_role, format=fmt)
        return jsonify({"ok": True, "resume": resume, "format": fmt})

    @app.route("/")
    def index():
        idx = _DEMO_DIR / "index.html"
        if idx.exists():
            return idx.read_text(encoding="utf-8")
        return "resume-product 运行中（前端待构建）"

    return app
