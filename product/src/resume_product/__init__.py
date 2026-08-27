# -*- coding: utf-8 -*-
"""resume_product — 通用简历制作 Agent 独立产品（W3 ⭐）。

复用 medical-resume-agent 引擎（claim_gate/confirmation_gate/experience_draft/
bullet_composer）+ ai-job-search 工作流，通用化改造为全行业简历工具。
"""

from .core import ResumeEngine
from .core import generate_resume, enrich_experience

__all__ = ["ResumeEngine", "generate_resume", "enrich_experience"]
