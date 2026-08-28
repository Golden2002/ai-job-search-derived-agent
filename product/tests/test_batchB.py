# -*- coding: utf-8 -*-
"""批次 B 测试：interview_prep / application_tracker / skill_gap / profile_3d。"""
import json
import os
import tempfile

import pytest

from resume_product.interview_prep import prepare, simulate_interview
from resume_product.application_tracker import ApplicationTracker, generate_followup
from resume_product.skill_gap import analyze_gaps
from resume_product.profile_3d import Profile3D


# ---------- interview_prep ----------

def test_prepare_star_four_elements():
    profile = {"experience": [{"project": "P", "role": "Engineer",
                               "skills": ["python"], "summary": "built X",
                               "context": "c", "task": "t", "action": "a", "result": "r"}]}
    r = prepare("Engineer", "ACME", profile, "python role")
    s = r["star_stories"][0]
    assert s["S"] == "c" and s["T"] == "t" and s["A"] == "a" and s["R"] == "r"


def test_prepare_questions_to_ask():
    r = prepare("Engineer", "ACME", {"experience": []}, "")
    assert len(r["questions_to_ask"]) >= 3
    assert len(r["tough_questions"]) >= 4


def test_simulate_interview_structure():
    r = simulate_interview("Engineer", {"experience": []}, rounds=1)
    assert r["rounds"] == 1
    assert "opening_questions" in r and "star_pool" in r


# ---------- application_tracker ----------

def test_tracker_add_and_list():
    with tempfile.TemporaryDirectory() as d:
        t = ApplicationTracker(os.path.join(d, "app.json"))
        e = t.add("ACME", "Engineer", source="url")
        assert e["status"] == "applied"
        assert len(t.list()) == 1
        assert len(t.list("applied")) == 1


def test_tracker_status_machine():
    with tempfile.TemporaryDirectory() as d:
        t = ApplicationTracker(os.path.join(d, "app.json"))
        e = t.add("ACME", "Engineer")
        t.update_status(e["id"], "interview")
        assert t.get(e["id"])["status"] == "interview"


def test_tracker_invalid_status():
    with tempfile.TemporaryDirectory() as d:
        t = ApplicationTracker(os.path.join(d, "app.json"))
        e = t.add("ACME", "Engineer")
        with pytest.raises(ValueError):
            t.update_status(e["id"], "bogus")


def test_followup_tiers():
    entry = {"company": "ACME", "role": "Engineer", "contact": "HR"}
    f7 = generate_followup(entry, 7)
    f14 = generate_followup(entry, 14)
    f21 = generate_followup(entry, 21)
    assert "ACME" in f7
    assert f7 != f14 != f21  # 三档内容不同


# ---------- skill_gap ----------

def test_skill_gap_heatmap_weight():
    jobs = [{"title": "A", "fit_rating": 0, "skills": ["python"]},
            {"title": "B", "fit_rating": 60, "skills": ["python"]}]
    profile = {"skills": ["java"]}
    r = analyze_gaps(jobs, profile)
    assert "python" in r["heatmap"]
    # 权重 = (100-0)/100 + (100-60)/100 = 1.0 + 0.4 = 1.4
    assert abs(r["heatmap"]["python"]["weight"] - 1.4) < 0.001


def test_skill_gap_recorded_beats_inferred():
    jobs = [{"title": "A", "fit_rating": 50, "skills": ["x"], "gaps": ["y"]}]
    profile = {"skills": []}
    r = analyze_gaps(jobs, profile)
    assert "y" in r["heatmap"]
    assert "recorded" in r["heatmap"]["y"]["provenance"]


def test_skill_gap_blank_fit_skipped():
    jobs = [{"title": "A", "fit_rating": None, "skills": ["python"]}]
    profile = {"skills": []}
    r = analyze_gaps(jobs, profile)
    assert r["skipped_blank_fit"] == 1


# ---------- profile_3d ----------

def test_profile_validate_ok():
    p = Profile3D({"name": "A", "skills": ["python"], "experience": []},
                  {}, {"forbidden": ["em-dash"]})
    assert p.validate() == []


def test_profile_validate_missing_skills():
    p = Profile3D({"name": "A", "experience": []}, {}, {})
    errs = p.validate()
    assert any("skills" in e for e in errs)


def test_profile_json_roundtrip():
    p = Profile3D({"name": "A", "skills": ["python"], "experience": []}, {}, {})
    d = json.loads(p.to_json())
    assert d["candidate"]["name"] == "A"
    p2 = Profile3D.from_dict(d)
    assert p2.candidate == p.candidate
