# -*- coding: utf-8 -*-
"""resume_product.api — Flask API（网页产品后端，接入全部基线对齐能力 ⭐）。

网页端全链路：经历采集 → 事实校验（claim_gate）→ JD 匹配（五维评分）→
多版本生成（稳妥/专业/高竞争力）→ ATS 校验 → 导出（HTML/Word/PDF）。

端点：
- GET  /api/health            健康检查
- GET  /api/role-packs        行业方向清单
- POST /api/enrich            经历 → 事实卡（含 claim_gate 分档）
- POST /api/claim-check       事实校验（verified/unverified/exaggerated）
- POST /api/match             JD 五维匹配评分（匹配项/缺失项）
- POST /api/versions          多版本输出（稳妥/专业/高竞争力）
- POST /api/ats               ATS 兼容性校验（通过率评分）
- POST /api/trim              相关性加权裁剪
- POST /api/interview         面试准备（STAR/难题/反问）
- POST /api/skill-gaps        技能缺口分析 + 学习路径
- POST /api/generate          生成简历（markdown/html）
- POST /api/export            导出（docx/pdf 文件下载）
- GET  /                      前端页面
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_file

from .core import enrich_experience, generate_resume, list_role_packs
from .claim_gate import ClaimGate, ConfirmationGate
from .job_evaluation import evaluate_fit
from .multi_version import generate_versions
from .ats_check import ats_check
from .cv_trim import trim_experience
from .interview_prep import prepare as prepare_interview
from .skill_gap import analyze_gaps

_DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "web"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(_DEMO_DIR), static_url_path="/web")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True, "service": "resume-product"})

    @app.route("/api/role-packs")
    def role_packs():
        return jsonify({"ok": True, "role_packs": list_role_packs()})

    @app.route("/api/templates")
    def templates():
        """PDF 渲染模板清单（前端模板示例卡片数据源）。"""
        from .render.render_pdf import TEMPLATE_META, TEMPLATE_IDS
        return jsonify({
            "ok": True,
            "templates": [
                {"id": tid, **TEMPLATE_META.get(tid, {})} for tid in TEMPLATE_IDS
            ],
        })

    @app.route("/api/enrich", methods=["POST"])
    def enrich():
        """经历 → 事实卡（含 claim_gate 分档：verified/unverified/exaggerated）。"""
        data = request.get_json(force=True) or {}
        raw = data.get("raw_text", "")
        facts = enrich_experience(raw)
        # claim_gate 分档：claim 直接引自用户原文（原文即证据），故证据为 strong；
        # 若 claim 含强度词且证据缺失才会被判 exaggerated/unverified
        claims = [{"text": f.get("claim", ""), "evidence_key": "auto"} for f in facts]
        evidence = {"auto": {"strength": "strong", "text": raw}}
        gate = ClaimGate.review(claims, evidence)
        verdict_map = {}
        for item in gate["passed"]:
            verdict_map[item["text"]] = "verified"
        for item in gate["needs_confirmation"]:
            verdict_map[item["text"]] = "unverified"
        for item in gate["failed"]:
            verdict_map[item["text"]] = "exaggerated"
        for f in facts:
            f["verdict"] = verdict_map.get(f.get("claim", ""), "unverified")
        return jsonify({
            "ok": True,
            "facts": facts,
            "gate_summary": gate["summary"],
            "confirm_questions": ConfirmationGate.ask(claims[:5]),
        })

    @app.route("/api/claim-check", methods=["POST"])
    def claim_check():
        data = request.get_json(force=True) or {}
        r = ClaimGate.review(data.get("claims", []), data.get("evidence", {}))
        return jsonify({"ok": True, "result": r})

    @app.route("/api/match", methods=["POST"])
    def match():
        """JD 五维匹配评分：匹配项/缺失项标注。"""
        data = request.get_json(force=True) or {}
        posting = {
            "title": data.get("jd_title", ""),
            "description": data.get("jd_text", ""),
            "location": data.get("location", ""),
        }
        profile = data.get("profile", {}) or {
            "skills": data.get("skills", []),
            "experience": data.get("experience", []),
            "languages": data.get("languages", []),
            "career_goals": data.get("career_goals", []),
            "behavioral": data.get("behavioral", {}),
        }
        r = evaluate_fit(posting, profile)
        return jsonify({"ok": True, "result": r})

    @app.route("/api/improve", methods=["POST"])
    def improve():
        """低分简历改进建议（rewrite 可应用 / gap 不编造）。"""
        data = request.get_json(force=True) or {}
        facts = data.get("facts", [])
        posting = {
            "title": data.get("jd_title", ""),
            "description": data.get("jd_text", ""),
            "location": data.get("location", ""),
        }
        profile = {
            "skills": data.get("skills", []),
            "experience": [{"summary": f.get("claim", "")} for f in facts],
            "languages": data.get("languages", []),
            "career_goals": data.get("career_goals", []),
            "behavioral": data.get("behavioral", {}),
        }
        # 服务端内部重跑评估（不信任客户端分数）
        evaluation = evaluate_fit(posting, profile)
        if not evaluation.get("scored"):
            return jsonify({"ok": False, "error": "前置门未通过，无法评分",
                            "result": evaluation}), 400
        # LLM 优先，失败降级规则兜底
        from .improve import generate_improvements
        from . import llm_client
        degraded = False
        try:
            suggestions = generate_improvements(facts, evaluation, posting,
                                                chat_fn=llm_client.chat)
            degraded = not suggestions
        except Exception:
            suggestions = generate_improvements(facts, evaluation, posting,
                                                chat_fn=None)
            degraded = True
        if not suggestions:
            suggestions = generate_improvements(facts, evaluation, posting,
                                                chat_fn=None)
            degraded = True
        return jsonify({
            "ok": True,
            "evaluation": evaluation,
            "suggestions": suggestions,
            "degraded": degraded,
        })

    @app.route("/api/versions", methods=["POST"])
    def versions():
        """多版本输出：稳妥/专业/高竞争力横向对比。"""
        data = request.get_json(force=True) or {}
        r = generate_versions(data.get("content", ""), data.get("target", ""))
        return jsonify({"ok": True, "versions": r})

    @app.route("/api/ats", methods=["POST"])
    def ats():
        """ATS 兼容性校验：关键词覆盖/联系方式/通过率评分。"""
        data = request.get_json(force=True) or {}
        r = ats_check(data.get("resume_text", ""))
        return jsonify({"ok": True, "result": r})

    @app.route("/api/trim", methods=["POST"])
    def trim():
        data = request.get_json(force=True) or {}
        r = trim_experience(data.get("entries", []),
                            data.get("target_role", ""),
                            int(data.get("max_items", 5)),
                            data.get("target_desc", ""))
        return jsonify({"ok": True, "result": r})

    @app.route("/api/interview", methods=["POST"])
    def interview():
        data = request.get_json(force=True) or {}
        r = prepare_interview(data.get("role", ""), data.get("company", ""),
                              data.get("profile", {}), data.get("jd_text", ""))
        return jsonify({"ok": True, "result": r})

    @app.route("/api/skill-gaps", methods=["POST"])
    def skill_gaps():
        data = request.get_json(force=True) or {}
        r = analyze_gaps(data.get("jobs", []), data.get("profile", {}))
        return jsonify({"ok": True, "result": r})

    @app.route("/api/generate", methods=["POST"])
    def generate():
        data = request.get_json(force=True) or {}
        experiences = data.get("experiences", [])
        target_role = data.get("target_role", "")
        fmt = data.get("format", "markdown")
        resume = generate_resume(experiences, target_role=target_role, format=fmt)
        return jsonify({"ok": True, "resume": resume, "format": fmt})

    @app.route("/api/export", methods=["POST"])
    def export():
        """导出 docx/pdf 文件下载（PDF 支持模板选择 + 自定义 CSS）。"""
        data = request.get_json(force=True) or {}
        experiences = data.get("experiences", [])
        target_role = data.get("target_role", "")
        fmt = data.get("format", "docx")
        template = data.get("template", "classic")
        custom_css = data.get("custom_css")
        if fmt not in ("docx", "pdf"):
            return jsonify({"ok": False, "error": f"不支持的格式: {fmt}"}), 400
        if fmt == "pdf":
            from .core import generate_resume as _gen_md
            md = _gen_md(experiences, target_role=target_role, format="markdown")
            from .render.render_pdf import render_markdown_to_pdf
            import tempfile
            path = os.path.join(tempfile.gettempdir(), "resume_export.pdf")
            try:
                path = render_markdown_to_pdf(md, path, template=template,
                                              custom_css=custom_css)
            except Exception as e:
                return jsonify({"ok": False,
                                "error": f"PDF 渲染失败（Chrome/Playwright 依赖）: {str(e)[:200]}"}), 500
            if path.endswith(".pdf"):
                return send_file(path, as_attachment=True,
                                 download_name="我的简历.pdf",
                                 mimetype="application/pdf")
            return jsonify({"ok": False, "error": "PDF 未生成"}), 500
        path = generate_resume(experiences, target_role=target_role, format=fmt)
        if isinstance(path, str) and path.endswith("." + fmt):
            name = f"我的简历.{fmt}"
            if fmt == "docx":
                mimetype = ("application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document")
            else:
                mimetype = "application/pdf"
            return send_file(path, as_attachment=True, download_name=name,
                             mimetype=mimetype)
        return jsonify({"ok": False, "error": f"{fmt} 导出失败，未生成文件"}), 500

    @app.route("/api/import-docx", methods=["POST"])
    def import_docx():
        """上传 Word 简历 → 解析排版 → 返回还原 CSS + HTML（完美还原原排版）。"""
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "缺少 file 字段（multipart/form-data）"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "空文件名"}), 400
        suffix = os.path.splitext(f.filename)[1].lower() or ".docx"
        if suffix != ".docx":
            return jsonify({"ok": False,
                            "error": f"仅支持 .docx，收到 {suffix}"}), 400
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(),
                           f"resume_import_{os.urandom(4).hex()}.docx")
        f.save(tmp)
        try:
            from .render.docx_import import import_docx_resume
            r = import_docx_resume(tmp)
        except ImportError:
            return jsonify({"ok": False,
                            "error": "python-docx 未安装（pip install resume-product[resume_extract]）"}), 500
        except Exception as e:
            return jsonify({"ok": False, "error": f"解析失败: {str(e)[:200]}"}), 500
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return jsonify({
            "ok": True,
            "html": r["html"],
            "css": r["css"],
            "meta": r["meta"],
            "filename": f.filename,
        })

    @app.route("/")
    def index():
        idx = _DEMO_DIR / "index.html"
        if idx.exists():
            return idx.read_text(encoding="utf-8")
        return "resume-product 运行中（前端待构建）"

    return app
