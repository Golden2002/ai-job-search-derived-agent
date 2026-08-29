# test_artifacts — 简历制作工具「全产物实测」落盘

本目录是对 `product/src/resume_product/`（Flask 网页 + 对话式三栏前端）**逐一实测后落盘的全部产物**，
由 `generate_artifacts.py` 用 **Flask test_client**（不起真实端口）调用各端点生成，可复现、可回归比对。

- 生成方式：在 `product/` 下执行 `python test_artifacts/generate_artifacts.py`
- 测试基线（product 子集）：在 `product/` 下 `python -m pytest tests/ -q` → **148 passed**
  （含 7 个后端回归用例 + 9 个浏览器端 E2E 用例 `test_e2e_browser.py`）
- 测试基线（仓库全量）：在仓库根 `python -m pytest -q` → **448 passed + 143 subtests**
  （根 `tests/` 300 + `product/tests/` 148）
- LLM：真实 DeepSeek（`~/.local/share/opencode/auth.json`），实测 `llm: true` 生效

## 产物清单（对应任务 6 类产物）

### ① 对话式收集（/api/chat）
| 文件 | 说明 |
|---|---|
| `01_chat_collection.json` | 求职·后端开发·基本信息 两轮真实对话：实体抽取（姓名/年限）+ 枚举追问；`llm: true` |

### ② 场景卡片（/api/scene-cards）
| 文件 | 说明 |
|---|---|
| `02_scene_cards_summary.json` | 4 场景（保研/考研/出国/求职）+ 求职 11 岗位结构摘要 |

### ③ 四格式排版还原 HTML/CSS（/api/import-*）
| 文件 | 说明 |
|---|---|
| `03_import_docx.{html,css,meta.json}` | Word → 段落/字体/字号/表格/分栏/合并单元格还原 |
| `03_import_pdf.{html,css,meta.json}` | PDF → pdfplumber 字符级坐标+字体+颜色还原（双栏） |
| `03_import_xlsx.{html,css,meta.json}` | Excel → openpyxl 单元格样式还原（合并单元格/填充/对齐） |
| `03_import_image.{html,css,meta.json}` | 截图 → rapidocr OCR 几何布局还原（双栏） |
| `03_import_summary.json` | 四格式 meta 汇总 |

### ④ 简历生成（/api/generate）
| 文件 | 说明 |
|---|---|
| `04_resume.md` | markdown 简历（Role Pack 定向 + 证据引用） |
| `04_resume.html` | HTML 简历 |

### ⑤ 导出（/api/export）
| 文件 | 说明 |
|---|---|
| `05_resume.docx` | 结构化经历 → Word |
| `05_resume.pdf` | markdown → PDF（Playwright + Chrome，classic 模板） |
| `05_resume_from_chat.docx` | 对话式收集的 `resume_text` → Word（前端 downloadWord 契约） |

### ⑥ 多版本 / ATS / 面试 / 技能缺口（+匹配/改进）
| 文件 | 说明 |
|---|---|
| `06_versions.json` | 稳妥/专业/高竞争力三版对比 |
| `06_ats.json` | ATS 兼容性校验（关键词/量化/联系方式/标题，score=100） |
| `06_interview.json` | STAR 故事 + 高频难题 + 反问 |
| `06_skill_gaps.json` | 技能缺口热图 + 学习路径 |
| `06_match.json` | JD 五维匹配评分（Moderate Fit 66.2） |
| `06_improve.json` | 低分改进建议（LLM 优先，非降级） |

## 测试发现并修复的问题

1. **`/api/export` 忽略前端 `resume_text`（导出空简历）**：前端 `downloadPDF()/downloadWord()`
   传 `resume_text`，后端只认 `experiences`，导致对话收集内容丢失、导出空白简历。
   → 后端 `/api/export` 接受 `resume_text`（PDF 直接渲染 markdown；DOCX 走新增 `resume_text_to_docx`）。
2. **`stage_id` 非全局唯一（对话收集取错场景）**：`basic/education/work` 等多场景复用，
   后端 `_find_stage` 与前端 `findStage` 都取「首个匹配」（保研·临床医学），
   导致选其它场景时字段卡片与 LLM 追问全错。
   → 后端 `find_stage(stage_id, scene_id, sub_scene_id)` + 前端 `findStage` 场景内优先、`/api/chat` 传 `scene_id/sub_scene_id`。
3. **前端 `state/filled` 以 stage_id 为键跨场景串数据**：同名 stage（如 basic）在多个场景共享状态，
   汇总/预览/导出出现重复「基本信息」小节。
   → 改为 `stageKey(scene|sub|stage)` 复合键。
4. **`**` 加粗标记泄入 HTML/PDF**：`to_html`/`build_html` 用 `strip('*')` 未去净 `**适配方向**` 中间星号。
   → 改用 `replace('**','')`。
5. **对话收集的 `###` 小节标题在 PDF 渲染为普通 `<p>`**：`build_html` 未处理 `### `。
   → 新增 `###/##` → `.r-subtitle` 节标题。
6. **（Round-2 测试卫生）`tests/test_upstream_triage.py` 子进程 GBK 解码告警**：`subprocess.run(text=True)`
   未指定 `encoding`，在中文 Windows 下用 GBK 解码上游 triage 脚本的 UTF-8 输出（如 `✓` 的尾字节 `0x93`），
   产生 7 条 `PytestUnhandledThreadExceptionWarning`。→ 两处 `subprocess.run` 统一加 `encoding="utf-8", errors="replace"`，
   该文件 10 用例仍全绿、告警归零。

## 风险与已知限制

- **PDF 渲染依赖 Playwright + Chrome**：无 Chrome 时 `/api/export?format=pdf` 返回 500（已给清晰错误）。
  本机 Chrome 存在，实测 PDF 生成成功（`05_resume.pdf` 65159 bytes，`%PDF` 头）。
- **四格式导入为可选依赖**：python-docx/pdfplumber/openpyxl/rapidocr 本机已装；缺依赖时各端点优雅降级返回 500+提示。
- **docx 导入 CSS 复用限制**：导入产生的 `.docx-p-*` 类 CSS 含 `@page/body` 基础样式，作用到新生成 markdown
  （`.r-*` 结构）时仅字体/页边距生效，`.docx-p-*` 类不匹配（CHANGELOG 所述「自动应用还原 CSS」为部分生效）。
- **LLM 输出非确定性**：`/api/chat`、`/api/enrich`、`/api/improve` 依赖真实 LLM，同一输入输出可能有差异；
  规则兜底路径（无 key）已保证不报错。
- **前端 JS 已通过 `node --check` 语法校验**，并已补浏览器端自动化回归（见下方「浏览器端 E2E」）。

## 浏览器端 E2E（Round 5 新增、Round 6 补齐四格式，`product/tests/test_e2e_browser.py`，9 用例）

仿 vocab 的 E2E 基建（Playwright + 后台线程起 `create_app()` 真实 HTTP 服务 + 系统 Chrome/Edge 兜底），
用**真实浏览器渲染 + 真实 HTTP**回归前端三栏（导航/对话/汇总）与后端契约；LLM 用 monkeypatch 替换为
确定性降级（返回空串 → `/api/chat` 走规则式追问），不跑真实 PDF 渲染，秒级完成（~5.2s）。

| 用例 | 覆盖 |
|---|---|
| `test_scene_cards_load` | `/api/scene-cards` → 左侧导航渲染场景/子场景/阶段 |
| `test_dialog_send_degrades_to_rule` | 对话收集：LLM 降级 → `_fallbackAsk` 规则式填入首个空字段 |
| `test_chip_collection_multi_field` | 卡片 chip 点选 multi 字段 → 填充/进度/汇总/圆点 partial |
| `test_generate_preview` | 生成简历 → 预览模态框 + 结构化小节 + 模板切换（经典/现代/极简） |
| `test_export_docx_contract` | `downloadWord` 的 `/api/export` 真实 docx 字节流契约 |
| `test_import_docx_via_upload` | 上传 `.docx` → `/api/import-docx` 解析 → 「已还原排版」 |
| `test_import_xlsx_via_upload` | 上传 `.xlsx` → `/api/import-xlsx`（openpyxl 单元格样式 → HTML 表格，Round 6） |
| `test_import_pdf_via_upload` | 上传 `.pdf` → `/api/import-pdf`（pdfplumber 字符级 → CSS/HTML，Round 6） |
| `test_import_image_via_upload_mocked` | 上传 `.png` → `/api/import-image`（OCR mock，验证前端分派契约，Round 6） |

未安装 playwright 或 Chrome/Edge 时上述 9 用例自动 `skip`（`pytest.importorskip` + `skipif`），不影响其余用例。

## 回归用例（新增 13 个）

- `test_api.py`：`test_scene_cards_structure`、`test_export_uses_resume_text`、`test_generate_html_no_stray_markdown`、
  `test_find_stage_scene_aware`、`test_chat_scene_aware`
- `test_render_templates.py`：`test_build_html_no_stray_asterisks`、`test_build_html_renders_sub_heading`
- `test_e2e_browser.py`：上述 9 个浏览器端 E2E 用例（Round 5 新增 6、Round 6 补齐 xlsx/pdf/image 三格式）
