# -*- coding: utf-8 -*-
"""LLM + 语言规范接入测试：口语规范化 / 降级 / 病句修正。"""
import pytest

from resume_product.core import ResumeEngine


# ---------- S3: 语言规范病句修正 ----------

def test_lang_style_fixes_gaffe():
    from resume_product.core import _lang_fix
    fixed = _lang_fix("我在这里听着你。")
    assert "听你说说" in fixed


def test_lang_style_import_flag():
    from resume_product.core import _HAS_LANG_STYLE
    assert _HAS_LANG_STYLE is True


# ---------- S1: LLM 接入后口语规范化 ----------

def test_enrich_llm_normalizes_colloquial():
    def fake_chat(sys_p, usr_p):
        return '[{"claim": "参与北京市集成电路设计大赛模拟组，获二等奖", "evidence": "比赛二等奖", "quote": "比赛...二等奖"}, {"claim": "参与一生一芯项目并通过入学答辩", "evidence": "通过入学答辩", "quote": "入学答辩过了"}]'
    eng = ResumeEngine(chat_fn=fake_chat)
    facts = eng.enrich("当时就是当 spice monkey，瞎调参数，最后竟然也有个二等奖")
    assert len(facts) >= 2
    joined = " ".join(f.get("claim", "") for f in facts)
    # 口语词不应出现在规范化后的 claim
    assert "瞎调" not in joined
    assert "spice monkey" not in joined


def test_enrich_llm_no_llm_fallback():
    """无 LLM（空返回）→ 降级 heuristic，不崩。"""
    def no_chat(sys_p, usr_p):
        return ""
    eng = ResumeEngine(chat_fn=no_chat)
    facts = eng.enrich("我在字节实习，优化推荐算法，CTR 提升 15%。")
    assert len(facts) >= 1


# ---------- S2: 空输入边界 ----------

def test_enrich_empty_input():
    eng = ResumeEngine()
    assert eng.enrich("") == []
    assert eng.enrich("   ") == []


# ---------- RED 驱动：提示词须要求口语规范化 ----------

def test_enrich_prompt_requires_normalization():
    captured = {}
    def fake_chat(sys_p, usr_p):
        captured["sys"] = sys_p
        return '[{"claim": "规范化后的主张", "evidence": "x", "quote": "x"}]'
    eng = ResumeEngine(chat_fn=fake_chat)
    eng.enrich("当时就是当 spice monkey，瞎调参数")
    assert "规范化" in captured["sys"]
    assert "口语" in captured["sys"]


# ---------- RED 驱动：compose 应用语言规范 ----------

def test_compose_applies_lang_fix():
    eng = ResumeEngine(chat_fn=lambda s, u: "")
    out = eng.compose([{"claim": "我在这里听着你。", "evidence": ""}], "测试岗位")
    assert "听你说说" in out


# ---------- RED 驱动：默认引擎必须真正走 LLM（而非短路到 heuristic） ----------

def test_default_engine_uses_llm(monkeypatch):
    import resume_product.core as core_mod

    def fake_llm(sys_p, usr_p):
        return '[{"claim": "规范化主张", "evidence": "e", "quote": "q"}]'

    monkeypatch.setattr(core_mod.llm_client, "chat", fake_llm)
    eng = core_mod.ResumeEngine()  # 默认 chat_fn = _default_chat
    facts = eng.enrich("原始口语文本")
    assert facts[0]["claim"] == "规范化主张"  # 走了 LLM 路径而非 heuristic
