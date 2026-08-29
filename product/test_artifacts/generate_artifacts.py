# -*- coding: utf-8 -*-
"""test_artifacts 产物生成脚本（可复现）。

用 Flask test_client 逐一实测每个产物端点，把「认可的全部产物」落盘到
product/test_artifacts/（自建），供人工审查与回归比对。

用法：在 product/ 目录下执行  python test_artifacts/generate_artifacts.py
"""
import io
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # product/test_artifacts
_PRODUCT = _HERE.parent                            # product
_SRC = _PRODUCT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from resume_product.api import create_app

WS = Path(r"D:\wbo-workspace")
SAMPLE_DOCX = WS / "test_resume.docx"
SAMPLE_PDF = WS / "test_resume.pdf"
SAMPLE_XLSX = WS / "test_resume.xlsx"
SAMPLE_IMG = WS / "test_resume_screenshot.png"

app = create_app()
app.config["TESTING"] = True
c = app.test_client()

OUT = _HERE


def _w(name, text):
    p = OUT / name
    p.write_text(text, encoding="utf-8")
    return p


def _wj(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _wb(name, data: bytes):
    p = OUT / name
    p.write_bytes(data)
    return p


def _j(r):
    return r.get_json()


def _import(ep, sample, name):
    with open(sample, "rb") as f:
        r = c.post(ep, data={"file": (f, sample.name)},
                   content_type="multipart/form-data")
    d = _j(r)
    assert d.get("ok"), f"{name} 失败: {d}"
    _w(name + ".html", d["html"])
    _w(name + ".css", d["css"])
    _wj(name + ".meta.json", d["meta"])
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []

    # ── ① 对话式收集 /api/chat（真实 message：实体抽取 + 追问）──
    # 求职·后端开发·基本信息（scene_id/sub_scene_id 精确定位 stage）
    chat_log = []
    collected = {}
    for msg in ["我叫张三，想应聘后端开发，工作3年",
                "我熟悉 Java 和 Spring Cloud，主导过微服务改造"]:
        r = c.post("/api/chat", json={
            "message": msg, "stage_id": "basic",
            "scene_id": "job", "sub_scene_id": "backend",
            "collected": collected})
        d = _j(r)
        chat_log.append({"message": msg, "response": d})
        collected = dict(collected, **(d.get("filled") or {}))
    _wj("01_chat_collection.json", {"turns": chat_log,
                                    "llm": chat_log[-1]["response"].get("llm")})
    manifest.append("01_chat_collection.json")

    # ── ② 场景卡片摘要 ──
    scenes = _j(c.get("/api/scene-cards")).get("scenes", [])
    summary = {
        "scene_count": len(scenes),
        "scenes": [
            {"id": s["id"], "label": s["label"], "hint": s.get("hint", ""),
             "sub_scenes": [
                 {"id": ss["id"], "label": ss["label"],
                  "stages": [{"id": st["id"], "label": st["label"],
                              "fields": len(st.get("fields", []))}
                             for st in ss.get("stages", [])]}
                 for ss in s.get("sub_scenes", [])]}
            for s in scenes],
        "job_positions": [ss["label"] for ss in
                          next(s for s in scenes if s["id"] == "job")["sub_scenes"]],
    }
    _wj("02_scene_cards_summary.json", summary)
    manifest.append("02_scene_cards_summary.json")

    # ── ③ 四格式还原 HTML/CSS ──
    d_docx = _import("/api/import-docx", SAMPLE_DOCX, "03_import_docx")
    d_pdf = _import("/api/import-pdf", SAMPLE_PDF, "03_import_pdf")
    d_xlsx = _import("/api/import-xlsx", SAMPLE_XLSX, "03_import_xlsx")
    d_img = _import("/api/import-image", SAMPLE_IMG, "03_import_image")
    _wj("03_import_summary.json", {
        "docx": d_docx["meta"], "pdf": d_pdf["meta"],
        "xlsx": d_xlsx["meta"], "image": d_img["meta"]})
    for n in ("03_import_docx", "03_import_pdf", "03_import_xlsx", "03_import_image"):
        manifest += [n + ".html", n + ".css", n + ".meta.json"]
    manifest.append("03_import_summary.json")

    # ── ④ 简历生成 markdown / html ──
    experiences = [
        {"claim": "负责推荐算法优化", "evidence": "点击率提升 15%"},
        {"claim": "主导召回模型迭代", "evidence": "用户时长提升 8%"},
    ]
    md = _j(c.post("/api/generate", json={
        "experiences": experiences, "target_role": "算法工程师",
        "format": "markdown"})).get("resume", "")
    html = _j(c.post("/api/generate", json={
        "experiences": experiences, "target_role": "算法工程师",
        "format": "html"})).get("resume", "")
    _w("04_resume.md", md)
    _w("04_resume.html", html)
    manifest += ["04_resume.md", "04_resume.html"]

    # ── ⑤ 导出 docx / pdf ──
    r_docx = c.post("/api/export", json={
        "experiences": experiences, "target_role": "算法工程师", "format": "docx"})
    assert r_docx.status_code == 200 and "wordprocessingml" in r_docx.content_type
    _wb("05_resume.docx", r_docx.data)

    r_pdf = c.post("/api/export", json={
        "experiences": experiences, "target_role": "算法工程师",
        "format": "pdf", "template": "classic"})
    assert r_pdf.status_code == 200 and r_pdf.data[:4] == b"%PDF"
    _wb("05_resume.pdf", r_pdf.data)

    # 对话式 resume_text 导出（前端 downloadWord/downloadPDF 契约）
    resume_text = "### 基本信息\n姓名：张三；联系方式：13800138000\n### 教育背景\n院校：清华大学；专业：计算机\n### 工作经历\n字节跳动 算法实习生：负责推荐算法优化，CTR 提升 15%"
    r_docx_rt = c.post("/api/export", json={
        "experiences": [], "target_role": "算法工程师",
        "resume_text": resume_text, "format": "docx"})
    _wb("05_resume_from_chat.docx", r_docx_rt.data)
    manifest += ["05_resume.docx", "05_resume.pdf", "05_resume_from_chat.docx"]

    # ── ⑥ 多版本 / ATS / 面试 / 技能缺口 / 匹配 / 改进 ──
    versions = _j(c.post("/api/versions", json={
        "content": "主导推荐算法优化，点击率提升15%", "target": "算法工程师"}))
    _wj("06_versions.json", versions)

    ats = _j(c.post("/api/ats", json={"resume_text": (
        "姓名：张三\n电话：13800138000\n邮箱：z@x.com\n教育背景：清华大学\n"
        "工作经历：负责推荐系统，CTR 提升 15%，支撑日活 100 万")}))
    _wj("06_ats.json", ats)

    interview = _j(c.post("/api/interview", json={
        "role": "算法工程师", "company": "字节跳动",
        "profile": {"experience": [
            {"project": "推荐系统", "skills": ["深度学习", "PyTorch"],
             "context": "召回阶段效果瓶颈", "task": "优化双塔模型",
             "action": "引入多兴趣向量 + 负采样优化", "result": "CTR +15%"}],
                    "skills": ["Python", "深度学习"]},
        "jd_text": "熟悉推荐系统、深度学习、有分布式训练经验"}))
    _wj("06_interview.json", interview)

    gaps = _j(c.post("/api/skill-gaps", json={
        "jobs": [
            {"title": "算法工程师", "skills": ["Python", "PyTorch", "Kubernetes"],
             "fit_rating": 60},
            {"title": "后端工程师", "skills": ["Go", "MySQL", "Redis"],
             "fit_rating": 70, "gaps": ["Go"]}],
        "profile": {"skills": ["Python", "PyTorch"]}}))
    _wj("06_skill_gaps.json", gaps)

    match = _j(c.post("/api/match", json={
        "jd_title": "算法工程师",
        "jd_text": "熟悉 Python 深度学习 推荐系统，有分布式训练经验", "location": "北京",
        "skills": ["Python", "深度学习"],
        "experience": [{"role": "算法工程师", "summary": "推荐系统"}],
        "languages": [{"lang": "English", "level": "B2"}]}))
    _wj("06_match.json", match)

    improve = _j(c.post("/api/improve", json={
        "facts": [{"claim": "负责数据分析"}],
        "jd_title": "数据分析师", "jd_text": "熟悉 SQL Python 数据分析",
        "skills": ["Python", "SQL"]}))
    _wj("06_improve.json", improve)

    for n in ("06_versions.json", "06_ats.json", "06_interview.json",
              "06_skill_gaps.json", "06_match.json", "06_improve.json"):
        manifest.append(n)

    print("生成完成，共", len(manifest), "个产物 →", OUT)


if __name__ == "__main__":
    main()
