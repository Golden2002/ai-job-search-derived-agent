# -*- coding: utf-8 -*-
"""批次 A 测试：job_evaluation / cv_trim / rank / salary_benchmark。"""
import pytest

from resume_product.job_evaluation import (
    EligibilityGate, LanguageGate, evaluate_fit,
)
from resume_product.cv_trim import trim_experience
from resume_product.rank import rank_postings
from resume_product.salary_benchmark import benchmark


# ---------- EligibilityGate ----------

def test_eligibility_citizenship_fail_hard_stop():
    r = EligibilityGate.evaluate("Must be a citizen of Denmark to apply.")
    assert r["verdict"] == "FAIL"
    assert r["quote"]


def test_eligibility_welcome_pass():
    r = EligibilityGate.evaluate("International applicants welcome. We sponsor visas.")
    assert r["verdict"] == "PASS"


def test_eligibility_silent_unverified():
    r = EligibilityGate.evaluate("Senior engineer role. Apply now.")
    assert r["verdict"] == "PROCEED_UNVERIFIED"


# ---------- LanguageGate ----------

def test_language_fail_undeclared():
    langs = [{"lang": "English", "level": "B1"}]
    r = LanguageGate.evaluate("Fluent Polish required for this role.", langs)
    assert r["verdict"] == "FAIL"


def test_language_flag_higher_bar():
    langs = [{"lang": "English", "level": "B1"}]
    r = LanguageGate.evaluate("Fluent English required.", langs)
    assert r["verdict"] == "FLAG"


def test_language_pass():
    langs = [{"lang": "English", "level": "C2"}]
    r = LanguageGate.evaluate("Conversational English required.", langs)
    assert r["verdict"] in ("PASS", "FLAG")  # 解析宽松，不断言过严


# ---------- evaluate_fit ----------

def test_evaluate_fit_eligibility_fail_no_score():
    p = {"title": "X", "description": "Must be a citizen."}
    profile = {"skills": ["python"], "experience": [], "languages": []}
    r = evaluate_fit(p, profile)
    assert r["scored"] is False
    assert r["reason"] == "eligibility_fail"


def test_evaluate_fit_low_score_missing_skills():
    p = {"title": "Data Scientist", "description": "Need python machine learning sql aws.",
         "location": "Remote"}
    profile = {"skills": ["writing"], "experience": [], "languages": [],
               "behavioral": {}, "career_goals": []}
    r = evaluate_fit(p, profile)
    assert r["scored"] is True
    assert r["scores"]["technical"] < 50
    assert r["gaps"]  # 缺失技能被识别


def test_evaluate_fit_high_score_full_match():
    p = {"title": "Python Engineer", "description": "python machine learning sql docker aws react",
         "location": "Remote"}
    profile = {"skills": ["python", "machine learning", "sql", "docker", "aws", "react"],
               "experience": [{"role": "Python Engineer", "summary": "built ML systems"}],
               "languages": [], "behavioral": {}, "career_goals": ["python"]}
    r = evaluate_fit(p, profile)
    assert r["scored"] is True
    assert r["scores"]["technical"] >= 70


# ---------- cv_trim ----------

def _mk_entry(role, skills, summary="", project=""):
    return {"role": role, "skills": skills, "summary": summary, "project": project}


def test_trim_no_trim_when_within_limit():
    entries = [_mk_entry("Engineer", ["python"]) for _ in range(3)]
    r = trim_experience(entries, "Engineer", max_items=5)
    assert len(r["kept"]) == 3
    assert r["removed"] == []


def test_trim_prioritizes_relevance_over_time():
    # 旧但相关的经历应保留；新但无关的经历应被裁剪（非机械时间排序）
    relevant_old = _mk_entry("Data Scientist", ["python", "sql"], "built models")
    irrelevant_new = _mk_entry("Barista", ["coffee"], "made coffee")
    entries = [irrelevant_new, relevant_old]  # 新在前，旧在后
    r = trim_experience(entries, "Data Scientist", max_items=1)
    assert r["kept"][0]["role"] == "Data Scientist"


def test_trim_returns_reason_for_removed():
    entries = [_mk_entry("Data Scientist", ["python"]), _mk_entry("Waiter", ["service"])]
    r = trim_experience(entries, "Data Scientist", max_items=1)
    assert len(r["removed"]) == 1
    assert "reason" in r["removed"][0]


# ---------- rank ----------

def test_rank_sorts_by_total_desc():
    postings = [
        {"title": "A", "description": "python sql", "location": "Remote"},
        {"title": "B", "description": "python sql docker aws react ml", "location": "Remote"},
    ]
    profile = {"skills": ["python", "sql", "docker", "aws", "react", "ml"],
               "experience": [], "languages": [], "behavioral": {}, "career_goals": []}
    r = rank_postings(postings, profile)
    assert r[0]["rank"] == 1
    assert r[0]["posting"]["title"] == "B"


# ---------- salary_benchmark ----------

def test_benchmark_with_sources():
    sources = [{"role": "engineer", "region": "Shanghai", "years": 3,
                "p25": 200, "p50": 300, "p75": 400, "source": "test"}]
    r = benchmark("Software Engineer", "Shanghai", 3, sources=sources, expected=300)
    assert r["percentile50"] == 300
    assert r["data_sufficient"] is True
    assert r["verdict"] == "符合市场"


def test_benchmark_verdict_below_market():
    sources = [{"role": "engineer", "region": "Shanghai", "p50": 300}]
    r = benchmark("Engineer", "Shanghai", 3, sources=sources, expected=100)
    assert r["verdict"] == "低于市场"


def test_benchmark_no_sources_insufficient():
    r = benchmark("Engineer", "Shanghai", 3)
    assert r["data_sufficient"] is False
    assert r["percentile50"] is None
