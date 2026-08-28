# -*- coding: utf-8 -*-
"""resume_product.job_portal —— 职位门户可扩展架构。

基线对齐：.agents/skills/ 6 门户 scraper 的「统一 Posting 契约 + 适配器注册」精神。
真实门户（LinkedIn/前程无忧/BOSS 直聘等）按 JobPortalAdapter 同接口扩展。
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Posting:
    title: str
    company: str
    source: str
    url: str = ""
    description: str = ""
    deadline: Optional[str] = None  # 缺省 None，绝不猜值
    location: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JobPortalAdapter(ABC):
    """职位门户适配器抽象基类——真实门户按此接口实现。"""

    name: str = "abstract"

    @abstractmethod
    def search(self, query: str, **kwargs) -> List[Posting]:
        """按关键词检索职位。"""

    @abstractmethod
    def detail(self, url: str) -> Optional[Posting]:
        """获取单个职位详情（未命中返回 None）。"""


class JSONFilePortal(JobPortalAdapter):
    """JSON 文件职位源适配器（示例 + 测试用）。"""

    name = "json_file"

    def __init__(self, path: str):
        self.path = path
        self._postings: List[Posting] = self._load()

    def _load(self) -> List[Posting]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return [Posting(**{k: p.get(k) for k in Posting.__dataclass_fields__})
                for p in (data if isinstance(data, list) else [])]

    def search(self, query: str, **kwargs) -> List[Posting]:
        q = query.lower()
        return [p for p in self._postings
                if q in (p.title + " " + p.description + " " + p.company).lower()]

    def detail(self, url: str) -> Optional[Posting]:
        for p in self._postings:
            if p.url == url:
                return p
        return None


class PortalRegistry:
    def __init__(self):
        self._portals: Dict[str, JobPortalAdapter] = {}

    def register(self, adapter: JobPortalAdapter) -> None:
        if adapter.name in self._portals:
            raise ValueError(f"门户已注册：{adapter.name}")
        self._portals[adapter.name] = adapter

    def get(self, name: str) -> JobPortalAdapter:
        if name not in self._portals:
            raise KeyError(f"未注册门户：{name}")
        return self._portals[name]

    def list(self) -> List[str]:
        return list(self._portals.keys())


def portal_search(registry: PortalRegistry, portal_name: str, query: str) -> List[Dict[str, Any]]:
    return [p.to_dict() for p in registry.get(portal_name).search(query)]


def portal_detail(registry: PortalRegistry, portal_name: str, url: str) -> Optional[Dict[str, Any]]:
    p = registry.get(portal_name).detail(url)
    return p.to_dict() if p else None
