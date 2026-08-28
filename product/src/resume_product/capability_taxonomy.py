# -*- coding: utf-8 -*-
"""resume_product.capability_taxonomy —— 能力分类体系。

基线对齐：medical-resume-agent capability-taxonomy.md。
结构化能力维度划分，用于经历标签化与职位匹配。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "..", "data"))


def load_taxonomy(path: Optional[str] = None) -> Dict[str, Any]:
    """加载能力分类体系（默认 data/capability_tags/general_v1.json）。"""
    p = path or os.path.join(_DATA_DIR, "capability_tags", "general_v1.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def tag_experience(experience: Dict[str, Any],
                   taxonomy: Optional[Dict[str, Any]] = None) -> List[str]:
    """经历标签化：根据能力分类体系为经历打标签。"""
    tax = taxonomy or load_taxonomy()
    tags = []
    text = " ".join([
        str(experience.get("role", "")),
        str(experience.get("summary", "") or experience.get("description", "")),
        " ".join(experience.get("skills", []) or []),
    ]).lower()

    # taxonomy 结构：{dimension: {tag: [keywords]}}
    for dimension, tags_map in tax.items():
        if not isinstance(tags_map, dict):
            continue
        for tag, keywords in tags_map.items():
            kws = keywords if isinstance(keywords, list) else [keywords]
            if any(k.lower() in text for k in kws):
                tags.append(f"{dimension}:{tag}")
    return tags
