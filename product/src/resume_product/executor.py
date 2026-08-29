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

    # ---- 基线对齐补全工具（批次 A-E）----

    if name == "evaluate_fit":
        from .job_evaluation import evaluate_fit
        try:
            posting = args.get("posting", {})
            profile = args.get("profile", {})
            return json.dumps({"ok": True, "result": evaluate_fit(posting, profile)},
                              ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "trim_experience":
        from .cv_trim import trim_experience
        try:
            entries = args.get("entries", [])
            r = trim_experience(entries, args.get("target_role", ""),
                                int(args.get("max_items", 5)),
                                args.get("target_desc", ""))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "rank_postings":
        from .rank import rank_postings
        try:
            postings = args.get("postings", [])
            profile = args.get("profile", {})
            return json.dumps({"ok": True, "result": rank_postings(postings, profile)},
                              ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "salary_benchmark":
        from .salary_benchmark import benchmark
        try:
            r = benchmark(args.get("role", ""), args.get("region", ""),
                          float(args.get("years", 0)),
                          sources=args.get("sources"),
                          expected=args.get("expected"))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "prepare_interview":
        from .interview_prep import prepare
        try:
            r = prepare(args.get("role", ""), args.get("company", ""),
                        args.get("profile", {}), args.get("jd_text", ""))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "simulate_interview":
        from .interview_prep import simulate_interview
        try:
            r = simulate_interview(args.get("role", ""), args.get("profile", {}),
                                   int(args.get("rounds", 1)))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "track_application":
        from .application_tracker import ApplicationTracker
        try:
            t = ApplicationTracker()
            e = t.add(args.get("company", ""), args.get("role", ""),
                      source=args.get("source", ""),
                      deadline=args.get("deadline"),
                      contact=args.get("contact", ""), notes=args.get("notes", ""))
            return json.dumps({"ok": True, "entry": e}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "generate_followup":
        from .application_tracker import generate_followup
        try:
            entry = args.get("entry", {})
            days = int(args.get("days_since", 7))
            return json.dumps({"ok": True, "followup": generate_followup(entry, days)},
                              ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "analyze_skill_gaps":
        from .skill_gap import analyze_gaps
        try:
            r = analyze_gaps(args.get("jobs", []), args.get("profile", {}))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "claim_review":
        from .claim_gate import ClaimGate
        try:
            r = ClaimGate.review(args.get("claims", []), args.get("evidence", {}))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "generate_versions":
        from .multi_version import generate_versions
        try:
            r = generate_versions(args.get("content", ""), args.get("target", ""))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "decompose_experience":
        from .schemas.canonical_experience import decompose
        try:
            r = decompose(args.get("raw_experience", ""), args.get("target_direction", ""))
            return json.dumps({"ok": True, "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "tag_experience":
        from .capability_taxonomy import tag_experience
        try:
            r = tag_experience(args.get("experience", {}))
            return json.dumps({"ok": True, "tags": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "list_templates":
        from .template_registry import TemplateRegistry
        try:
            r = TemplateRegistry()
            return json.dumps({"ok": True, "templates": r.list()}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "register_template":
        from .template_registry import TemplateRegistry
        try:
            r = TemplateRegistry()
            t = r.import_template(args.get("template_id", ""), args.get("name", ""),
                                  args.get("format", ""), args.get("path", ""))
            return json.dumps({"ok": True, "template": t}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "compile_latex":
        from .render.latex_compile import compile_tex
        try:
            r = compile_tex(args.get("tex_path", ""), args.get("workdir"))
            return json.dumps({"ok": r.get("ok", False), "result": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "portal_search":
        from .job_portal import PortalRegistry, JSONFilePortal, portal_search
        try:
            reg = PortalRegistry()
            path = args.get("portal_path", "")
            if path:
                reg.register(JSONFilePortal(path))
            r = portal_search(reg, args.get("portal_name", "json_file"),
                              args.get("query", ""))
            return json.dumps({"ok": True, "results": r}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "import_resume_docx":
        from .render.docx_import import import_docx_resume
        try:
            r = import_docx_resume(args.get("docx_path", ""))
            return json.dumps({
                "ok": True,
                "html": r["html"],
                "css": r["css"],
                "meta": r["meta"],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "import_resume_image":
        from .render.image_import import import_resume_image
        try:
            r = import_resume_image(args.get("image_path", ""))
            return json.dumps({
                "ok": True,
                "html": r["html"],
                "css": r["css"],
                "meta": r["meta"],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "import_resume_pdf":
        from .render.pdf_import import import_resume_pdf
        try:
            r = import_resume_pdf(args.get("pdf_path", ""))
            return json.dumps({
                "ok": True,
                "html": r["html"],
                "css": r["css"],
                "meta": r["meta"],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    if name == "import_resume_xlsx":
        from .render.xlsx_import import import_resume_xlsx
        try:
            r = import_resume_xlsx(args.get("xlsx_path", ""))
            return json.dumps({
                "ok": True,
                "html": r["html"],
                "css": r["css"],
                "meta": r["meta"],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    return json.dumps({"ok": False, "error": f"未知工具: {name}"},
                      ensure_ascii=False)
