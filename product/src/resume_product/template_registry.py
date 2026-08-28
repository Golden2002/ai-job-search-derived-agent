# -*- coding: utf-8 -*-
"""resume_product.template_registry —— 多模板注册/切换/导入。

基线对齐：05-cv-templates.md（多模板支持）。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

_VALID_FORMATS = {"tex", "html", "md"}

# 仓库根资产路径：resume_product/ -> src/ -> product/ -> ai-job-search-derived-agent/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "..", "..", ".."))


class TemplateRegistry:
    def __init__(self):
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._current: Optional[str] = None
        self._register_builtins()

    def _register_builtins(self):
        self.register("moderncv_banking", "moderncv banking 风格 LaTeX 简历",
                      "tex", os.path.join(_REPO_ROOT, "cv", "main_example.tex"))
        self.register("resume_html", "现有 HTML 简历模板", "html", None)
        self.register("generic_md", "通用 Markdown 简历", "md", None)

    def register(self, template_id: str, name: str, fmt: str,
                 path: Optional[str] = None) -> Dict[str, Any]:
        if template_id in self._templates:
            raise ValueError(f"模板 ID 已存在：{template_id}")
        if fmt not in _VALID_FORMATS:
            raise ValueError(f"非法格式 {fmt}，合法格式：{sorted(_VALID_FORMATS)}")
        if path is not None and not os.path.exists(path):
            raise ValueError(f"模板文件不存在：{path}")
        self._templates[template_id] = {"id": template_id, "name": name,
                                        "format": fmt, "path": path}
        return self._templates[template_id]

    def import_template(self, template_id: str, name: str, fmt: str, path: str) -> Dict[str, Any]:
        """导入自定义模板：校验文件存在 + 格式合法。"""
        if not os.path.exists(path):
            raise ValueError(f"导入失败：文件不存在 {path}")
        return self.register(template_id, name, fmt, path)

    def switch(self, template_id: str) -> Dict[str, Any]:
        if template_id not in self._templates:
            raise KeyError(f"未注册模板：{template_id}")
        self._current = template_id
        return self._templates[template_id]

    def list(self) -> List[Dict[str, Any]]:
        return list(self._templates.values())

    def get(self, template_id: str) -> Dict[str, Any]:
        if template_id not in self._templates:
            raise KeyError(f"未注册模板：{template_id}")
        return self._templates[template_id]

    @property
    def current(self) -> Optional[str]:
        return self._current
