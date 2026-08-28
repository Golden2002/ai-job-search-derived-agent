# -*- coding: utf-8 -*-
"""批次 E 测试：job_portal 职位门户架构。"""
import json
import os
import tempfile

import pytest

from resume_product.job_portal import (
    Posting, JSONFilePortal, PortalRegistry, portal_search, portal_detail,
)


def _make_postings(path):
    data = [
        {"title": "Python Engineer", "company": "ACME", "source": "json",
         "url": "https://x/1", "description": "python backend", "deadline": None,
         "location": "Shanghai"},
        {"title": "Data Analyst", "company": "Beta", "source": "json",
         "url": "https://x/2", "description": "sql analysis", "deadline": "2026-12-01",
         "location": "Beijing"},
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def test_posting_deadline_none_not_guessed():
    p = Posting(title="x", company="y", source="z")
    assert p.deadline is None
    d = p.to_dict()
    assert d["deadline"] is None


def test_json_portal_search():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "jobs.json")
        _make_postings(p)
        portal = JSONFilePortal(p)
        results = portal.search("python")
        assert len(results) == 1
        assert results[0].title == "Python Engineer"


def test_json_portal_detail_hit_and_miss():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "jobs.json")
        _make_postings(p)
        portal = JSONFilePortal(p)
        assert portal.detail("https://x/1").company == "ACME"
        assert portal.detail("https://x/nope") is None


def test_registry_register_and_get():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "jobs.json")
        _make_postings(p)
        reg = PortalRegistry()
        reg.register(JSONFilePortal(p))
        assert "json_file" in reg.list()
        assert isinstance(reg.get("json_file"), JSONFilePortal)


def test_registry_duplicate_rejected():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "jobs.json")
        _make_postings(p)
        reg = PortalRegistry()
        reg.register(JSONFilePortal(p))
        with pytest.raises(ValueError):
            reg.register(JSONFilePortal(p))


def test_registry_unknown_name():
    reg = PortalRegistry()
    with pytest.raises(KeyError):
        reg.get("nope")


def test_portal_search_helper():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "jobs.json")
        _make_postings(p)
        reg = PortalRegistry()
        reg.register(JSONFilePortal(p))
        r = portal_search(reg, "json_file", "data")
        assert len(r) == 1
        assert r[0]["title"] == "Data Analyst"
