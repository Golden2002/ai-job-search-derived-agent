# CHANGELOG — ai-job-search-derived-agent（PAEG 工具生态 14.5 通用简历工具）

本文件记录本工具的更新路径：版本、改动模块、测试数、关联需求文档。

## v1.7.0 (2026-08-28) — LLM + 语言规范接入（网页端体验修复）

**更新路径**：product/src/resume_product/{llm_client.py, core.py, api.py} + product/web/index.html + product/tests/test_llm_lang.py

- 新增 llm_client.py：DeepSeek 客户端（auth.json key → 环境变量降级，失败返回空串）
- core.py：`_default_chat` 接入真实 LLM；修复 enrich 的 `is _default_chat` 短路 bug（默认引擎曾永远走 heuristic）；LLM 提示词增加口语规范化要求（口语/自嘲表述 → 书面简历语言，保留量化数据，不编造）
- core.py：compose 接入语言规范模块 paeg_lang_style（14.1，editable 安装指向真实位置）
- SURFACE 验证：真实 DeepSeek 规范化生效（"当 spice monkey，瞎调参数"→"负责参数调优工作"；"用来充数的一生一芯"→"参与'一生一芯'项目"）
- 测试：102 全绿（+8：test_llm_lang.py）

## v1.6.0 (2026-08-28) — 网页端六步全链路重做

**更新路径**：product/web/index.html（重写）+ product/src/resume_product/api.py（3→12 端点）

- 六步流程：经历+JD → 事实校验（verified/unverified/exaggerated 分档）→ JD 五维匹配评分 → 三版本生成 → ATS 校验 → 在线编辑+导出（HTML/Word/PDF）
- API 12 端点：health/role-packs/enrich/claim-check/match/versions/ats/trim/interview/skill-gaps/generate/export

## v1.5.0 (2026-08-28) — 基线对齐补全（15 项）

**更新路径**：product/src/resume_product/{job_evaluation, cv_trim, rank, salary_benchmark, interview_prep, application_tracker, skill_gap, profile_3d, claim_gate, multi_version, capability_taxonomy, job_portal, template_registry}.py + render/latex_compile.py + schemas/canonical_experience.py

- 主基线（ai-job-search）14 项 + 参考基线（medical-resume-agent）4 项全量补全
- MCP 工具 3→20；测试 94 全绿
- 关联：审计报告_第一波_基线能力拆解.md 第六节

## v1.4.0 (2026-08-28) — 多行业 Role Pack + ATS + 双 Agent

**更新路径**：product/data/role_packs/{consulting_v1,finance_v1,education_v1}.json + ats_check.py + drafter_reviewer.py

- 34 测试全绿

## v1.0.0 (2026-08) — 产品化核心（W3-W10）

**更新路径**：product/src/resume_product/ 核心引擎 + MCP + API + 前端 + 四格式渲染（markdown/html/docx/pdf + resume.css + render_pdf.py）

- 需求文档：REQ_需求文档.md v0.1；方案：docs/产品化方案 v1.0
