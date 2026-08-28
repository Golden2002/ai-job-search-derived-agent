# -*- coding: utf-8 -*-
"""resume_product.application_tracker —— 申请结果跟踪 + 跟进信生成。

基线对齐：.claude/commands/apply.md + outcome.md（申请状态机 + 跟进信）。
本地 JSON 存储，数据安全（本机运行）。
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

_VALID_STATUS = ["applied", "interview", "offer", "rejected", "withdrawn"]


class ApplicationTracker:
    """本地 JSON 申请跟踪器。"""

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
            "data", "applications.json")
        self._entries: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=2)

    def add(self, company: str, role: str, source: str = "",
            deadline: Optional[str] = None, contact: str = "", notes: str = "") -> Dict[str, Any]:
        entry = {
            "id": len(self._entries) + 1,
            "company": company,
            "role": role,
            "source": source,
            "deadline": deadline,
            "contact": contact,
            "notes": notes,
            "status": "applied",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "events": [{"status": "applied", "at": datetime.now().isoformat(timespec="seconds")}],
        }
        self._entries.append(entry)
        self._save()
        return entry

    def update_status(self, entry_id: int, new_status: str) -> Dict[str, Any]:
        if new_status not in _VALID_STATUS:
            raise ValueError(f"非法状态 {new_status}，合法状态：{_VALID_STATUS}")
        for e in self._entries:
            if e["id"] == entry_id:
                e["status"] = new_status
                e["updated_at"] = datetime.now().isoformat(timespec="seconds")
                e["events"].append({"status": new_status,
                                    "at": datetime.now().isoformat(timespec="seconds")})
                self._save()
                return e
        raise KeyError(f"未找到申请 ID {entry_id}")

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status is None:
            return list(self._entries)
        return [e for e in self._entries if e["status"] == status]

    def get(self, entry_id: int) -> Dict[str, Any]:
        for e in self._entries:
            if e["id"] == entry_id:
                return e
        raise KeyError(f"未找到申请 ID {entry_id}")


def generate_followup(entry: Dict[str, Any], days_since: int) -> str:
    """按距申请天数分档生成跟进信。"""
    company = entry.get("company", "")
    role = entry.get("role", "")
    contact = entry.get("contact", "") or "招聘团队"

    if days_since <= 7:
        tone = "礼貌确认"
        body = (f"我想跟进一下我 {days_since} 天前提交的 {role} 职位申请，"
                f"确认材料是否已完整收到，并表达对该机会的持续热情。")
    elif days_since <= 14:
        tone = "适度重申"
        body = (f"我于约两周前申请了 {role} 职位。我仍非常期待加入 {company}，"
                f"如需要我补充任何材料或安排面试，我随时配合。")
    else:
        tone = "最后跟进"
        body = (f"我于 {days_since} 天前申请了 {role} 职位，至今未收到回复。"
                f"我对该机会依然重视，如已进入其他候选阶段，也恳请告知以作安排。")

    return f"致 {company} {contact}：\n\n{body}\n\n此致\n敬礼"
