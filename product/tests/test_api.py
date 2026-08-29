# -*- coding: utf-8 -*-
"""W9 ⭐ 网页产品后端测试（Flask API + 前端页面）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.api import create_app, find_stage


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ── R1: 健康检查 ──
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


# ── R2: 角色包清单 ──
def test_role_packs(client):
    r = client.get("/api/role-packs")
    assert r.status_code == 200
    packs = r.get_json()["role_packs"]
    assert "tech_v1" in packs


# ── R3: 经历采集 API ──
def test_enrich_api(client):
    r = client.post("/api/enrich", json={"raw_text": "我在公司负责数据分析，提升效率20%。"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True
    assert d["facts"], "应产出事实卡"


def test_enrich_api_empty(client):
    r = client.post("/api/enrich", json={"raw_text": ""})
    assert r.status_code == 200
    assert r.get_json()["facts"] == []


# ── R4: 简历生成 API ──
def test_generate_api(client):
    r = client.post("/api/generate", json={
        "experiences": [{"claim": "负责推荐算法优化", "evidence": "提升15%"}],
        "target_role": "算法工程师", "format": "markdown"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True
    assert "推荐" in d["resume"]


def test_generate_api_html(client):
    r = client.post("/api/generate", json={
        "experiences": [{"claim": "数据分析"}], "format": "html"})
    d = r.get_json()
    assert "<html" in d["resume"].lower()


# ── R5: 前端页面 ──
def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "对话式简历制作" in r.get_data(as_text=True)


# ── R6: 对话式收集 /api/chat ──
def test_chat_missing_message(client):
    r = client.post("/api/chat", json={"stage_id": "basic"})
    assert r.status_code == 400


def test_chat_unknown_stage(client):
    r = client.post("/api/chat", json={"message": "你好", "stage_id": "nonexistent"})
    assert r.status_code == 400


def test_chat_llm_graceful(client):
    """/api/chat 正常返回（LLM 可用/不可用均 ok=True 不报错）。"""
    r = client.post("/api/chat", json={"message": "我在字节跳动实习", "stage_id": "basic"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True
    assert isinstance(d["llm"], bool)
    assert "filled" in d and "followup" in d and "summary" in d


def test_chat_valid_stage(client):
    """有效 stage（backend 的 basic）正常返回。"""
    r = client.post("/api/chat", json={"message": "我叫张三", "stage_id": "basic"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True


# ── R8: 场景卡片 ──
def test_scene_cards_structure(client):
    """4 场景 / 求职 11 岗位结构。"""
    r = client.get("/api/scene-cards")
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True
    scenes = {s["id"] for s in d["scenes"]}
    assert {"baoyan", "kaoyan", "abroad", "job"} <= scenes
    job = next(s for s in d["scenes"] if s["id"] == "job")
    assert len(job["sub_scenes"]) == 11


# ── R9: 导出（对话式 resume_text 契约，前端 downloadWord/downloadPDF 对齐）──
def test_export_uses_resume_text(client):
    """前端传 resume_text（非 experiences）→ 导出 docx 应包含对话收集内容。"""
    r = client.post("/api/export", json={
        "experiences": [], "target_role": "算法工程师",
        "resume_text": "### 基本信息\n姓名：张三\n### 教育背景\n院校：清华大学", "format": "docx"})
    assert r.status_code == 200
    assert "wordprocessingml" in r.content_type
    import io
    pytest.importorskip("docx")
    from docx import Document
    doc = Document(io.BytesIO(r.data))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "张三" in text
    assert "清华大学" in text


def test_generate_html_no_stray_markdown(client):
    """加粗标记 ** 不应泄入 HTML 输出。"""
    r = client.post("/api/generate", json={
        "experiences": [{"claim": "负责数据分析"}],
        "target_role": "数据分析师", "format": "html"})
    assert r.status_code == 200
    assert "**" not in r.get_json()["resume"]


# ── R10: 分场景 stage 精确定位（stage_id 在多场景复用，非全局唯一）──
def test_find_stage_scene_aware():
    """带 scene_id/sub_scene_id 应精确定位到对应场景的 stage。"""
    st = find_stage("basic", "job", "backend")
    assert st is not None
    keys = {f["key"] for f in st["fields"]}
    assert "target_role" in keys and "years" in keys

    st2 = find_stage("basic", "baoyan", "baoyan_clinical")
    keys2 = {f["key"] for f in st2["fields"]}
    assert "target_school" in keys2 and "target_direction" in keys2

    # 缺省场景 → 全局首匹配（向后兼容）
    st3 = find_stage("basic")
    assert st3 is not None


def test_chat_scene_aware(client):
    """chat 接受 scene_id/sub_scene_id，正常返回。"""
    r = client.post("/api/chat", json={
        "message": "我想做后端开发，Java 3年", "stage_id": "basic",
        "scene_id": "job", "sub_scene_id": "backend"})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
