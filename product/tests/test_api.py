# -*- coding: utf-8 -*-
"""W9 ⭐ 网页产品后端测试（Flask API + 前端页面）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from resume_product.api import create_app


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
