# -*- coding: utf-8 -*-
"""批次 D 测试：claim_gate / multi_version / canonical_experience / capability_taxonomy。"""
import pytest

from resume_product.claim_gate import ClaimGate, ConfirmationGate
from resume_product.multi_version import generate_versions
from resume_product.schemas.canonical_experience import (
    CANONICAL_EXPERIENCE_SCHEMA, validate_canonical, decompose,
)
from resume_product.capability_taxonomy import tag_experience


# ---------- claim_gate ----------

def test_claim_verified():
    claims = [{"text": "开发了 X 系统", "evidence_key": "e1"}]
    evidence = {"e1": {"strength": "strong"}}
    r = ClaimGate.review(claims, evidence)
    assert r["passed"][0]["verdict"] == "verified"
    assert r["summary"]["verified"] == 1


def test_claim_unverified_no_evidence():
    claims = [{"text": "独立完成项目", "evidence_key": ""}]
    r = ClaimGate.review(claims, {})
    assert r["needs_confirmation"][0]["verdict"] == "unverified"


def test_claim_exaggerated():
    claims = [{"text": "主导了核心系统", "evidence_key": "e1"}]
    evidence = {"e1": {"strength": "weak"}}
    r = ClaimGate.review(claims, evidence)
    assert r["failed"][0]["verdict"] == "exaggerated"


def test_confirmation_gate_questions():
    claims = [{"text": "独立完成 X"}]
    qs = ConfirmationGate.ask(claims)
    assert "独立完成 X" in qs[0]["question"]


# ---------- multi_version ----------

def test_multi_version_three_versions():
    r = generate_versions("主导了系统开发", "数据工程师")
    assert set(r.keys()) == {"safe", "professional", "competitive"}
    assert r["safe"] != r["competitive"]


def test_multi_version_safe_weakens_strong_terms():
    r = generate_versions("独立完成核心模块", "工程师")
    assert "独立完成" not in r["safe"]


def test_multi_version_competitive_mentions_quantify():
    r = generate_versions("开发系统", "工程师")
    assert "量化" in r["competitive"] or "成果" in r["competitive"]


# ---------- canonical_experience ----------

def test_canonical_schema_requires_six_fields():
    assert "research_subject" in CANONICAL_EXPERIENCE_SCHEMA["required"]
    assert "transferable_skill" in CANONICAL_EXPERIENCE_SCHEMA["required"]


def test_validate_missing_fields():
    errs = validate_canonical({"research_subject": "x"})
    assert len(errs) >= 5


def test_validate_ok():
    d = {"research_subject": "x", "method": "m", "tools": ["t"], "role": "r",
         "deliverable": "d", "transferable_skill": "s"}
    assert validate_canonical(d) == []


def test_decompose_fallback_six_fields():
    r = decompose("研究了某系统", "数据方向")
    for f in ["research_subject", "method", "tools", "role", "deliverable",
              "transferable_skill"]:
        assert f in r


# ---------- capability_taxonomy ----------

def test_tag_experience():
    taxonomy = {"技术": {"数据分析": ["python", "sql"]},
                "协作": {"沟通": ["present", "汇报"]}}
    exp = {"role": "Analyst", "skills": ["python"], "summary": "present results"}
    tags = tag_experience(exp, taxonomy)
    assert "技术:数据分析" in tags
    assert "协作:沟通" in tags
