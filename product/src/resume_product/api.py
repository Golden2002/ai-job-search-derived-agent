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

_SCENE_PATH = Path(__file__).resolve().parent / "data" / "scene_cards.json"


def load_scenes() -> list:
    """加载分场景卡片（scene_cards.json → scenes 列表）。"""
    try:
        return json.loads(_SCENE_PATH.read_text(encoding="utf-8")).get("scenes", [])
    except Exception:
        return []


def find_stage(stage_id: str, scene_id: str = "", sub_scene_id: str = "") -> dict | None:
    """按 (scene_id, sub_scene_id, stage_id) 精确定位 stage；缺省时全局首匹配。

    stage_id（如 basic/education/work/core）在多个场景中复用，**不全局唯一**；
    前端带 scene_id / sub_scene_id 时优先按上下文定位，避免对话收集取到错误场景的字段。
    """
    if scene_id or sub_scene_id:
        for s in load_scenes():
            if scene_id and s.get("id") != scene_id:
                continue
            for ss in s.get("sub_scenes", []):
                if sub_scene_id and ss.get("id") != sub_scene_id:
                    continue
                for st in ss.get("stages", []):
                    if st.get("id") == stage_id:
                        return st
        return None
    for s in load_scenes():
        for ss in s.get("sub_scenes", []):
            for st in ss.get("stages", []):
                if st.get("id") == stage_id:
                    return st
    return None


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(_DEMO_DIR), static_url_path="/web")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True, "service": "resume-product"})

    @app.route("/api/role-packs")
    def role_packs():
        return jsonify({"ok": True, "role_packs": list_role_packs()})

    @app.route("/api/scene-cards")
    def scene_cards():
        """分场景预制卡片（场景→方向→维度→字段，对话式收集数据源）。"""
        import json as _json
        p = Path(__file__).resolve().parent / "data" / "scene_cards.json"
        try:
            return jsonify({"ok": True, **_json.loads(p.read_text(encoding="utf-8"))})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:200]}), 500

    def _build_collect_system(stage, collected):
        """构建收集助手 system prompt（场景字段约束 → LLM 追问 + 实体抽取）。"""
        lines = []
        for f in stage.get("fields", []):
            opt = f"可选：{' / '.join(f['options'])}" if f.get("options") else ""
            req = "必填" if f.get("required") else "可选"
            lines.append(f"- {f['label']}(key={f['key']})：{req}{'，' + opt if opt else ''}")
        collected_desc = json.dumps(collected, ensure_ascii=False) if collected else "（暂无）"
        return (
            "你是简历信息收集助手，通过对话收集用户的简历信息，帮助补全遗漏。\n"
            f"当前收集维度：「{stage.get('label', '')}」——{stage.get('hint', '')}\n"
            f"需要收集的字段：\n{chr(10).join(lines)}\n"
            f"已收集：{collected_desc}\n\n"
            "任务：\n"
            "1. 从用户输入中识别信息，填充到对应字段（key 用上面的 key）\n"
            "2. 追问缺失的必填字段，每次追问 1-2 个；枚举字段给出可选选项\n"
            "3. 绝不编造用户没说过的信息\n"
            "4. 只输出 JSON，不要其他文字：\n"
            '{"filled": {"字段key": "值"}, "followup": "追问问题", "summary": "已收集小结"}'
        )

    @app.route("/api/chat", methods=["POST"])
    def chat():
        """对话式收集：LLM 约束追问 + 实体抽取（前端 send 接入）。"""
        data = request.get_json(force=True) or {}
        message = data.get("message", "")
        stage_id = data.get("stage_id", "")
        scene_id = data.get("scene_id", "")
        sub_scene_id = data.get("sub_scene_id", "")
        collected = data.get("collected", {}) or {}
        if not message:
            return jsonify({"ok": False, "error": "缺少 message"}), 400
        stage = find_stage(stage_id, scene_id, sub_scene_id)
        if stage is None:
            return jsonify({"ok": False, "error": "未知 stage_id"}), 400
        system = _build_collect_system(stage, collected)
        from .llm_client import chat as llm_chat
        raw = llm_chat(system, f"用户说：{message}", max_tokens=1000)
        if not raw:
            # LLM 不可用 → 降级（前端走规则式追问）
            return jsonify({"ok": True, "filled": {}, "followup": "",
                            "summary": "", "llm": False})
        result = {}
        try:
            import re as _re
            m = _re.search(r"\{.*\}", raw, _re.S)
            result = json.loads(m.group(0)) if m else {}
        except Exception:
            result = {}
        return jsonify({
            "ok": True,
            "filled": result.get("filled", {}),
            "followup": result.get("followup", ""),
            "summary": result.get("summary", ""),
            "llm": True,
        })

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
        resume_text = (data.get("resume_text", "") or "").strip()
        fmt = data.get("format", "docx")
        template = data.get("template", "classic")
        custom_css = data.get("custom_css")
        if fmt not in ("docx", "pdf"):
            return jsonify({"ok": False, "error": f"不支持的格式: {fmt}"}), 400
        if fmt == "pdf":
            from .render.render_pdf import render_markdown_to_pdf
            import tempfile
            # 对话式收集的 resume_text 优先（前端 downloadPDF 契约），否则由 experiences 生成
            md = resume_text if resume_text else generate_resume(
                experiences, target_role=target_role, format="markdown")
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
        if resume_text:
            # 对话式收集的 resume_text 优先（前端 downloadWord 契约）
            from .core import resume_text_to_docx
            path = resume_text_to_docx(resume_text, target_role=target_role)
        else:
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

    @app.route("/api/import-image", methods=["POST"])
    def import_image():
        """上传简历截图 → OCR 排版识别 → 返回还原 CSS + HTML（还原自定义样式）。"""
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "缺少 file 字段（multipart/form-data）"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "空文件名"}), 400
        suffix = os.path.splitext(f.filename)[1].lower() or ".png"
        if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
            return jsonify({"ok": False,
                            "error": f"仅支持图片（png/jpg/jpeg/webp/bmp），收到 {suffix}"}), 400
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(),
                           f"resume_img_{os.urandom(4).hex()}{suffix}")
        f.save(tmp)
        try:
            from .render.image_import import import_resume_image
            r = import_resume_image(tmp)
        except ImportError:
            return jsonify({"ok": False,
                            "error": "OCR 依赖未安装（pip install rapidocr-onnxruntime）"}), 500
        except Exception as e:
            return jsonify({"ok": False, "error": f"识别失败: {str(e)[:200]}"}), 500
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

    @app.route("/api/import-pdf", methods=["POST"])
    def import_pdf():
        """上传 PDF 简历 → pdfplumber 字符级提取 → 返回还原 CSS + HTML。"""
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "缺少 file 字段"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "空文件名"}), 400
        suffix = os.path.splitext(f.filename)[1].lower() or ".pdf"
        if suffix != ".pdf":
            return jsonify({"ok": False, "error": f"仅支持 .pdf，收到 {suffix}"}), 400
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(),
                           f"resume_pdf_{os.urandom(4).hex()}.pdf")
        f.save(tmp)
        try:
            from .render.pdf_import import import_resume_pdf
            r = import_resume_pdf(tmp)
        except ImportError:
            return jsonify({"ok": False, "error": "pdfplumber 未安装"}), 500
        except Exception as e:
            return jsonify({"ok": False, "error": f"解析失败: {str(e)[:200]}"}), 500
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return jsonify({
            "ok": True, "html": r["html"], "css": r["css"],
            "meta": r["meta"], "filename": f.filename,
        })

    @app.route("/api/import-xlsx", methods=["POST"])
    def import_xlsx():
        """上传 Excel 简历 → openpyxl 单元格样式提取 → 返回还原 HTML 表格 + CSS。"""
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "缺少 file 字段"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "空文件名"}), 400
        suffix = os.path.splitext(f.filename)[1].lower() or ".xlsx"
        if suffix not in (".xlsx", ".xlsm"):
            return jsonify({"ok": False, "error": f"仅支持 .xlsx/.xlsm，收到 {suffix}"}), 400
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(),
                           f"resume_xlsx_{os.urandom(4).hex()}{suffix}")
        f.save(tmp)
        try:
            from .render.xlsx_import import import_resume_xlsx
            r = import_resume_xlsx(tmp)
        except ImportError:
            return jsonify({"ok": False, "error": "openpyxl 未安装"}), 500
        except Exception as e:
            return jsonify({"ok": False, "error": f"解析失败: {str(e)[:200]}"}), 500
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return jsonify({
            "ok": True, "html": r["html"], "css": r["css"],
            "meta": r["meta"], "filename": f.filename,
        })

    @app.route("/")
    def index():
        idx = _DEMO_DIR / "index.html"
        if idx.exists():
            return idx.read_text(encoding="utf-8")
        return "resume-product 运行中（前端待构建）"

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=False)
