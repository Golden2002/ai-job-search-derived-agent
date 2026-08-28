# -*- coding: utf-8 -*-
"""resume_product.job_evaluation —— 职位匹配度五维度评估评分。

基线对齐：ai-job-search-derived-agent 的 04-job-evaluation.md（Eligibility Gate +
Language Gate + 五维评分框架），通用化后作为 PAEG 简历工具的核心匹配引擎。

五维度（各 0-100）：
1. technical —— 技术技能匹配
2. experience —— 经验匹配（按职能而非职位头衔）
3. behavioral —— 行为/文化匹配
4. location —— 地点与物流（PASS/FAIL/FLAG + 说明）
5. alignment —— 职业对齐与动机
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _norm(s: str) -> str:
    """归一化关键词（大小写 + 去空白）。"""
    return " ".join(str(s).strip().lower().split())


def _tokenize(text: str) -> List[str]:
    """§3.116 ⭐ R-R3 中英文分词：英文按空白/标点，中文用 jieba（缺失时字符 bigram 兜底）。

    修复审查发现"CJK 相关性评分失效"（.split() 对中文无空格 → 整段成一个 token）。
    """
    tokens: List[str] = []
    for part in re.split(r'[\s,，。.;；:：!?！？、()（）\[\]【】]+', str(text).lower()):
        if not part:
            continue
        if re.search(r'[\u4e00-\u9fff]', part):
            try:
                import jieba
                tokens.extend(w for w in jieba.cut(part) if w.strip())
            except Exception:
                # 无 jieba 时字符 bigram 兜底（中文 2 字组合）
                _bg = [part[i:i + 2] for i in range(len(part) - 1)]
                tokens.extend(_bg or [part])
        else:
            tokens.append(part)
    return tokens


def _contains_any(text: str, keywords: List[str]) -> bool:
    t = _norm(text)
    return any(_norm(k) in t for k in keywords)


class EligibilityGate:
    """资格门——评分前硬过滤（公民/永久居留/安全许可）。"""

    # 硬性公民/永居要求措辞
    _CITIZENSHIP_HARD = [
        "citizen of", "permanent resident", "pr required", "must be a citizen",
        "be a citizen", "citizenship required", "full working rights",
        "security clearance", "right to work",
    ]
    # 明确欢迎国际申请者措辞
    _WELCOME = [
        "international applicants welcome", "visa holders considered",
        "we sponsor", "visa sponsorship", "work permit", "open to international",
        "international candidates", "sponsorship available",
    ]

    @classmethod
    def evaluate(cls, posting_text: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = posting_text or ""
        for kw in cls._CITIZENSHIP_HARD:
            if kw in _norm(text):
                # 找到原文出处
                quote = cls._find_quote(text, kw)
                return {
                    "verdict": "FAIL",
                    "reason": "citizenship_or_residency_requirement",
                    "quote": quote,
                    "note": "职位要求公民/永久居留/安全许可，属于硬性排除条件，停止评分与起草。",
                }
        for kw in cls._WELCOME:
            if kw in _norm(text):
                return {
                    "verdict": "PASS",
                    "reason": "international_welcome",
                    "quote": cls._find_quote(text, kw),
                    "note": "职位明确接受国际申请者/提供签证担保。",
                }
        return {
            "verdict": "PROCEED_UNVERIFIED",
            "reason": "silent",
            "quote": "",
            "note": "职位未明确公民/居留要求，标记为未核实，起草前应查雇主官网确认。",
        }

    @staticmethod
    def _find_quote(text: str, kw: str) -> str:
        t = _norm(text)
        idx = t.find(_norm(kw))
        if idx < 0:
            return ""
        # 取原文片段（按空格还原粗粒度）
        start = max(0, idx - 40)
        end = min(len(t), idx + len(kw) + 60)
        return t[start:end]


class LanguageGate:
    """语言门——评分前校验职位语言要求 vs 候选人语言表。"""

    @classmethod
    def evaluate(cls, posting_text: str, languages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """languages: [{lang: "English", level: "B1"}, ...]（level 可为 CEFR 或自然语言）。"""
        declared = {_norm(item.get("lang", "")): _norm(item.get("level", "")) for item in languages}
        text = posting_text or ""

        # 识别职位语言要求（含 "fluent/native/C1/business-level/required" 等）
        required = cls._extract_requirements(text)
        if not required:
            return {"verdict": "PASS", "note": "职位未声明特定工作语言要求。", "required": []}

        results = []
        for lang, bar in required:
            if lang not in declared:
                results.append({"lang": lang, "verdict": "FAIL", "bar": bar,
                                "note": f"职位要求 {lang}，但候选人语言表未声明。"})
            else:
                # 简化级别比较：bar 有 "fluent/native/c1/c2/business" 且候选人级别低则 FLAG
                if cls._bar_exceeds(bar, declared[lang]):
                    results.append({"lang": lang, "verdict": "FLAG", "bar": bar,
                                    "note": f"职位要求 {lang}（{bar}），候选人声明 {declared[lang]}，可能偏低。"})
                else:
                    results.append({"lang": lang, "verdict": "PASS", "bar": bar, "note": ""})

        if any(r["verdict"] == "FAIL" for r in results):
            verdict = "FAIL"
        elif any(r["verdict"] == "FLAG" for r in results):
            verdict = "FLAG"
        else:
            verdict = "PASS"
        return {"verdict": verdict, "required": results}

    # 已知语言词表（用于精确匹配语言名，避免正则贪多）
    _KNOWN_LANGS = [
        "english", "chinese", "mandarin", "cantonese", "polish", "french", "german",
        "spanish", "italian", "portuguese", "russian", "japanese", "korean", "arabic",
        "danish", "swedish", "norwegian", "dutch", "finnish", "hindi", "turkish",
    ]

    @classmethod
    def _extract_requirements(cls, text: str) -> List[tuple]:
        import re
        t = text.lower()
        out = []
        # 只对已知语言词表匹配 "fluent/native/business X" 或 "X required"
        for lang in cls._KNOWN_LANGS:
            for m in re.finditer(
                r"(?:fluent|native|business[- ]level|professional|conversational|working "
                r"proficiency[^\w]?\w*)\s+(?:in\s+|with\s+)?%s" % lang, t):
                bar = m.group(0).split(lang)[0].strip()
                out.append((lang, bar))
            for m in re.finditer(r"%s\s+required" % lang, t):
                out.append((lang, "required"))
        return out

    @staticmethod
    def _bar_exceeds(bar: str, declared: str) -> bool:
        high = ["fluent", "native", "c1", "c2", "business-level", "business level", "professional"]
        low = ["a1", "a2", "b1", "b2", "conversational", "basic", "beginner"]
        b = _norm(bar)
        d = _norm(declared)
        if any(h in b for h in high) and any(l in d for l in low):
            return True
        return False


def evaluate_fit(posting: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """五维度评分主入口。

    posting: {title, company, description, location, ...}
    profile: {skills: [...], experience: [...], behavioral: {...}, languages: [...], career_goals: [...]}
    """
    text = posting.get("description", "") or ""
    title = posting.get("title", "") or ""

    # 资格门 + 语言门
    eligibility = EligibilityGate.evaluate(text, profile)
    if eligibility["verdict"] == "FAIL":
        return {"scored": False, "eligibility": eligibility, "reason": "eligibility_fail"}
    language = LanguageGate.evaluate(text, profile.get("languages", []))
    if language["verdict"] == "FAIL":
        return {"scored": False, "eligibility": eligibility, "language": language, "reason": "language_fail"}

    skills = [_norm(s) for s in profile.get("skills", [])]
    joined_text = _norm(title + " " + text)

    # 1. 技术技能匹配
    technical = _score_skills(joined_text, skills)

    # 2. 经验匹配（按职能关键词，而非职位头衔）
    experience = _score_experience(joined_text, profile.get("experience", []))

    # 3. 行为/文化匹配
    behavioral = _score_behavioral(profile.get("behavioral", {}))

    # 4. 地点与物流
    location = _score_location(posting.get("location", ""), profile.get("location", ""))

    # 5. 职业对齐
    alignment = _score_alignment(joined_text, profile.get("career_goals", []))

    scores = {
        "technical": technical,
        "experience": experience,
        "behavioral": behavioral,
        "location": location,
        "alignment": alignment,
    }

    # total 加权：technical 30% + experience 30% + behavioral 15% + alignment 25%（location 为定性）
    numeric = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
    total = round(
        0.30 * numeric.get("technical", 0)
        + 0.30 * numeric.get("experience", 0)
        + 0.15 * numeric.get("behavioral", 0)
        + 0.25 * numeric.get("alignment", 0),
        1,
    )

    verdict = _verdict_from_total(total)
    gaps = _detect_gaps(joined_text, skills)

    return {
        "scored": True,
        "eligibility": eligibility,
        "language": language,
        "scores": scores,
        "total": total,
        "verdict": verdict,
        "gaps": gaps,
    }


def _score_skills(posting_text: str, skills: List[str]) -> int:
    if not skills:
        return 20
    # §3.116 ⭐ R-R3：分词后 token 子集匹配（中文技能词也能命中）
    posting_tokens = set(_tokenize(posting_text))
    matched = 0
    for s in skills:
        s_tokens = set(_tokenize(s))
        if s in posting_text or (s_tokens and s_tokens.issubset(posting_tokens)):
            matched += 1
    ratio = matched / len(skills)
    if ratio >= 0.8:
        return 80 + int(20 * ratio)
    if ratio >= 0.5:
        return 60 + int(20 * ratio)
    if ratio >= 0.3:
        return 40 + int(20 * ratio)
    return max(10, int(40 * ratio))


def _score_experience(posting_text: str, experience: List[Dict[str, Any]]) -> int:
    if not experience:
        return 15
    # 从经历中提取职能关键词（role + summary）
    func_keywords = []
    for exp in experience:
        func_keywords.append(_norm(exp.get("role", "")))
        func_keywords.append(_norm(exp.get("summary", "") or exp.get("description", "")))
    all_func = " ".join(func_keywords)
    # §3.116 ⭐ R-R3：中文分词后 set 交集（.split() 对中文无效）
    overlap = len(set(_tokenize(posting_text)) & set(_tokenize(all_func)))
    base = min(60, overlap)
    return 50 + base if experience and overlap > 3 else 35


def _score_behavioral(behavioral: Dict[str, Any]) -> int:
    # 无行为画像时给中性分
    if not behavioral:
        return 50
    return 70


def _score_location(posting_loc: str, profile_loc: str) -> Dict[str, Any]:
    pl = _norm(posting_loc)
    pf = _norm(profile_loc)
    if "remote" in pl:
        return {"verdict": "PASS", "note": "远程职位，无地点限制。", "score": 90}
    if not pl:
        return {"verdict": "FLAG", "note": "职位未标注地点。", "score": 60}
    if pf and pf in pl:
        return {"verdict": "PASS", "note": "地点匹配。", "score": 90}
    return {"verdict": "FLAG", "note": "地点可能需搬迁/通勤，需与用户确认。", "score": 40}


def _score_alignment(posting_text: str, career_goals: List[str]) -> int:
    if not career_goals:
        return 50
    matched = [g for g in career_goals if _norm(g) in posting_text]
    ratio = len(matched) / len(career_goals)
    return 50 + int(40 * min(1.0, ratio))


def _verdict_from_total(total: float) -> str:
    if total >= 75:
        return "Strong Fit"
    if total >= 55:
        return "Moderate Fit"
    if total >= 40:
        return "Weak Fit"
    return "Poor Fit"


def _detect_gaps(posting_text: str, skills: List[str]) -> List[str]:
    # 从职位描述中识别未被候选人技能覆盖的常见技能关键词
    common_skills = [
        "python", "java", "javascript", "sql", "machine learning", "deep learning",
        "data analysis", "project management", "communication", "leadership",
        "excel", "tableau", "docker", "kubernetes", "aws", "react", "node",
        "统计", "数据分析", "机器学习", "项目管理", "沟通", "领导力",
    ]
    gaps = [s for s in common_skills if s in posting_text and s not in skills]
    return gaps[:10]
