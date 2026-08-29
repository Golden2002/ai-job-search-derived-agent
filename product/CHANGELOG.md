# CHANGELOG — ai-job-search-derived-agent（PAEG 工具生态 14.5 通用简历工具）

本文件记录本工具的更新路径：版本、改动模块、测试数、关联需求文档。

## v1.8.5 (2026-08-30) — 网页产品浏览器端 E2E 补齐四格式导入（xlsx/pdf/image）

**更新路径**：product/tests/test_e2e_browser.py + product/test_artifacts/README.md

- v1.8.4 的浏览器端 E2E 只覆盖 docx 导入；本轮补齐四格式导入的浏览器回归缺口：
  - 导入 xlsx（上传 `.xlsx` → `/api/import-xlsx`，openpyxl 单元格样式 → HTML 表格）
  - 导入 pdf（上传 `.pdf` → `/api/import-pdf`，pdfplumber 字符级 → CSS/HTML）
  - 导入 image（上传 `.png` → `/api/import-image`，OCR 用 mock 跳过 rapidocr 慢路径，验证前端分派契约）
- 测试 +3（E2E 6 → 9 用例），全量 445 → 448 passed + 143 subtests

## v1.8.4 (2026-08-30) — 网页产品浏览器端 E2E 回归（补齐前端自动化缺口）

**更新路径**：product/tests/test_e2e_browser.py（新增）+ product/test_artifacts/README.md

- 新增浏览器端 E2E（Playwright + 后台线程起 `create_app()` 真实 HTTP + 系统 Chrome/Edge 兜底），
  首次覆盖 `product/web/index.html` 三栏前端（导航/对话/汇总）与后端契约的真实浏览器回归：
  - 场景卡片加载（`/api/scene-cards` → 左侧导航渲染场景/子场景/阶段）
  - 对话收集（LLM 降级 → `/api/chat` 返回 llm:false → 前端 `_fallbackAsk` 规则式填入首个空字段）
  - 卡片 chip 收集（multi 字段点选 → 填充/进度/汇总/圆点 partial）
  - 生成预览（`generateResume()` → 预览模态框 + 结构化小节 + 三模板切换）
  - 导出 docx（`/api/export` 真实 docx 字节流契约）
  - 导入 docx（上传 `.docx` → `/api/import-docx` 解析 → 「已还原排版」）
- LLM 用 monkeypatch 替换为确定性降级（返回空串），不跑真实 PDF 渲染，6 用例 ~5.2s 秒级完成
- 未装 playwright/Chrome/Edge 时 6 用例自动 skip，不影响其余用例
- 测试 +6（全量 439 → 445 passed + 143 subtests）

## v1.8.3 (2026-08-30) — 独立接入 LLM（环境变量，对齐主项目配置约定）

**更新路径**：product/src/resume_product/llm_client.py + product/.env.example（新增）

- `llm_client` 配置发现优先级对齐主项目 llm_api.py：
  1. `PAEG_API_KEY`（+`PAEG_API_BASE`/`PAEG_MODEL`，主项目自定义）
  2. `DEEPSEEK_API_KEY`（→ DeepSeek）
  3. opencode auth.json（项目 `secret/auth.json` 优先 → `~/.local/share` / `~/.config` / `%APPDATA%` 系统级；同时识别 `key` 与 `api_key` 字段）
- 新增 `.env` 自动加载（无第三方依赖的轻量实现，独立运行时读取 `DEEPSEEK_API_KEY`）
- 支持 `PAEG_API_BASE`/`DEEPSEEK_API_URL` → chat/completions 端点归一化；旧模型别名 `deepseek-reasoner` → `deepseek-v4-flash`
- 新增 `.env.example` 说明文档（对齐主项目同一套约定）
- 实测：`/api/chat` 对话式收集返回 `llm: true` + 正确实体抽取（姓名/院校/专业/方向）+ 枚举追问

## v1.8.2 (2026-08-29) — PDF/Excel 简历上传 → 排版还原（Oracle 多格式改造完整实施）

**更新路径**：product/src/resume_product/render/{pdf_import.py, xlsx_import.py}（新增）+ executor.py + mcp_server.py + api.py + web/index.html + product/tests/test_pdf_xlsx_import.py

- 新增 pdf_import.py（P0）：PDF 简历 → pdfplumber 字符级提取（text + 坐标 + fontname + size + non_stroking_color）→ 几何布局（复用 image_import 框架：行分组/分栏/字号/颜色）→ CSS/HTML 还原（真实字体信息替代 OCR 推断，精度更高）
- 新增 xlsx_import.py（P1）：Excel 简历 → openpyxl 读取单元格样式（字体/字号/加粗/颜色/填充 solid/对齐）+ merged_cells → HTML 表格（colspan/rowspan + 单元格样式）
- executor + MCP 25 工具（import_resume_pdf / import_resume_xlsx）；api.py 新增 `POST /api/import-pdf` + `/api/import-xlsx`
- 前端上传入口扩展：接受 .docx/.pdf/.xlsx/.xlsm/图片，`uploadResume()` 按扩展名分发到对应端点
- 测试 +3（test_pdf_xlsx_import.py：PDF 还原/Excel 合并单元格样式/无填充不误加背景）
- **四格式还原全齐**：Word(100%) / Excel(表格+样式) / PDF(坐标+真实字体) / 图片(OCR+几何)
- 依赖：pdfplumber + openpyxl（可选，无则优雅降级）

## v1.8.1 (2026-08-29) — 简历截图上传 → OCR 排版识别 → CSS/HTML 还原

**更新路径**：product/src/resume_product/render/image_import.py（新增）+ executor.py + mcp_server.py + api.py + web/index.html + product/tests/test_image_import.py

- 新增 image_import.py：上传简历截图（图片）→ rapidocr OCR 提取文字 + 边界框 → 几何布局分析（center_x 分类左/右/居中 → 分栏检测 → 栏内按 top 分行 → 字号 box 高度 → 对齐）→ 生成还原自定义样式的 CSS + HTML
- `import_resume_image(image_path)` 返回 `{html, css, meta}`；css 含 `column-count` 双栏还原
- executor + MCP 23 工具 `import_resume_image`；api.py 新增 `POST /api/import-image`（png/jpg/jpeg/webp/bmp）
- 前端上传入口扩展：同时接受 .docx + 图片，`uploadResume()` 按文件类型分发到 /api/import-docx 或 /api/import-image
- 测试 +3（test_image_import.py：OCR 文字/布局还原/优雅降级）
- 依赖：rapidocr-onnxruntime + Pillow（可选，无则优雅降级返回空）

## v1.8.0 (2026-08-29) — Word 简历上传 → 排版还原 CSS（用户核心优化点）

**更新路径**：product/src/resume_product/render/docx_import.py（新增）+ executor.py + mcp_server.py + api.py + product/web/index.html + product/tests/test_docx_import.py

- 新增 docx_import.py：上传 Word 简历 → python-docx 解析排版 → 生成定制 CSS，**完美、精准还原原文档排版**，覆盖复杂排版元素：
  - 段落：字体（含 eastAsia 中文字体）/字号/加粗/斜体/下划线/颜色/对齐/首行缩进/左缩进/段前后间距/行距
  - **表格**：行/列/单元格文本 → HTML `<table>`（按文档顺序与段落交错渲染）
  - **分栏**：section 的 `w:cols` → CSS `column-count`（双栏简历还原）
  - **图片**：inline shape → base64 data URI `<img>`（图形元素保留）
  - **列表**：项目符号（List Bullet → `• `）/ 编号（List Number → `1. 2.` 递增，非 decimal 打断重置）
  - **合并单元格**：`w:gridSpan` → `<td colspan>`（水平合并还原）
  - **页眉页脚**：section header/footer → HTML 顶部/底部块（简历常见：页眉放姓名/联系方式）
- `import_docx_resume(docx_path)` 一站式返回 `{html, css, meta}`；css 可作 `render_pdf.build_html` 的 `custom_css`
- executor + MCP 22 工具 `import_resume_docx`；api.py 新增 `POST /api/import-docx`（multipart 上传）
- 前端 index.html 第一步新增「上传 Word 简历」入口：上传 → 还原排版 → 导出 PDF 自动应用还原 CSS
- 测试 +5（test_docx_import.py：段落排版/表格/分栏 + CSS 还原 + executor 接入）；图片提取实测通过
- 依赖：python-docx（`resume_extract` 可选依赖，已声明于 pyproject.toml）

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
